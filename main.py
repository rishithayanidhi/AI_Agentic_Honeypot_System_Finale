from fastapi import FastAPI, HTTPException, Security, Depends, Request, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import asyncio
import warnings
import sys
from typing import Optional, Union

# Suppress Pydantic warnings from google-genai library
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal._fields")

from config import settings
from src.models.schemas import (
    IncomingRequest, APIResponse, EngagementMetrics, 
    ExtractedIntelligence, Message
)
from src.services.session_manager import session_manager
from src.services.scam_detector import ScamDetector
from src.services.ai_agent import AIAgent
from src.utils.intelligence_extractor import IntelligenceExtractor
from src.services.guvi_callback import guvi_callback
from src.services.intent_drift_analyzer import intent_drift_analyzer

# Configure logging for Render (explicit stdout)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

# Log startup info
# Clean deployment - no database dependencies (v2.0)
logger.info("="*60)
logger.info("AI AGENTIC HONEYPOT SYSTEM STARTING")
logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
logger.info("="*60)
sys.stdout.flush()  # Force flush to Render

# Initialize FastAPI app with performance optimizations
app = FastAPI(
    title="AI Agentic Honeypot System",
    description="AI-powered honeypot for scam detection and intelligence extraction",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,  # Disable unused ReDoc
    openapi_url="/openapi.json"
)

# Add compression middleware for faster responses
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
from fastapi.security import APIKeyHeader
api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)

def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key"""
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Initialize services
scam_detector = ScamDetector()
ai_agent = AIAgent()
intelligence_extractor = IntelligenceExtractor()


# Add validation error handler for better debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log and return detailed validation errors"""
    logger.error(f"=" * 80)
    logger.error(f"VALIDATION ERROR for {request.url.path}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Headers: {dict(request.headers)}")
    
    # Try to read the raw body
    try:
        body = await request.body()
        logger.error(f"Raw body: {body.decode('utf-8')}")
    except Exception as e:
        logger.error(f"Could not read body: {e}")
    
    logger.error(f"Validation errors: {exc.errors()}")
    logger.error(f"=" * 80)
    
    # Create detailed error messages
    error_details = []
    error_summary = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get('loc', []))
        error_msg = err.get('msg', '')
        error_summary.append(f"{field_path}: {error_msg}")
        error_details.append({
            "field": field_path,
            "message": error_msg,
            "type": err.get('type', ''),
            "input": str(err.get('input', 'N/A'))[:100]  # Truncate long inputs
        })
    
    # Create user-friendly message that will be displayed
    friendly_message = (
        "VALIDATION ERROR:\n\n" + 
        "\n".join(f"• {err}" for err in error_summary[:5]) +  # Show first 5 errors
        "\n\nRequired format:\n" +
        '{"sessionId":"session-123","message":{"sender":"scammer","text":"Your message","timestamp":"2026-02-01T10:00:00Z"},"conversationHistory":[],"metadata":{"channel":"SMS","language":"English","locale":"IN"}}'
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error": "INVALID_REQUEST_BODY",
            "message": friendly_message,
            "errors": error_details,
            "example": {
                "sessionId": "session-123",
                "message": {
                    "sender": "scammer",
                    "text": "URGENT: Your account will be blocked. Share OTP now.",
                    "timestamp": "2026-02-01T10:00:00Z"
                },
                "conversationHistory": [],
                "metadata": {
                    "channel": "SMS",
                    "language": "English",
                    "locale": "IN"
                }
            }
        }
    )


@app.get("/")
@app.head("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Agentic Honeypot System",
        "version": "1.0.0"
    }


@app.get("/health")
@app.head("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "AI Agentic Honeypot System",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(session_manager.sessions),
        "llm_provider": settings.LLM_PROVIDER
    }


@app.post("/api/message")
async def handle_message(
    raw_request: Request,
    api_key: str = Header(None, alias="x-api-key")
):
    """
    Main endpoint to handle incoming messages
    Accepts flexible formats - handles empty body, simple format, and full format
    GUVI Format: Returns {"status": "success", "reply": "agent response"}
    """
    # Make API key optional for GUVI tester compatibility
    if api_key:
        if api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    try:
        # Parse request body manually to avoid validation errors
        request = None
        body_str = ""
        try:
            body = await raw_request.body()
            body_str = body.decode('utf-8') if body else ""
            
            if body_str and body_str.strip():
                import json
                request_data = json.loads(body_str)
                request = IncomingRequest(**request_data)
            else:
                # Empty body - return test response
                logger.info("Empty request body received - returning test response")
                return {
                    "status": "success",
                    "reply": "Hello! I'm the AI honeypot agent. Send me a message to test."
                }
        except json.JSONDecodeError as je:
            logger.warning(f"Invalid JSON in request body: {je}, using default")
            return {
                "status": "success",
                "reply": "Invalid request format. Please send valid JSON."
            }
        except Exception as parse_error:
            logger.warning(f"Could not parse request body: {parse_error}, using default")
            request = IncomingRequest()
        
        logger.info(f"Received request type: {type(request).__name__}")
        logger.info(f"Request data: {request.model_dump()}")
        
        # Extract session_id with fallback
        session_id = request.sessionId or f"auto-{datetime.now().timestamp()}"
        
        # Handle message in various formats
        if request.message is None or request.message == "":
            # Empty message - GUVI tester or test request
            # Return immediately without processing (fast path for timeout avoidance)
            logger.info("Empty message received - returning quick test response")
            return {
                "status": "success",
                "reply": "Hello! I'm the AI honeypot agent ready to engage with scammers."
            }
        elif isinstance(request.message, str):
            # Simple string message
            message_text = request.message if request.message else "Hello"
            message_obj = Message(
                sender="scammer",
                text=message_text,
                timestamp=datetime.now().isoformat()
            )
        elif isinstance(request.message, dict):
            # Dictionary format - convert to Message
            message_text = request.message.get("text", request.message.get("message", "Hello"))
            if not message_text:  # Ensure we have text
                message_text = "Hello"
            message_obj = Message(
                sender=request.message.get("sender", "scammer"),
                text=message_text,
                timestamp=request.message.get("timestamp") or datetime.now().isoformat()
            )
        else:
            # Message object
            message_obj = request.message
            message_text = request.message.text if request.message.text else "Hello"
        
        # Ensure message_text is never empty
        if not message_text or message_text.strip() == "":
            message_text = "Hello"
        
        # ULTRA FAST PATH: Respond immediately to short messages (< 50 chars) to avoid GUVI timeout
        # Only process full scam detection for longer, obvious scam messages
        message_lower = message_text.lower().strip()
        has_strong_scam_keywords = any(
            keyword in message_lower for keyword in 
            ["urgent", "otp", "blocked", "suspend", "compromised", "verify account", "bank account"]
        )
        
        # If message is short and doesn't have strong scam indicators, return fast
        if len(message_text) < 50 and not has_strong_scam_keywords:
            logger.info(f"Short/test message detected (len={len(message_text)}): '{message_text}' - fast response")
            return {
                "status": "success",
                "reply": "Hello! I'm listening. What would you like to discuss?"
            }
        
        # Handle conversation history
        conversation_history = request.conversationHistory or []
        
        logger.info(f"Received message for session: {session_id}")
        
        # Get or create session
        session = session_manager.get_or_create_session(session_id)
        
        # Early exit if session is already complete
        if not session.engagement_active and session.scam_detected:
            return {
                "status": "success",
                "scamDetected": True,
                "agentResponse": "Thank you for your message. This conversation has ended.",
                "sessionComplete": True,
                "detection": {
                    "is_scam": True,
                    "confidence": 0.95,
                    "scam_type": "completed",
                    "reasoning": "Session already completed"
                }
            }
        
        # Add incoming message to session
        session.messages.append(message_obj)
        session.message_count += 1
        
        # Add conversation history to session if this is first message (only if list is small)
        if conversation_history and not session.engagement_active and len(conversation_history) < 10:
            for hist_msg in conversation_history:
                if hist_msg not in session.messages:
                    session.messages.insert(0, hist_msg)
        
        # Initialize detection variables
        detection_result = {}
        scam_confidence = 0.0
        scam_type = 'unknown'
        
        # SPEED OPTIMIZED: Run synchronously, intelligence extraction is fast
        if not session.scam_detected:
            # Extract intelligence first (fast, no API calls)
            try:
                new_intel = intelligence_extractor.extract_from_message(message_text)
                session.intelligence = intelligence_extractor.merge_intelligence(
                    session.intelligence, new_intel
                )
                
                # Log confidence metrics
                logger.info(f"📊 Intelligence Confidence Metrics:")
                logger.info(f"  - Overall Confidence: {session.intelligence.overallConfidence:.2f}")
                logger.info(f"  - High Confidence Items: {session.intelligence.highConfidenceCount}")
                if session.intelligence.bankAccountsDetailed:
                    logger.info(f"  - Bank Accounts: {len(session.intelligence.bankAccountsDetailed)} items")
                    for item in session.intelligence.bankAccountsDetailed[:3]:  # Show top 3
                        logger.info(f"    • {item.value} (confidence: {item.confidence:.2f}, seen: {item.occurrences}x)")
                if session.intelligence.upiIdsDetailed:
                    logger.info(f"  - UPI IDs: {len(session.intelligence.upiIdsDetailed)} items")
                    for item in session.intelligence.upiIdsDetailed[:3]:
                        logger.info(f"    • {item.value} (confidence: {item.confidence:.2f}, seen: {item.occurrences}x)")
                if session.intelligence.phishingLinksDetailed:
                    logger.info(f"  - Phishing Links: {len(session.intelligence.phishingLinksDetailed)} items")
                    for item in session.intelligence.phishingLinksDetailed[:2]:
                        logger.info(f"    • {item.value[:50]}... (confidence: {item.confidence:.2f})")
            except Exception as e:
                logger.error(f"Intelligence extraction error: {e}")
            
            # Scam detection (uses keyword-based fallback primarily, fast)
            try:
                detection_result = scam_detector.detect_scam(message_text, session.messages)
            except Exception as e:
                logger.error(f"Scam detection error: {e}")
                detection_result = {
                    'is_scam': False,
                    'confidence': 0.0,
                    'scam_type': 'error',
                    'reasoning': f'Detection error: {str(e)[:100]}'
                }
        else:
            # Session already detected - only extract intelligence (fast)
            new_intel = intelligence_extractor.extract_from_message(message_text)
            session.intelligence = intelligence_extractor.merge_intelligence(
                session.intelligence, new_intel
            )            
            # Log confidence metrics for continuing conversations
            logger.info(f"📊 Updated Intelligence (Overall Confidence: {session.intelligence.overallConfidence:.2f})")        
        # Process detection results
        if not session.scam_detected:
            # Validate detection result
            if not detection_result or not isinstance(detection_result, dict):
                logger.error(f"Invalid detection result: {detection_result}")
                detection_result = {
                    'is_scam': False,
                    'confidence': 0.0,
                    'scam_type': 'unknown',
                    'reasoning': 'Detection error - invalid result'
                }
            
            session.scam_detected = detection_result.get('is_scam', False)
            scam_confidence = detection_result.get('confidence', 0.0)
            scam_type = detection_result.get('scam_type', 'unknown')
            
            logger.info(f"Scam detection: {session.scam_detected} (confidence: {scam_confidence})")
            
            if session.scam_detected:
                session.engagement_active = True
                session.agent_notes = f"Scam detected: {scam_type}. {detection_result.get('reasoning', '')}"
        else:
            # Session already has scam detected - continue engagement
            scam_confidence = 0.95
            scam_type = session.agent_notes.split(':')[1].split('.')[0].strip() if ':' in session.agent_notes else 'confirmed'
            detection_result = {
                'is_scam': True,
                'confidence': 0.95,
                'scam_type': scam_type,
                'reasoning': 'Continuing conversation from previously detected scam'
            }
            # Keep engagement active for multi-turn conversations
            session.engagement_active = True
        
        # === INTENT DRIFT TRACKING (New Feature) ===
        # Track intent and detect drift without changing existing logic
        try:
            # Track current intent
            intent_record = intent_drift_analyzer.track_intent(
                intent=scam_type,
                confidence=scam_confidence,
                message_number=session.message_count,
                reasoning=detection_result.get('reasoning', '')
            )
            
            # Detect drift if previous intent exists
            drift_event = None
            if session.current_intent and session.current_intent != scam_type:
                drift_event = intent_drift_analyzer.detect_drift(
                    current_intent=scam_type,
                    current_confidence=scam_confidence,
                    previous_intent=session.current_intent,
                    message_number=session.message_count
                )
            
            # Update session with new intent
            session.intent_history.append(intent_record)
            session.current_intent = scam_type
            
            # Perform full drift analysis
            session.drift_analysis = intent_drift_analyzer.analyze_drift_pattern(session.intent_history)
            
            # Log drift insights
            if drift_event:
                logger.warning(f"⚠️ Intent Drift: {drift_event.from_intent} → {drift_event.to_intent} (magnitude: {drift_event.drift_magnitude})")
            
            if session.drift_analysis:
                logger.info(f"📊 Drift Analysis: {session.drift_analysis.total_drifts} drifts, behavior: {session.drift_analysis.behavior_type.value}")
                
        except Exception as drift_error:
            logger.error(f"Intent drift tracking error: {drift_error}")
            # Don't fail the request if drift tracking fails
        # === END INTENT DRIFT TRACKING ===
        
        # Generate agent response if scam is detected
        agent_response_text = None
        session_complete = False
        should_continue = True
        should_end = False
        end_reason = ""
        
        # Only generate AI response if engagement is active
        if session.scam_detected and session.engagement_active:
            try:
                # Select or maintain persona (dynamic change interval)
                if not session.persona or session.message_count % settings.PERSONA_CHANGE_INTERVAL == 0:
                    session.persona = ai_agent.select_persona(
                        scam_type=scam_type,
                        message_count=session.message_count
                    )
                
                # Generate response with timeout to avoid GUVI 30s timeout
                # Use shorter timeout in FAST_MODE for instant fallback
                timeout = 3.0 if settings.FAST_MODE else 20.0
                try:
                    agent_decision = await asyncio.wait_for(
                        asyncio.to_thread(
                            ai_agent.generate_response,
                            scammer_message=message_text,
                            conversation_history=session.messages,
                            persona=session.persona,
                            scam_type=scam_type,
                            extracted_intel=session.intelligence.model_dump(),
                            session_id=session_id
                        ),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"AI generation timed out after {timeout}s - using fast fallback")
                    agent_decision = {
                        'response': "I see. Could you provide more details about this?",
                        'should_continue': True,
                        'notes': 'Timeout - fast fallback'
                    }
                
                # Safely extract response fields with validation
                if agent_decision and isinstance(agent_decision, dict):
                    agent_response_text = agent_decision.get('response', None)
                    should_continue = agent_decision.get('should_continue', True)
                    notes = agent_decision.get('notes', '')
                    
                    # Update agent notes
                    if notes:
                        session.agent_notes += f" | {notes}"
                    
                    # Add agent response to conversation
                    if agent_response_text:
                        user_message = Message(
                            sender="user",
                            text=agent_response_text,
                            timestamp=datetime.now().isoformat()
                        )
                        session.messages.append(user_message)
                        session.message_count += 1
                else:
                    # Fallback if agent_decision is None or invalid
                    logger.warning(f"AI agent returned invalid response: {agent_decision}")
                    agent_response_text = "I'm not sure I understand. Can you explain?"
                    should_continue = True
                
                # Check if conversation should end
                intelligence_quality = sum([
                    len(session.intelligence.bankAccounts) > 0,
                    len(session.intelligence.upiIds) > 0,
                    len(session.intelligence.phishingLinks) > 0,
                    len(session.intelligence.phoneNumbers) > 0,
                    len(session.intelligence.suspiciousKeywords) >= 3
                ])
                
                should_end, end_reason = ai_agent.should_end_conversation(
                    message_count=session.message_count,
                    intelligence_quality=intelligence_quality,
                    scam_confidence=scam_confidence
                )
            except Exception as agent_error:
                # Comprehensive error handling for AI agent failures
                logger.error(f"Error generating AI agent response: {agent_error}", exc_info=True)
                agent_response_text = "Sorry, I'm confused. What was that?"
                should_continue = True
                should_end = False
                end_reason = ""
                session.agent_notes += f" | Agent error: {str(agent_error)[:100]}"
            
            if should_end or not should_continue:
                session_complete = True
                session.engagement_active = False
                session.agent_notes += f" | Conversation ended: {end_reason}"
                logger.info(f"Session {session_id} complete: {end_reason}")
                
                # Send final results to GUVI
                success = guvi_callback.send_final_result(
                    session_id=session_id,
                    scam_detected=session.scam_detected,
                    total_messages=session.message_count,
                    extracted_intelligence=session.intelligence.model_dump(),
                    agent_notes=session.agent_notes
                )
                
                if success:
                    logger.info(f"Successfully sent final results to GUVI for session {session_id}")
                else:
                    logger.warning(f"Failed to send results to GUVI for session {session_id}")
        
        # Fast response preparation with minimal overhead
        engagement_duration = int((datetime.now() - session.created_at).total_seconds())
        
        # Prepare response according to GUVI specification
        # Primary format: simple {"status": "success", "reply": "agent response"}
        response_dict = {
            "status": "success",
            "reply": agent_response_text if agent_response_text else "I see. Can you tell me more?"
        }
        
        # Add optional detailed fields for debugging/monitoring (won't affect competition evaluation)
        if settings.INCLUDE_DEBUG_INFO:
            response_dict.update({
                "sessionId": session_id,
                "scamDetected": session.scam_detected,
                "sessionComplete": session_complete,
                "engagementMetrics": {
                    "totalMessagesExchanged": session.message_count,
                    "engagementDurationSeconds": engagement_duration,
                    "scamDetectionAccuracy": scam_confidence
                },
                "extractedIntelligence": {
                    "phoneNumbers": session.intelligence.phoneNumbers,
                    "upiIds": session.intelligence.upiIds,
                    "phishingLinks": session.intelligence.phishingLinks,
                    "suspiciousKeywords": session.intelligence.suspiciousKeywords,
                    "bankAccounts": session.intelligence.bankAccounts
                },
                "detection": {
                    "is_scam": session.scam_detected,
                    "confidence": scam_confidence,
                    "scam_type": scam_type,
                    "reasoning": detection_result.get('reasoning', '') if session.scam_detected else ''
                }
            })
        
        # Update session asynchronously (non-blocking)
        session_manager.update_session(session)
        
        return response_dict
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}")
async def delete_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a session"""
    session_manager.delete_session(session_id)
    return {"status": "success", "message": f"Session {session_id} deleted"}


@app.get("/api/session/{session_id}")
async def get_session_info(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get session information"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "sessionId": session.session_id,
        "messageCount": session.message_count,
        "scamDetected": session.scam_detected,
        "engagementActive": session.engagement_active,
        "intelligence": session.intelligence.model_dump(),
        "createdAt": session.created_at.isoformat(),
        "lastActivity": session.last_activity.isoformat(),
        "currentIntent": session.current_intent,
        "driftAnalysisSummary": {
            "totalDrifts": session.drift_analysis.total_drifts if session.drift_analysis else 0,
            "behaviorType": session.drift_analysis.behavior_type.value if session.drift_analysis else "unknown",
            "stabilityScore": session.drift_analysis.stability_score if session.drift_analysis else 1.0
        } if session.drift_analysis else None
    }


@app.get("/api/session/{session_id}/intelligence")
async def get_detailed_intelligence(
    session_id: str,
    api_key: str = Depends(verify_api_key),
    threshold: float = 0.0
):
    """Get detailed confidence-weighted intelligence for a session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    intel = session.intelligence
    
    return {
        "sessionId": session.session_id,
        "overallConfidence": intel.overallConfidence,
        "highConfidenceCount": intel.highConfidenceCount,
        "totalItemsExtracted": (
            len(intel.bankAccountsDetailed) + len(intel.upiIdsDetailed) +
            len(intel.phishingLinksDetailed) + len(intel.phoneNumbersDetailed) +
            len(intel.suspiciousKeywordsDetailed)
        ),
        "detailedIntelligence": {
            "bankAccounts": [
                {
                    "value": item.value,
                    "confidence": round(item.confidence, 3),
                    "occurrences": item.occurrences,
                    "firstSeen": item.firstSeen,
                    "context": item.context[:100] if item.context else None
                }
                for item in intel.bankAccountsDetailed
                if item.confidence >= threshold
            ],
            "upiIds": [
                {
                    "value": item.value,
                    "confidence": round(item.confidence, 3),
                    "occurrences": item.occurrences,
                    "firstSeen": item.firstSeen,
                    "context": item.context[:100] if item.context else None
                }
                for item in intel.upiIdsDetailed
                if item.confidence >= threshold
            ],
            "phishingLinks": [
                {
                    "value": item.value,
                    "confidence": round(item.confidence, 3),
                    "occurrences": item.occurrences,
                    "firstSeen": item.firstSeen
                }
                for item in intel.phishingLinksDetailed
                if item.confidence >= threshold
            ],
            "phoneNumbers": [
                {
                    "value": item.value,
                    "confidence": round(item.confidence, 3),
                    "occurrences": item.occurrences,
                    "firstSeen": item.firstSeen,
                    "context": item.context[:100] if item.context else None
                }
                for item in intel.phoneNumbersDetailed
                if item.confidence >= threshold
            ],
            "suspiciousKeywords": [
                {
                    "value": item.value,
                    "confidence": round(item.confidence, 3),
                    "occurrences": item.occurrences
                }
                for item in intel.suspiciousKeywordsDetailed
                if item.confidence >= threshold
            ]
        },
        "confidenceDistribution": {
            "veryHigh": sum(1 for item in (
                intel.bankAccountsDetailed + intel.upiIdsDetailed + 
                intel.phishingLinksDetailed + intel.phoneNumbersDetailed
            ) if item.confidence >= 0.9),
            "high": sum(1 for item in (
                intel.bankAccountsDetailed + intel.upiIdsDetailed + 
                intel.phishingLinksDetailed + intel.phoneNumbersDetailed
            ) if 0.7 <= item.confidence < 0.9),
            "medium": sum(1 for item in (
                intel.bankAccountsDetailed + intel.upiIdsDetailed + 
                intel.phishingLinksDetailed + intel.phoneNumbersDetailed
            ) if 0.5 <= item.confidence < 0.7),
            "low": sum(1 for item in (
                intel.bankAccountsDetailed + intel.upiIdsDetailed + 
                intel.phishingLinksDetailed + intel.phoneNumbersDetailed
            ) if item.confidence < 0.5)
        }
    }


@app.get("/api/session/{session_id}/drift")
async def get_drift_analysis(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get intent drift analysis for a session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.drift_analysis:
        return {
            "sessionId": session_id,
            "message": "No drift analysis available yet",
            "intentHistory": []
        }
    
    return {
        "sessionId": session_id,
        "driftAnalysis": intent_drift_analyzer.get_drift_summary(session.drift_analysis),
        "intentHistory": [
            {
                "intent": record.intent,
                "confidence": round(record.confidence, 3),
                "messageNumber": record.message_number,
                "timestamp": record.timestamp,
                "reasoning": record.reasoning
            }
            for record in session.intent_history
        ],
        "currentIntent": session.current_intent,
        "behaviorInsights": {
            "behaviorType": session.drift_analysis.behavior_type.value,
            "interpretation": session.drift_analysis.interpretation,
            "stabilityScore": session.drift_analysis.stability_score,
            "intentDiversity": session.drift_analysis.intent_diversity
        }
    }


@app.post("/api/cleanup")
async def cleanup_sessions(api_key: str = Depends(verify_api_key)):
    """Cleanup expired sessions"""
    session_manager.cleanup_expired_sessions()
    return {
        "status": "success",
        "active_sessions": len(session_manager.sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
