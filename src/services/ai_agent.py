from typing import List, Optional, Dict, Any
from google import genai
from anthropic import Anthropic
from config import settings
from src.models.schemas import Message
import random
import logging
import json
import re

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
    
    def _call_llm(self, provider: str, prompt: str, temperature: float = 0.7) -> str:
        """Call LLM (Claude Haiku 4.5 or Gemini) with error handling - optimized for speed"""
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
                
                # Prioritize Flash models for speed
                gemini_models = [
                    'models/gemini-2.5-flash',      # Fastest
                    'models/gemini-flash-latest',    # Fast fallback
                    'models/gemini-2.0-flash',       # Fast alternative
                    self.models['gemini'],           # User configured
                    'models/gemini-2.5-pro',         # Quality fallback
                    'models/gemini-pro-latest'       # Last resort
                ]
                
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
                                # Try next model with current key
                                continue
                            else:
                                # Non-quota error, try next model
                                logger.warning(f"AI Agent: Gemini model {model_name} failed: {model_error}")
                                continue
                    
                    # All models failed with current key, rotate to next key
                    if len(self.gemini_clients) > 1:
                        self.gemini_key_index = (self.gemini_key_index + 1) % len(self.gemini_clients)
                        logger.warning(f"AI Agent: Rotating to Gemini API key {self.gemini_key_index + 1}")
                    else:
                        # Only one key, can't rotate
                        break
                
                # If all models and all keys failed, raise the last error
                if last_error:
                    raise last_error
            
            raise ValueError(f"Unknown provider: {provider}")
            
        except Exception as e:
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
        """Smart context-aware fallback response"""
        import re
        
        message_lower = scammer_message.lower()
        
        # Detect what scammer is asking for and respond contextually
        responses = []
        
        # OTP/PIN requests - act confused
        if any(word in message_lower for word in ['otp', 'pin', 'code', 'verification code', 'cvv']):
            responses = [
                "wait, what code? i didnt get any msg",
                "otp? where do i find that?",
                "which code ur talking about? confused"
            ]
        
        # Payment/Money requests - show concern
        elif any(word in message_lower for word in ['payment', 'send money', 'transfer', 'pay', 'upi', 'paytm']):
            responses = [
                "how much do i need to send?",
                "what is the payment for exactly?",
                "do i really need to pay? seems weird"
            ]
        
        # Link clicks - act cautious
        elif any(word in message_lower for word in ['click', 'link', 'website', 'url', 'download']):
            responses = [
                "is this link safe? never clicked random links before",
                "what happens if i click it?",
                "my phone says its not secure, shud i still click?"
            ]
        
        # Account/Bank issues - show worry
        elif any(word in message_lower for word in ['account', 'bank', 'suspend', 'block', 'kyc']):
            responses = [
                "omg is my account really blocked?? what did i do wrong",
                "how do i check if my account is ok?",
                "why would they block it? i havnt done anything"
            ]
        
        # Urgency/Threats - express concern
        elif any(word in message_lower for word in ['urgent', 'immediate', 'now', 'expire', 'last chance']):
            responses = [
                "wait wait slow down, what do i need to do exactly?",
                "ok ok im panicking now, help me fix this",
                "how much time do i have? this is scary"
            ]
        
        # Prize/Lottery - act excited but confused
        elif any(word in message_lower for word in ['won', 'prize', 'winner', 'lottery', 'congratulations']):
            responses = [
                "omg really?? how did i win? didnt even participate",
                "wow thats amazing! what do i need to do to get it?",
                "are u sure its me? sounds too good"
            ]
        
        # Generic fallback responses
        else:
            responses = [
                "i dont understand, can u explain more?",
                "what do u mean exactly?",
                "sorry im confused, say that again?",
                "ok but how do i do that?",
                "wait what?? ur going too fast"
            ]
        
        return {
            'response': random.choice(responses),
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
