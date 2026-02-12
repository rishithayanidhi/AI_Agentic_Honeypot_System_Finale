from typing import List, Optional, Dict, Any
from google import genai
from anthropic import Anthropic
from config import settings
from src.models.schemas import Message
import random
import logging
import json
import re
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> str:
    """Extract JSON object from text that may contain other content"""
    if not text:
        return "{}"
    
    # Try to find JSON object in the text
    # Look for content between first { and last }
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx + 1]
    
    return text


class AIAgent:
    """AI Agent that engages with scammers using believable personas"""
    
    # Different personas the agent can adopt
    PERSONAS = {
        "cautious_user": {
            "description": "A cautious but curious user who asks clarifying questions",
            "traits": "careful, asks many questions, slightly worried, tech-unsavvy"
        },
        "eager_victim": {
            "description": "An eager person who seems likely to comply but needs guidance",
            "traits": "willing to help, slightly panicked, ready to act, not tech-savvy"
        },
        "confused_elderly": {
            "description": "An elderly person who is confused and needs step-by-step help",
            "traits": "confused, needs simple explanations, slow to understand, forgetful"
        },
        "busy_professional": {
            "description": "A busy professional who wants to resolve issues quickly",
            "traits": "impatient, multitasking, wants quick solutions, easily distracted"
        }
    }
    
    def __init__(self):
        self.primary_provider = settings.LLM_PROVIDER
        self.available_providers = []
        self.clients = {}
        self.models = {}
        self.gemini_key_index = 0  # Track current Gemini key
        self.gemini_clients = []  # Multiple Gemini clients
        
        # Rate limiting and cooldown tracking
        self.provider_cooldowns = {}  # Track when providers can be used again
        self.model_cooldowns = {}  # Track per-model cooldowns
        self.last_request_time = {}  # Track last request per provider
        self.request_counts = {}  # Track requests per minute
        self.min_request_interval = settings.MIN_REQUEST_INTERVAL  # Minimum seconds between requests
        
        # Track recent responses to avoid repetition
        self.recent_responses = []  # Store last 5 responses
        self.max_recent_responses = 5
        
        # Initialize all available providers dynamically
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize LLM providers (Claude Haiku 4.5, Gemini with multi-key support)"""
        # Try Anthropic (Claude Haiku 4.5) - Primary
        try:
            if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "your-anthropic-api-key-here":
                self.clients['anthropic'] = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                self.models['anthropic'] = settings.ANTHROPIC_MODEL
                self.available_providers.append('anthropic')
                logger.info(f"🚀 AI Agent: Claude Haiku 4.5 initialized with model: {settings.ANTHROPIC_MODEL}")
        except Exception as e:
            logger.warning(f"AI Agent: Failed to initialize Claude: {e}")
        
        # Initialize multiple Gemini clients with different API keys
        try:
            gemini_keys = settings.get_gemini_api_keys()
            if gemini_keys:
                for idx, api_key in enumerate(gemini_keys):
                    try:
                        client = genai.Client(api_key=api_key)
                        self.gemini_clients.append(client)
                        logger.info(f"AI Agent: Gemini client {idx + 1} initialized (key: ...{api_key[-4:]})")
                    except Exception as e:
                        logger.warning(f"AI Agent: Failed to initialize Gemini client {idx + 1}: {e}")
                
                if self.gemini_clients:
                    # Set first client as default
                    self.clients['gemini'] = self.gemini_clients[0]
                    self.models['gemini'] = settings.GEMINI_MODEL
                    self.available_providers.append('gemini')
                    logger.info(f"✅ AI Agent: {len(self.gemini_clients)} Gemini API key(s) initialized")
        except Exception as e:
            logger.warning(f"AI Agent: Failed to initialize Gemini: {e}")
        
        if not self.available_providers:
            logger.warning("AI Agent: No LLM providers available - will use fallback responses only")
        else:
            logger.info(f"✅ AI Agent: Available providers: {', '.join(self.available_providers)}")
    
    def _extract_retry_delay(self, error_msg: str) -> float:
        """Extract retry delay from error message (e.g., 'Please retry in 18.360292146s')"""
        try:
            import re
            match = re.search(r'retry in ([0-9.]+)s', error_msg)
            if match:
                delay = float(match.group(1))
                logger.info(f"AI Agent: Extracted retry delay: {delay}s")
                return delay
            # Also check for retryDelay field
            match = re.search(r'retryDelay["\']?:\s*["\']?([0-9.]+)s?["\']?', error_msg)
            if match:
                delay = float(match.group(1))
                logger.info(f"AI Agent: Extracted retry delay from field: {delay}s")
                return delay
        except Exception as e:
            logger.debug(f"AI Agent: Could not extract retry delay: {e}")
        return settings.DEFAULT_RETRY_DELAY  # Default cooldown from config
    
    def _is_provider_in_cooldown(self, provider: str) -> bool:
        """Check if provider is in cooldown period"""
        if provider in self.provider_cooldowns:
            cooldown_until = self.provider_cooldowns[provider]
            if datetime.now() < cooldown_until:
                remaining = (cooldown_until - datetime.now()).total_seconds()
                logger.debug(f"AI Agent: {provider} in cooldown for {remaining:.1f}s more")
                return True
            else:
                # Cooldown expired, remove it
                del self.provider_cooldowns[provider]
        return False
    
    def _is_model_in_cooldown(self, model: str) -> bool:
        """Check if specific model is in cooldown period"""
        if model in self.model_cooldowns:
            cooldown_until = self.model_cooldowns[model]
            if datetime.now() < cooldown_until:
                remaining = (cooldown_until - datetime.now()).total_seconds()
                logger.debug(f"AI Agent: Model {model} in cooldown for {remaining:.1f}s more")
                return True
            else:
                del self.model_cooldowns[model]
        return False
    
    def _set_cooldown(self, identifier: str, delay_seconds: float, is_model: bool = False):
        """Set cooldown for provider or model"""
        cooldown_until = datetime.now() + timedelta(seconds=delay_seconds)
        if is_model:
            self.model_cooldowns[identifier] = cooldown_until
            logger.info(f"AI Agent: Model {identifier} cooldown set for {delay_seconds}s")
        else:
            self.provider_cooldowns[identifier] = cooldown_until
            logger.info(f"AI Agent: Provider {identifier} cooldown set for {delay_seconds}s")
    
    def _throttle_request(self, provider: str):
        """Enforce minimum time between requests to avoid rate limits"""
        if provider in self.last_request_time:
            elapsed = time.time() - self.last_request_time[provider]
            if elapsed < self.min_request_interval:
                sleep_time = self.min_request_interval - elapsed
                logger.info(f"AI Agent: Throttling {provider} request, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
        self.last_request_time[provider] = time.time()
    
    def _call_llm(self, provider: str, prompt: str, temperature: float = 0.7) -> str:
        """Call LLM (Claude Haiku 4.5 or Gemini) with error handling - optimized for speed"""
        # Check provider cooldown
        if self._is_provider_in_cooldown(provider):
            raise Exception(f"{provider} is in cooldown period")
        
        # Throttle request to avoid hitting rate limits
        self._throttle_request(provider)
        
        try:
            if provider == "anthropic":
                # Claude Haiku 4.5 - Ultra fast and cost-effective
                response = self.clients['anthropic'].messages.create(
                    model=self.models['anthropic'],
                    max_tokens=settings.LLM_MAX_TOKENS_RESPONSE,
                    temperature=temperature,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                result_text = response.content[0].text
                logger.info(f"🚀 AI Agent: Successfully used Claude Haiku 4.5")
                logger.debug(f"AI Agent: Claude response: {result_text[:200]}...")
                return result_text
            
            elif provider == "gemini":
                # Try all Gemini clients with rotation on quota errors
                last_error = None
                quota_exhausted = False  # Track if quota is globally exhausted
                
                # Prioritize Flash models for speed (filter out models in cooldown)
                all_gemini_models = [
                    'models/gemini-2.5-flash',      # Fastest
                    'models/gemini-flash-latest',    # Fast fallback
                    'models/gemini-2.0-flash',       # Fast alternative
                    self.models['gemini'],           # User configured
                    'models/gemini-2.5-pro',         # Quality fallback
                    'models/gemini-pro-latest'       # Last resort
                ]
                
                # Filter out models in cooldown
                gemini_models = [m for m in all_gemini_models if not self._is_model_in_cooldown(m)]
                
                if not gemini_models:
                    logger.warning("AI Agent: All Gemini models are in cooldown")
                    raise Exception("All Gemini models in cooldown")
                
                # Try each Gemini client (rotating through API keys)
                for client_attempt in range(len(self.gemini_clients)):
                    current_client = self.gemini_clients[self.gemini_key_index]
                    client_num = self.gemini_key_index + 1
                    
                    for model_name in gemini_models:
                        try:
                            # Use proper generation configuration
                            response = current_client.models.generate_content(
                                model=model_name,
                                contents=prompt,
                                config={
                                    'temperature': temperature,
                                    'maxOutputTokens': settings.LLM_MAX_TOKENS_RESPONSE,
                                    'topP': 0.95,
                                    'topK': 40
                                }
                            )
                            
                            # Check if response was blocked or incomplete
                            if hasattr(response, 'candidates') and response.candidates:
                                candidate = response.candidates[0]
                                if hasattr(candidate, 'finish_reason'):
                                    logger.info(f"AI Agent: Finish reason: {candidate.finish_reason}")
                            
                            logger.info(f"AI Agent: Successfully used Gemini model: {model_name}")
                            logger.info(f"AI Agent: Received response length: {len(response.text) if hasattr(response, 'text') else 0} characters")
                            
                            # Extract text from response - try different methods
                            result_text = ""
                            try:
                                # Primary method: use .text property
                                result_text = response.text
                            except Exception as e:
                                logger.debug(f"AI Agent: Could not get .text property: {e}")
                                # Fallback: extract from candidates
                                if hasattr(response, 'candidates') and response.candidates:
                                    candidate = response.candidates[0]
                                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                        parts_text = []
                                        for part in candidate.content.parts:
                                            if hasattr(part, 'text'):
                                                parts_text.append(part.text)
                                        result_text = ''.join(parts_text)
                            
                            if not result_text:
                                raise ValueError("Could not extract text from response")
                            
                            logger.debug(f"AI Agent: Raw response from {model_name}: {result_text[:200]}...")
                            return result_text
                            
                        except Exception as model_error:
                            error_msg = str(model_error)
                            last_error = model_error
                            
                            # Check if it's a quota error (429 or RESOURCE_EXHAUSTED)
                            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                                logger.warning(f"AI Agent: Gemini model {model_name} failed: {model_error}")
                                
                                # Extract retry delay and set model cooldown
                                retry_delay = self._extract_retry_delay(error_msg)
                                self._set_cooldown(model_name, retry_delay, is_model=True)
                                
                                # Check if it's a daily quota exhaustion (0 limit)
                                if "limit: 0" in error_msg or "Daily" in error_msg:
                                    logger.warning(f"AI Agent: Model {model_name} has exhausted daily quota")
                                    quota_exhausted = True
                                    # Set longer cooldown for daily quota
                                    self._set_cooldown(model_name, settings.QUOTA_EXHAUSTED_COOLDOWN, is_model=True)
                                
                                # Try next model with current key
                                continue
                            else:
                                # Non-quota error, try next model
                                logger.warning(f"AI Agent: Gemini model {model_name} failed: {model_error}")
                                continue
                    
                    # All models failed with current key, rotate to next key
                    if len(self.gemini_clients) > 1 and not quota_exhausted:
                        self.gemini_key_index = (self.gemini_key_index + 1) % len(self.gemini_clients)
                        logger.warning(f"AI Agent: Rotating to Gemini API key {self.gemini_key_index + 1}")
                    else:
                        # Only one key, or quota exhausted across all models
                        if quota_exhausted:
                            logger.warning("AI Agent: Daily quota exhausted, setting provider cooldown")
                            self._set_cooldown('gemini', settings.QUOTA_EXHAUSTED_COOLDOWN)
                        break
                
                # If all models and all keys failed, raise the last error
                if last_error:
                    raise last_error
            
            raise ValueError(f"Unknown provider: {provider}")
            
        except Exception as e:
            error_msg = str(e)
            # Set cooldown for rate limit errors
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                retry_delay = self._extract_retry_delay(error_msg)
                self._set_cooldown(provider, retry_delay)
            elif "credit balance" in error_msg.lower() or "billing" in error_msg.lower():
                logger.error(f"AI Agent: {provider} has billing issues, setting long cooldown")
                self._set_cooldown(provider, settings.BILLING_ERROR_COOLDOWN)
            
            logger.error(f"AI Agent: Error calling {provider}: {e}", exc_info=False)
            raise
    
    def select_persona(self, scam_type: str, message_count: int = 0) -> str:
        """Select appropriate persona based on scam type and conversation stage"""
        
        # Early conversation - be more cautious (dynamic threshold)
        if message_count < settings.EARLY_STAGE_THRESHOLD:
            return "cautious_user"
        
        # Mid conversation - adapt based on scam type
        if scam_type in ["bank_fraud", "upi_fraud"]:
            return random.choice(["eager_victim", "confused_elderly"])
        elif scam_type in ["phishing", "fake_offer"]:
            return random.choice(["cautious_user", "busy_professional"])
        
        return "cautious_user"
    
    def generate_response(
        self,
        scammer_message: str,
        conversation_history: List[Message],
        persona: str = "cautious_user",
        scam_type: str = "unknown",
        extracted_intel: Dict = None,
        message_count: int = 0
    ) -> Dict[str, any]:
        """
        Generate a human-like response to the scammer
        
        Returns: {
            'response': str,
            'strategy': str,
            'should_continue': bool,
            'notes': str
        }
        """
        
        # Build conversation context
        context = self._build_conversation_context(conversation_history)
        
        # Use provided message_count or calculate from history
        if message_count == 0:
            message_count = len(conversation_history)
        
        # Determine conversation stage
        stage = self._determine_stage(message_count, extracted_intel)
        
        # Get persona details
        persona_info = self.PERSONAS.get(persona, self.PERSONAS["cautious_user"])
        
        # Build recent responses context to avoid repetition
        recent_context = ""
        if self.recent_responses:
            recent_context = "\nRECENT RESPONSES YOU USED (DON'T REPEAT THESE):\n" + "\n".join(f"- {r}" for r in self.recent_responses[-3:])
        
        # Build the prompt for the AI
        prompt = f"""You are a REAL PERSON chatting with someone. You don't know you're talking to a scammer.

PERSONA: {persona}
Traits: {persona_info['traits']}

CONVERSATION SO FAR:
{context}
{recent_context}

LATEST MESSAGE FROM THEM:
"{scammer_message}"

CRITICAL RULES FOR REALISM:
1. Keep responses SHORT (1-3 sentences max, often just 5-15 words!)
2. Use casual WhatsApp/SMS style - lowercase, no perfect grammar
3. Make natural typos: teh→the, recieve→receive, dont→don't, plz, u, ur, wat, shud
4. Show raw emotions: "oh no!", "really??", "wait what", "omg", "😰"
5. Be scattered and confused - don't over-explain anything
6. Ask 1 simple question, not multiple analytical questions
7. Sometimes respond with JUST emotion or confusion
8. NEVER USE: "Could you", "I understand", "I appreciate", formal words
9. React to SPECIFIC WORDS they used - if they mention "OTP", "phone number", "account", SAY THOSE WORDS BACK
10. Vary your response structure - don't always follow same pattern

ANALYZE THEIR MESSAGE:
- What specific thing are they asking for? (OTP? account number? click link?)
- Did they mention any numbers, phone, time limit? Reference those!
- What's the urgency level? Show appropriate panic/confusion

BAD (robotic repetition): "which code ur talking about? confused"
GOOD (specific reaction): "wait u sent otp where? didnt get anything on 9876"

BAD (too formal): "Could you clarify what specific code you're referring to?"
GOOD (real person): "huh what code i dont see any msgs"

BAD (same every time): "what do you mean"
GOOD (varied): "not getting it explain again" OR "wat??" OR "dont understand this"

VARY YOUR CONFUSION:
- "huh?", "wat", "dont get it", "explain more", "not clear", "confused here"
- Reference THEIR specific words: if they say "OTP sent to +91-XX" → "which number u sent to"
- Mix lengths: Sometimes 3 words ("wat u mean"), sometimes 15 ("ok so ur saying my account will close if i dont send code right")

Respond with JSON (no markdown):
{{
  "response": "natural short casual reply",
  "strategy": "note",
  "should_continue": true/false,
  "notes": "quick observation"
}}"""

        # Try each available provider until one succeeds
        if not self.available_providers:
            logger.warning("AI Agent: No LLM providers available - using fallback response")
            return self._fallback_response(scammer_message, message_count)
        
        # Try primary provider first, then fallback to other available providers
        providers_to_try = []
        if self.primary_provider in self.available_providers:
            providers_to_try.append(self.primary_provider)
        # Add other providers as fallback
        for p in self.available_providers:
            if p not in providers_to_try:
                providers_to_try.append(p)
        
        last_error = None
        for provider in providers_to_try:
            try:
                logger.info(f"AI Agent: Attempting response generation with provider: {provider}")
                result = self._call_llm(provider, prompt, temperature=0.7)
                
                # Log raw result details
                logger.info(f"AI Agent: Received response length: {len(result)} characters")
                logger.debug(f"AI Agent: First 100 chars: {repr(result[:100])}")
                logger.debug(f"AI Agent: Last 100 chars: {repr(result[-100:])}")
                
                # Safety check for empty or None result
                if not result:
                    logger.warning(f"AI Agent: {provider} returned empty result")
                    continue
                
                # Clean JSON from markdown code blocks (Gemini often wraps in ```json```)
                result_clean = result.strip()
                if result_clean.startswith('```'):
                    # Remove code fence markers
                    result_clean = result_clean.replace('```json', '').replace('```', '')
                    # Clean up any remaining whitespace
                    result_clean = result_clean.strip()
                
                # Extract JSON from text (handles cases like "Here is the JSON: {...}")
                result_clean = extract_json_from_text(result_clean)
                
                # Parse JSON response with validation
                agent_decision = json.loads(result_clean)
                
                # Validate required fields
                if not isinstance(agent_decision, dict):
                    logger.error(f"AI Agent: Response is not a dictionary: {type(agent_decision)}")
                    continue
                
                if 'response' not in agent_decision:
                    logger.error(f"AI Agent: Response missing 'response' field")
                    agent_decision['response'] = "I'm not sure what you mean. Can you explain?"
                
                # Track successful response to avoid repetition
                response_text = agent_decision.get('response', '')
                self.recent_responses.append(response_text)
                if len(self.recent_responses) > self.max_recent_responses:
                    self.recent_responses.pop(0)
                
                logger.info(f"AI Agent: Successfully generated response with {provider}")
                return agent_decision
                
            except json.JSONDecodeError as e:
                logger.error(f"AI Agent: JSON parse error from {provider}: {e}. Raw result: {result[:200] if result else 'None'}")
                last_error = e
                continue
            except Exception as e:
                logger.error(f"AI Agent: Error with {provider}: {e}", exc_info=False)
                last_error = e
                continue
        
        # All providers failed - use fallback
        logger.warning(f"AI Agent: All LLM providers failed (last error: {last_error}) - using fallback response")
        fallback = self._fallback_response(scammer_message, message_count)
        
        # Extra safety: ensure fallback is valid
        if not fallback or not isinstance(fallback, dict):
            logger.error("AI Agent: Fallback response is invalid, returning emergency fallback")
            return {
                'response': "What do you mean?",
                'strategy': 'emergency_fallback',
                'should_continue': True,
                'notes': 'Emergency fallback due to all systems failing'
            }
        
        return fallback
    
    def _build_conversation_context(self, messages: List[Message]) -> str:
        """Build conversation context from message history"""
        if not messages:
            return "No previous conversation"
        
        context = ""
        for msg in messages[-10:]:  # Last 10 messages
            role = "Scammer" if msg.sender == "scammer" else "You (as victim)"
            context += f"{role}: {msg.text}\n"
        
        return context
    
    def _determine_stage(self, message_count: int, intel: Dict) -> str:
        """Determine conversation stage"""
        if message_count <= 5:
            return "early_engagement"
        elif message_count <= 15:
            return "information_gathering"
        else:
            return "late_stage_extraction"
    
    def _format_intel(self, intel: Dict) -> str:
        """Format extracted intelligence for display"""
        if not intel:
            return "None yet"
        
        items = []
        for key, values in intel.items():
            if values:
                items.append(f"{key}: {', '.join(values[:3])}")
        
        return "\n".join(items) if items else "None yet"
    
    def _fallback_response(self, scammer_message: str, message_count: int) -> Dict:
        """Smart context-aware fallback response with variety and natural language"""
        import re
        
        message_lower = scammer_message.lower()
        
        # Extract specific details from scammer message for natural responses
        phone_match = re.search(r'\+?\d{2}[-\s]?\d{10}|\d{10}', scammer_message)
        number_match = re.search(r'\d{6}|\d{16}|\d{4}', scammer_message)
        account_match = re.search(r'\d{16}|\d{12}', scammer_message)
        time_match = re.search(r'(\d+)\s*(minute|second|hour)', message_lower)
        
        # Build varied response pools with natural variations
        responses = []
        
        # OTP/PIN requests - act confused about what/where/how
        if any(word in message_lower for word in ['otp', 'pin', 'code', 'verification', 'cvv', '6-digit', '6‑digit']):
            responses = [
                "what code?? i didnt get anything" + (" on my phone" if phone_match else ""),
                "otp means what exactly? never heard this before",
                "where shud i look for this code? in my msgs?",
                "u mean password? or something else",
                "i checked my phone no new messages came",
                "code for what purpose exactly?",
                "how do i find that? is it in app or sms",
                "which otp r u asking? confused here"
            ]
        
        # Payment/Money requests - vary concern levels
        elif any(word in message_lower for word in ['payment', 'send money', 'transfer', 'pay', 'amount', 'rupees']):
            responses = [
                "how much??  dont have much money rn",
                "what am i paying for again? need to understand first",
                "is this payment necessary? sounds fishy",
                "where do i send it exactly",
                "never done this before what steps to follow",
                "will i get refund later or one time thing?"
            ]
        
        # Link clicks - show hesitation
        elif any(word in message_lower for word in ['click', 'link', 'website', 'url', 'download', 'open']):
            responses = [
                "link? my phone showing security warning",
                "not sure if i shud click dont want virus",
                "what will happen if i open it",
                "is it safe link or scam? how do i know",
                "cant open it says risk website"
            ]
        
        # Account/Bank issues - react to specific bank mentioned
        elif any(word in message_lower for word in ['account', 'blocked', 'suspend', 'freeze', 'kyc', 'sbi', 'bank']):
            bank_name = "account"
            if 'sbi' in message_lower:
                bank_name = "sbi account"
            elif 'hdfc' in message_lower:
                bank_name = "hdfc"
            elif 'icici' in message_lower:
                bank_name = "icici"
            
            responses = [
                f"wait my {bank_name} has problem?? what happened",
                "why would it get blocked i didnt do anything wrong",
                "can i check my balance is everything still there",
                "this is serious right? shud i go to branch",
                "how to fix this issue tell me steps"
            ]
        
        # Time pressure - acknowledge and show panic based on time mentioned
        elif any(word in message_lower for word in ['urgent', 'immediate', 'now', 'minute', 'second', 'expire', 'soon']):
            time_ref = f" {time_match.group(0)}" if time_match else ""
            responses = [
                f"ok ok{time_ref} is not much time right? what exactly i need do",
                "dont panic me im trying to understand first",
                "this urgent thing making me scared what if i mess up",
                "slow down! explain step by step plz",
                "only" + time_ref + "?? thats too less how can i do fast"
            ]
        
        # Phone number mentioned - acknowledge it
        elif phone_match:
            phone = phone_match.group(0)
            responses = [
                f"is {phone} my number? how u know my number",
                f"that number yours or mine unclear",
                f"i shud call {phone}? or wait for call"
            ]
        
        # Account number mentioned - verify it
        elif account_match:
            acc = account_match.group(0)
            responses = [
                f"is {acc[:4]}***{acc[-4:]} my account number? need to check",
                "how did u get my account details",
                "is this number correct let me verify first"
            ]
        
        # Prize/Lottery - excited confusion
        elif any(word in message_lower for word in ['won', 'prize', 'winner', 'lottery', 'congratulations', 'reward']):
            responses = [
                "really?? but i never entered any lottery",
                "wow!! how much i won? is it real",
                "sounds amazing but how u got my details",
                "what i need to do to claim it tell me"
            ]
        
        # Generic - natural confusion with variations
        else:
            responses = [
                "huh? didnt get what u said",
                "can u say that in simple way",
                "little confused explain again",
                "what exactly u want me to do unclear",
                "sorry not understanding this properly",
                "ok but how? need more details",
                "wait ur going too fast slow down"
            ]
        
        # Filter out recently used responses to avoid repetition
        available_responses = [r for r in responses if r not in self.recent_responses]
        if not available_responses:
            available_responses = responses  # Reset if all used
        
        selected_response = random.choice(available_responses)
        
        # Track this response
        self.recent_responses.append(selected_response)
        if len(self.recent_responses) > self.max_recent_responses:
            self.recent_responses.pop(0)
        
        return {
            'response': selected_response,
            'strategy': 'context_aware_fallback',
            'should_continue': message_count < 20,
            'notes': f'Fallback response to: {message_lower[:50]}'
        }
    
    def should_end_conversation(
        self,
        message_count: int,
        intelligence_quality: int,
        scam_confidence: float
    ) -> tuple[bool, str]:
        """
        Determine if conversation should end
        
        Returns: (should_end, reason)
        """
        
        # Max messages reached
        if message_count >= settings.MAX_MESSAGES_PER_SESSION:
            return True, "Maximum message limit reached"
        
        # Sufficient intelligence gathered
        if message_count >= 15 and intelligence_quality >= 3:
            return True, "Sufficient intelligence extracted"
        
        # Low quality engagement
        if message_count >= 10 and intelligence_quality == 0:
            return True, "No useful intelligence being extracted"
        
        # Not actually a scam
        if message_count >= 5 and scam_confidence < 0.5:
            return True, "Low scam confidence - likely not a scam"
        
        return False, ""
