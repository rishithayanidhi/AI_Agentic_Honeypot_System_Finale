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
        
        # Response history tracking to avoid repetition
        self.response_history = {}  # Track recent responses per session
        self.max_history_size = 10  # Remember last 10 responses
        
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
        
        # Log FAST_MODE status
        if settings.FAST_MODE:
            logger.info("⚡ AI Agent: FAST_MODE enabled - bypassing throttling and cooldowns for instant responses")
        else:
            logger.info(f"🐢 AI Agent: Production mode - rate limiting enabled ({settings.MIN_REQUEST_INTERVAL}s between requests)")
    
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
        # Skip cooldowns in FAST_MODE for testing/GUVI
        if settings.FAST_MODE:
            return False
        
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
        # Skip cooldowns in FAST_MODE for testing/GUVI
        if settings.FAST_MODE:
            return False
        
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
        # Skip throttling in FAST_MODE for testing/GUVI
        if settings.FAST_MODE:
            logger.debug(f"AI Agent: FAST_MODE enabled - skipping throttle for {provider}")
            return
        
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
                
                # In FAST_MODE, only try first model for speed
                if settings.FAST_MODE and gemini_models:
                    gemini_models = gemini_models[:settings.FAST_MODE_MAX_RETRY_ATTEMPTS]
                    logger.debug(f"AI Agent: FAST_MODE - limiting to {len(gemini_models)} model(s)")
                
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
        message_count: int = 0,
        session_id: str = "default"
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
        
        # Build the prompt for the AI
        prompt = f"""You are a REAL PERSON chatting with someone. You don't know you're talking to a scammer.

PERSONA: {persona}
Traits: {persona_info['traits']}

CONVERSATION SO FAR:
{context}

LATEST MESSAGE FROM THEM:
"{scammer_message}"

CRITICAL RULES FOR REALISM:
1. Keep responses SHORT (1-3 sentences max, sometimes just 1!)
2. Use casual WhatsApp/SMS style - lowercase, no perfect grammar
3. Make natural typos: teh→the, recieve→receive, dont→don't, plz, u, ur
4. Show raw emotions with: "oh no!", "really??", "wait what", punctuation!!!
5. Don't over-explain or sound articulate - be a bit scattered
6. Ask 1 simple question at a time, not multiple
7. Sometimes respond with JUST emotion: "😰", "omg", "wait"
8. Never use formal language or perfect structure
9. Real people don't explain their thought process
10. Be reactive, not analytical

BAD (too articulate): "I'm concerned about this situation. Could you please clarify what specific issue exists with my account? I want to understand the nature of this problem before proceeding."

GOOD (natural): "wait my account has problem?? what kind of problem?? i just checked yesterday everythng was fine"

GOOD (with typo): "oh no is it serious? what shud i do"

GOOD (brief emotion): "really?? thats scary"

YOUR GOAL: Sound like a real worried person texting, NOT like customer service or formal writing.

Respond with JSON (no markdown, keep response field SHORT and casual):
{{
  "response": "short casual response with maybe a typo",
  "strategy": "brief note",
  "should_continue": true/false,
  "notes": "quick observation"
}}"""

        # Try each available provider until one succeeds
        if not self.available_providers:
            logger.warning("AI Agent: No LLM providers available - using fallback response")
            return self._fallback_response(scammer_message, message_count, session_id)
        
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
        fallback = self._fallback_response(scammer_message, message_count, session_id)
        
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
    
    def _get_unique_response(self, responses: list, session_id: str = "default") -> str:
        """Get a response that hasn't been used recently"""
        # Initialize history for this session if needed
        if session_id not in self.response_history:
            self.response_history[session_id] = []
        
        history = self.response_history[session_id]
        available = [r for r in responses if r not in history[-5:]]  # Avoid last 5 responses
        
        if not available:
            available = responses  # All have been used, reset
        
        chosen = random.choice(available)
        
        # Add to history
        history.append(chosen)
        if len(history) > self.max_history_size:
            history.pop(0)
        
        return chosen
    
    def _fallback_response(self, scammer_message: str, message_count: int, session_id: str = "default") -> Dict:
        """Smart context-aware fallback response with variety and progression"""
        import re
        
        message_lower = scammer_message.lower()
        
        # Determine conversation stage for progressive responses
        is_early = message_count < 5
        is_mid = 5 <= message_count < 12
        is_late = message_count >= 12
        
        # Detect what scammer is asking for and respond contextually
        responses = []
        
        # OTP/PIN/CODE requests - Progressive confusion to fake info
        if any(word in message_lower for word in ['otp', 'pin', 'code', 'verification', 'cvv', 'digit']):
            if is_early:
                responses = [
                    "otp? where do i find that?",
                    "wait what code? didnt recieve anything",
                    "which code ur talking about",
                    "code? i dont see any msg",
                    "where shud i check for the code",
                    "no msg came on my phone",
                    "otp means what exactly?",
                    "checking my messages... nothing here",
                    "u mean password? or some other code",
                    "confused... what kind of code"
                ]
            elif is_mid:
                responses = [
                    "ok i see some msgs now... which one is it??",
                    "theres like 5 messages here which code do u want",
                    "wait lemme check properly... one sec",
                    "is it the code from 1234 number or 5678?",
                    "my phone shows multiple codes im confused",
                    "checking sms folder... lots of old msgs",
                    "do u mean the code that came yesterday?",
                    "found some numbers but not sure if thats otp",
                    "is otp same as verification code or different?",
                    "k checking... phone is slow tho"
                ]
            else:  # Late stage - give fake info or get suspicious
                responses = [
                    "ok i think its 123456 is that right?",
                    "the code shows 000000 is that normal?",
                    "it says 111111 but seems fake lol",
                    "got 987654 from bank is that correct",
                    "wait why do YOU need my code? cant u see it?",
                    "my friend said never share otp with anyone",
                    "isnt otp supposed to be private or something",
                    "code is 567890 but idk if i shud share it",
                    "bank msg says dont share otp... now im confused",
                    "hold on this feels weird. y do u need my code"
                ]
        
        # Account number / Personal info requests
        elif any(word in message_lower for word in ['account number', 'account no', 'card number', 'account details', 'personal']):
            if is_early:
                responses = [
                    "account number? let me check my passbook",
                    "i dont remember it... where can i find it",
                    "is it on the atm card or different",
                    "give me a min to find my account number",
                    "i have card number is that same thing?",
                    "checking my old statements",
                    "is account number same as customer id?"
                ]
            elif is_mid:
                responses = [
                    "ok found my card... its 16 digits right?",
                    "the number starts with 1234 is that enough",
                    "writing it down from passbook... bit faded",
                    "account number is 9876543210 or something like that",
                    "my card shows lot of numbers which one u need",
                    "is it 10 digit or 12 digit number"
                ]
            else:
                responses = [
                    "account is 123456789012 but why u need full number",
                    "wait shouldnt bank already have my account number??",
                    "feels strange giving account details... u sure its safe",
                    "my account is 9876543210123456 hope thats right",
                    "hmm my cousin told me to never share account details"
                ]
        
        # Payment/Money requests - show concern
        elif any(word in message_lower for word in ['payment', 'send money', 'transfer', 'pay', 'upi', 'paytm', 'amount']):
            if is_early:
                responses = [
                    "payment? what am i paying for",
                    "how much money do u need?",
                    "why do i need to pay exactly",
                    "payment for what service?",
                    "this is confusing... what payment",
                    "do i really have to pay something",
                    "how much is the amount"
                ]
            elif is_mid:
                responses = [
                    "ok so i need to pay how much exactly?",
                    "can i pay tomorrow? dont have money rn",
                    "is ₹100 enough or u need more",
                    "my balance is low can i pay ₹50 only",
                    "upi id? which id shud i send to",
                    "paytm or gpay which one works for u"
                ]
            else:
                responses = [
                    "wait if ur from bank why am I paying u?",
                    "this doesnt make sense... banks dont ask for payment like this",
                    "sending ₹1 first to check if its real",
                    "my friend said this sounds like scam now im worried",
                    "cant i just go to bank branch instead"
                ]
        
        # Link clicks - act cautious
        elif any(word in message_lower for word in ['click', 'link', 'website', 'url', 'download', 'install', 'app']):
            if is_early:
                responses = [
                    "link? let me see... where is it",
                    "which link ur talking about",
                    "ok i see a link but is it safe",
                    "never clicked random links before",
                    "what happens when i click it",
                    "my phone shows warning about this link",
                    "shud i click it on phone or computer"
                ]
            elif is_mid:
                responses = [
                    "clicked the link... its loading slow",
                    "page is not opening properly",
                    "it says website not secure should i continue",
                    "link opened but asking for lots of permissions",
                    "chrome is showing red warning is that ok",
                    "page is in english... hard to understand"
                ]
            else:
                responses = [
                    "wait this link looks suspicious",
                    "my antivirus blocked it saying its dangerous",
                    "why cant u just tell me instead of sending link",
                    "these types of links are how people get hacked no?",
                    "googled it and people saying its fake site"
                ]
        
        # Account/Bank issues - show worry
        elif any(word in message_lower for word in ['account', 'bank', 'suspend', 'block', 'kyc', 'locked', 'deactivate']):
            if is_early:
                responses = [
                    "omg my account is blocked?? serious",
                    "what happened to my account",
                    "why would bank block it? i didnt do anything",
                    "is this for real or ur joking",
                    "how do i check if my account is ok",
                    "when did it get blocked i just used it yesterday",
                    "this is scary what do i do now"
                ]
            elif is_mid:
                responses = [
                    "ok ok how do i unblock it tell me fast",
                    "what documents do u need for kyc",
                    "is there a fine or something to pay",
                    "how long will it take to fix this",
                    "can i still withdraw money or everything is blocked",
                    "will my salary credit come or that also blocked"
                ]
            else:
                responses = [
                    "but i checked internet banking and everything looks normal",
                    "called bank customer care and they said account is fine",
                    "u sure ur from real bank? this feels off",
                    "my account statement is working fine tho",
                    "banks usually send email for this... didnt get any"
                ]
        
        # Urgency/Threats - express concern then suspicion
        elif any(word in message_lower for word in ['urgent', 'immediate', 'now', 'hurry', 'quick', 'minutes', 'hours', 'expire', 'last chance']):
            if is_early:
                responses = [
                    "omg so urgent?? what should i do",
                    "ok ok dont panic me... tell me what to do",
                    "how much time do i have exactly",
                    "wait slow down im getting confused",
                    "this is making me nervous",
                    "cant breathe... too much pressure"
                ]
            elif is_mid:
                responses = [
                    "trying my best but ur going too fast",
                    "give me a minute to think properly",
                    "rushing me is making it harder to understand",
                    "can u extend the time a bit",
                    "let me call my son and ask him"
                ]
            else:
                responses = [
                    "wait why so much hurry... sounds fishy",
                    "real bank gives more time than this",
                    "this urgency tactic feels like those scam messages",
                    "my daughter works in bank she said this is not how banks work",
                    "if its that urgent why not call me officially"
                ]
        
        # Prize/Lottery - act excited but confused
        elif any(word in message_lower for word in ['won', 'prize', 'winner', 'lottery', 'congratulations', 'selected', 'lucky']):
            if is_early:
                responses = [
                    "omg really?? i won something",
                    "wow this is amazing! what did i win",
                    "how did i win? didnt even participate",
                    "are u sure its me not someone else",
                    "whats the prize amount",
                    "this sounds too good to be true"
                ]
            elif is_mid:
                responses = [
                    "ok so what do i need to do to claim it",
                    "when will i get the prize money",
                    "is there any tax or fees to pay first",
                    "do i need to come to office or online process",
                    "how did u get my number for this"
                ]
            else:
                responses = [
                    "wait why do i have to pay to get my prize??",
                    "my son said lotteries dont ask for payment beforehand",
                    "this is feeling like those fake lottery scams",
                    "if i won why am i paying u... that makes no sense",
                    "googled this and its showing scam warning"
                ]
        
        # Generic fallback responses with variety
        else:
            if is_early:
                responses = [
                    "what do u mean exactly",
                    "i dont understand can u explain",
                    "confused... say that again",
                    "sorry didnt get that",
                    "can u explain in simple words",
                    "not sure what ur asking",
                    "wait what are u trying to say"
                ]
            elif is_mid:
                responses = [
                    "ok im trying to understand but its confusing",
                    "can u break it down step by step",
                    "ur explanation is too technical for me",
                    "im not good with these things sorry",
                    "let me ask someone who knows better",
                    "give me a minute to process this"
                ]
            else:
                responses = [
                    "this is getting too complicated",
                    "ive been trying to understand but still confused",
                    "maybe i should just go to bank tomorrow",
                    "this conversation is going nowhere",
                    "i think there is some miscommunication",
                    "let me talk to bank directly instead"
                ]
        
        # Get unique response from the pool
        chosen_response = self._get_unique_response(responses, session_id)
        
        return {
            'response': chosen_response,
            'strategy': 'context_aware_fallback',
            'should_continue': message_count < 20,
            'notes': f'Fallback response (stage: {"early" if is_early else "mid" if is_mid else "late"}) to: {message_lower[:50]}'
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
