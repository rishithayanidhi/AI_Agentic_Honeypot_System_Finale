from typing import Optional, List, Dict, Any
from google import genai
from anthropic import Anthropic
from config import settings
from src.models.schemas import Message
import logging
import json
import hashlib
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


class ScamDetector:
    """AI-powered scam detection service with automatic fallback and caching"""
    
    def __init__(self):
        self.primary_provider = settings.LLM_PROVIDER
        self.available_providers = []
        self.clients = {}
        self.models = {}
        self.gemini_key_index = 0  # Track current Gemini key for rotation
        self.gemini_clients = []  # Multiple Gemini clients for key rotation
        self.detection_cache = {}  # In-memory cache for faster repeated detections
        self.cache_max_size = settings.CACHE_MAX_SIZE  # Dynamic cache size
        
        # Initialize all available providers dynamically
        self._initialize_providers()
    
    def _get_cache_key(self, message: str) -> str:
        """Generate cache key for message"""
        return hashlib.md5(message.lower().strip().encode()).hexdigest()
    
    def _add_to_cache(self, message: str, result: dict):
        """Add detection result to cache"""
        if len(self.detection_cache) >= self.cache_max_size:
            # Remove oldest entry (simple FIFO)
            self.detection_cache.pop(next(iter(self.detection_cache)))
        
        cache_key = self._get_cache_key(message)
        self.detection_cache[cache_key] = result
        logger.debug(f"Cached detection result for message: {message[:50]}...")
    
    def _initialize_providers(self):
        """Initialize LLM providers (Claude Haiku 4.5, Gemini)"""
        # Try Anthropic (Claude Haiku 4.5) - Primary
        try:
            if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "your-anthropic-api-key-here":
                self.clients['anthropic'] = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                self.models['anthropic'] = settings.ANTHROPIC_MODEL
                self.available_providers.append('anthropic')
                logger.info(f"🚀 Scam Detector: Claude Haiku 4.5 initialized with model: {settings.ANTHROPIC_MODEL}")
        except Exception as e:
            logger.warning(f"Scam Detector: Failed to initialize Claude: {e}")
        
        # Try Gemini with multiple API keys - Fallback
        try:
            gemini_keys = settings.get_gemini_api_keys()
            if gemini_keys:
                for idx, api_key in enumerate(gemini_keys):
                    try:
                        client = genai.Client(api_key=api_key)
                        self.gemini_clients.append(client)
                        logger.info(f"Scam Detector: Gemini client {idx + 1} initialized (key: ...{api_key[-4:]})")
                    except Exception as key_error:
                        logger.warning(f"Scam Detector: Failed to initialize Gemini key {idx + 1}: {key_error}")
                
                if self.gemini_clients:
                    self.clients['gemini'] = self.gemini_clients[0]  # For compatibility
                    self.models['gemini'] = settings.GEMINI_MODEL
                    self.available_providers.append('gemini')
                    logger.info(f"✅ Scam Detector: {len(self.gemini_clients)} Gemini API key(s) initialized")
        except Exception as e:
            logger.warning(f"Scam Detector: Failed to initialize Gemini: {e}")
        
        if not self.available_providers:
            logger.warning("No LLM providers available - will use keyword-based detection only")
        else:
            logger.info(f"✅ Available providers: {', '.join(self.available_providers)}")
    
    def _call_llm(self, provider: str, prompt: str) -> str:
        """Call LLM (Claude Haiku 4.5 or Gemini) with error handling - optimized for speed"""
        try:
            if provider == "anthropic":
                # Claude Haiku 4.5 - Ultra fast and cost-effective
                response = self.clients['anthropic'].messages.create(
                    model=self.models['anthropic'],
                    max_tokens=settings.LLM_MAX_TOKENS_DETECTION,
                    temperature=settings.LLM_TEMPERATURE_DETECTION,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                result_text = response.content[0].text
                logger.info(f"🚀 Scam Detector: Successfully used Claude Haiku 4.5")
                logger.debug(f"Scam Detector: Claude response: {result_text[:200]}...")
                return result_text
            
            elif provider == "gemini":
                # Prioritize Flash models for speed, then fallback to Pro for quality
                gemini_models = [
                    'models/gemini-2.5-flash',      # Fastest
                    'models/gemini-flash-latest',    # Fast fallback
                    'models/gemini-2.0-flash',       # Fast alternative
                    self.models['gemini'],           # User configured
                    'models/gemini-2.5-pro',         # Quality fallback
                    'models/gemini-pro-latest'       # Last resort
                ]
                
                # Try each Gemini client (rotating through API keys on quota errors)
                for client_attempt in range(len(self.gemini_clients)):
                    current_client = self.gemini_clients[self.gemini_key_index]
                    
                    last_error = None
                    for model_name in gemini_models:
                        try:
                            # Use proper generation configuration
                            response = current_client.models.generate_content(
                                model=model_name,
                                contents=prompt,
                                config={
                                    'temperature': settings.LLM_TEMPERATURE_DETECTION,
                                    'maxOutputTokens': settings.LLM_MAX_TOKENS_DETECTION,
                                    'topP': 0.95,
                                    'topK': 40
                                }
                            )
                            
                            # Check if response was blocked or incomplete
                            if hasattr(response, 'candidates') and response.candidates:
                                candidate = response.candidates[0]
                                if hasattr(candidate, 'finish_reason'):
                                    logger.info(f"Finish reason: {candidate.finish_reason}")
                            
                            logger.info(f"Scam Detector: Successfully used Gemini model: {model_name} (key {self.gemini_key_index + 1})")
                            
                            # Extract text from response - try different methods
                            result_text = ""
                            try:
                                # Primary method: use .text property
                                result_text = response.text
                            except Exception as e:
                                logger.debug(f"Could not get .text property: {e}")
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
                            
                            logger.debug(f"Raw response from {model_name}: {result_text[:200]}...")
                            return result_text
                        except Exception as model_error:
                            last_error = model_error
                            error_msg = str(model_error).lower()
                            
                            # Check if it's a quota error - if so, try next model with current key
                            if "429" in error_msg or "resource_exhausted" in error_msg or "quota" in error_msg:
                                logger.warning(f"Scam Detector: Gemini model {model_name} quota exceeded (key {self.gemini_key_index + 1})")
                                continue
                            else:
                                logger.warning(f"Scam Detector: Gemini model {model_name} failed: {model_error}")
                                continue
                    
                    # All models failed with current key, try rotating to next key
                    if len(self.gemini_clients) > 1 and client_attempt < len(self.gemini_clients) - 1:
                        self.gemini_key_index = (self.gemini_key_index + 1) % len(self.gemini_clients)
                        logger.warning(f"Scam Detector: Rotating to Gemini API key {self.gemini_key_index + 1}")
                        continue
                    else:
                        # All keys exhausted, raise the last error
                        if last_error:
                            raise last_error
            
            raise ValueError(f"Unknown provider: {provider}")
            
        except Exception as e:
            logger.error(f"Error calling {provider}: {e}")
            raise
    
    def detect_scam(self, message: str, conversation_history: List[Message] = None) -> dict:
        """
        Detect if a message is a scam with caching for performance
        Returns: {
            'is_scam': bool,
            'confidence': float,
            'scam_type': str,
            'reasoning': str
        }
        """
        
        # Check cache first for faster response
        cache_key = self._get_cache_key(message)
        if cache_key in self.detection_cache:
            logger.info(f"Cache hit for message detection")
            cached_result = self.detection_cache[cache_key].copy()
            cached_result['reasoning'] = cached_result.get('reasoning', '') + ' [cached]'
            return cached_result
        
        # Build context from conversation history
        context = ""
        if conversation_history:
            context = "Previous conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                context += f"{msg.sender}: {msg.text}\n"
        
        prompt = f"""Analyze the following message and determine if it's a scam or fraudulent attempt.

{context}

Current message to analyze: "{message}"

Consider these scam indicators:
1. Urgency tactics (immediate action required, account will be blocked)
2. Request for sensitive information (UPI ID, bank details, OTP, passwords)
3. Threats or fear tactics
4. Too-good-to-be-true offers (prizes, lottery wins)
5. Impersonation of banks, government, or official entities
6. Suspicious links or payment requests
7. Poor grammar or spelling (sometimes)
8. Unsolicited contact

Respond ONLY with a JSON object (no markdown):
{{
  "is_scam": true/false,
  "confidence": 0.0-1.0,
  "scam_type": "bank_fraud/upi_fraud/phishing/fake_offer/other/none",
  "reasoning": "brief explanation",
  "key_indicators": ["indicator1", "indicator2"]
}}"""

        # Try LLM first (respects LLM_PROVIDER setting), fallback to keywords
        if not self.available_providers:
            logger.info("No LLM available - using keyword detection")
            return self._fallback_detection(message)
        
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
                logger.info(f"Attempting scam detection with provider: {provider}")
                result = self._call_llm(provider, prompt)
                
                # Log raw result details
                logger.info(f"Received response length: {len(result)} characters")
                logger.debug(f"First 100 chars: {repr(result[:100])}")
                logger.debug(f"Last 100 chars: {repr(result[-100:])}")
                
                # Clean JSON from markdown code blocks (Gemini often wraps in ```json```)
                result_clean = result.strip()
                if result_clean.startswith('```'):
                    # Remove code fence markers
                    result_clean = result_clean.replace('```json', '').replace('```', '')
                    # Clean up any remaining whitespace
                    result_clean = result_clean.strip()
                
                # Extract JSON from text (handles cases like "Here is the JSON: {...}")
                result_clean = extract_json_from_text(result_clean)
                
                # Parse JSON response
                detection_result = json.loads(result_clean)
                logger.info(f"Successfully detected with {provider}: is_scam={detection_result.get('is_scam')}")
                
                # Cache successful detection
                self._add_to_cache(message, detection_result)
                
                return detection_result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error from {provider}: {e}. Raw result: {result[:500] if result else 'None'}")
                last_error = e
                continue
            except Exception as e:
                logger.error(f"Error with {provider}: {e}")
                last_error = e
                continue
        
        # All LLM providers failed - use keyword-based fallback
        logger.warning(f"All LLM providers failed (last error: {last_error}) - using keyword-based fallback")
        fallback_result = self._fallback_detection(message)
        
        # Cache fallback result too (for repeated messages)
        self._add_to_cache(message, fallback_result)
        return fallback_result
        self._add_to_cache(message, fallback_result)
        
        return fallback_result
    
    def _fallback_detection(self, message: str) -> dict:
        """Enhanced keyword-based scam detection with intelligent type classification"""
        import re
        
        message_lower = message.lower()
        logger.info(f"🔍 ANALYZING MESSAGE: '{message[:100]}...'")
        
        # Category-specific keyword patterns for intelligent classification
        bank_fraud_keywords = ['bank', 'account', 'customer', 'account blocked', 'account suspended', 'kyc', 'ifsc', 'atm', 'debit card', 'credit card', 'sbi', 'hdfc', 'icici', 'axis', 'verify your identity']
        upi_fraud_keywords = ['upi', 'paytm', 'phonepe', 'gpay', 'google pay', 'bhim', 'payment', 'transfer', 'send money', 'wallet']
        phishing_keywords = ['click', 'link', 'verify', 'confirm', 'website', 'login', 'password', 'download', 'update now']
        lottery_keywords = ['won', 'winner', 'prize', 'lottery', 'jackpot', 'claim', 'congratulations', 'lucky', 'selected', 'crore', 'lakh']
        
        # General urgency/scam indicators
        urgency_keywords = ['urgent', 'immediate', 'now', 'today', 'expire', 'last chance', 'limited time']
        threat_keywords = ['block', 'blocked', 'suspend', 'suspended', 'close', 'terminate', 'legal action', 'police', 'will be blocked']
        sensitive_keywords = ['otp', 'pin', 'password', 'cvv', 'card number', 'account number', 'verification code']
        
        # Count matches per category
        bank_score = sum(1 for kw in bank_fraud_keywords if kw in message_lower)
        upi_score = sum(1 for kw in upi_fraud_keywords if kw in message_lower)
        phishing_score = sum(1 for kw in phishing_keywords if kw in message_lower)
        lottery_score = sum(1 for kw in lottery_keywords if kw in message_lower)
        urgency_score = sum(1 for kw in urgency_keywords if kw in message_lower)
        threat_score = sum(1 for kw in threat_keywords if kw in message_lower)
        sensitive_score = sum(1 for kw in sensitive_keywords if kw in message_lower)
        
        logger.info(f"📊 KEYWORD SCORES: Bank={bank_score}, UPI={upi_score}, Phishing={phishing_score}, Lottery={lottery_score}, Urgency={urgency_score}, Threat={threat_score}, Sensitive={sensitive_score}")
        
        # Check for URLs and links (strong phishing indicator)
        has_url = bool(re.search(r'http[s]?://[^\s]+', message))
        has_short_url = bool(re.search(r'\b(?:bit\.ly|tinyurl|goo\.gl|ow\.ly|short\.link|t\.co)/[a-zA-Z0-9\-_]+', message, re.IGNORECASE))
        has_suspicious_link = bool(re.search(r'\b\w+\.\w+/\w+', message))
        
        # Phone number patterns (Indian format)
        has_phone = bool(re.search(r'(?:\+91|91)?[6-9]\d{9}', message))
        
        if has_url or has_short_url or has_suspicious_link or has_phone:
            logger.info(f"🔗 PATTERNS FOUND: URL={has_url}, ShortURL={has_short_url}, SuspiciousLink={has_suspicious_link}, Phone={has_phone}")
        
        # Calculate base score
        base_score = urgency_score + threat_score + sensitive_score
        
        # URL scoring
        if has_url or has_short_url:
            phishing_score += 3
            base_score += 3
        elif has_suspicious_link:
            phishing_score += 1
            base_score += 1
        
        # Phone number in suspicious context
        if has_phone and (urgency_score > 0 or threat_score > 0):
            base_score += 1
        
        # OTP + Threat combo is very strong bank fraud indicator
        if sensitive_score > 0 and threat_score > 0:
            bank_score += 2
            base_score += 2
        
        # Determine scam type based on scores
        total_score = base_score
        scam_type = 'none'
        type_confidence = 0.0
        
        if lottery_score >= 2:
            scam_type = 'fake_offer'
            type_confidence = min(lottery_score * settings.LOTTERY_CONFIDENCE_MULTIPLIER, settings.MAX_CONFIDENCE)
            total_score += lottery_score
        elif bank_score >= 2 or (sensitive_score > 0 and threat_score > 0):
            # OTP + threat OR bank keywords = bank_fraud
            scam_type = 'bank_fraud'
            type_confidence = min((bank_score + sensitive_score + threat_score) * settings.BANK_FRAUD_CONFIDENCE_MULTIPLIER, settings.MAX_CONFIDENCE)
            total_score += bank_score
        elif upi_score >= 2:
            scam_type = 'upi_fraud'
            type_confidence = min(upi_score * settings.UPI_CONFIDENCE_MULTIPLIER, settings.MAX_CONFIDENCE)
            total_score += upi_score
        elif (has_url or has_short_url) and phishing_score >= 2:
            scam_type = 'phishing'
            type_confidence = min(phishing_score * settings.PHISHING_CONFIDENCE_MULTIPLIER, settings.MAX_CONFIDENCE)
            total_score += phishing_score
        elif base_score >= 3:
            scam_type = 'potential_scam'
            type_confidence = min(base_score * settings.GENERIC_CONFIDENCE_MULTIPLIER, 0.90)
        
        is_scam = total_score >= settings.SCAM_SCORE_THRESHOLD or type_confidence >= settings.SCAM_DETECTION_THRESHOLD
        
        # Detailed result logging
        if is_scam:
            logger.warning(f"🚨 SCAM DETECTED! Type: {scam_type}, Confidence: {type_confidence:.0%}, Total Score: {total_score}")
        else:
            logger.info(f"✅ NOT A SCAM. Total Score: {total_score} (threshold: {settings.SCAM_SCORE_THRESHOLD})")
        confidence = max(type_confidence, min(total_score * 0.2, settings.MAX_CONFIDENCE)) if is_scam else min(total_score * 0.1, settings.MIN_CONFIDENCE_NOT_SCAM)
        
        # Build reasoning
        indicators = []
        if bank_score > 0: indicators.append(f'{bank_score} bank-related terms')
        if upi_score > 0: indicators.append(f'{upi_score} UPI/payment terms')
        if lottery_score > 0: indicators.append(f'{lottery_score} lottery/prize terms')
        if urgency_score > 0: indicators.append(f'{urgency_score} urgency indicators')
        if threat_score > 0: indicators.append(f'{threat_score} threat indicators')
        if sensitive_score > 0: indicators.append(f'{sensitive_score} sensitive info requests')
        if has_url or has_short_url: indicators.append('suspicious URL')
        if has_phone: indicators.append('phone number')
        
        reasoning = f"Classified as {scam_type}: " + ", ".join(indicators) if indicators else "No significant scam indicators"
        
        return {
            'is_scam': is_scam,
            'confidence': confidence,
            'scam_type': scam_type,
            'reasoning': reasoning,
            'key_indicators': indicators
        }
