import requests
from typing import Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class GUVICallback:
    """Handles callbacks to GUVI evaluation endpoint"""
    
    def __init__(self):
        self.callback_url = settings.GUVI_CALLBACK_URL
    
    def send_final_result(
        self,
        session_id: str,
        scam_detected: bool,
        total_messages: int,
        extracted_intelligence: Dict[str, Any],
        agent_notes: str
    ) -> bool:
        """
        Send final results to GUVI evaluation endpoint
        
        Returns: True if successful, False otherwise
        """
        
        payload = {
            "sessionId": session_id,
            "scamDetected": scam_detected,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": extracted_intelligence,
            "agentNotes": agent_notes
        }
        
        try:
            logger.info(f"Sending final result to GUVI for session {session_id}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(
                self.callback_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent results for session {session_id}")
                return True
            else:
                logger.error(f"GUVI callback failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"GUVI callback timeout for session {session_id}")
            return False
        except Exception as e:
            logger.error(f"Error sending GUVI callback: {e}")
            return False
    
    def format_intelligence_for_callback(self, intelligence: Any) -> Dict[str, Any]:
        """Format extracted intelligence for GUVI callback"""
        if hasattr(intelligence, 'model_dump'):
            return intelligence.model_dump()
        elif hasattr(intelligence, 'dict'):
            return intelligence.dict()
        else:
            return {
                "bankAccounts": intelligence.bankAccounts if hasattr(intelligence, 'bankAccounts') else [],
                "upiIds": intelligence.upiIds if hasattr(intelligence, 'upiIds') else [],
                "phishingLinks": intelligence.phishingLinks if hasattr(intelligence, 'phishingLinks') else [],
                "phoneNumbers": intelligence.phoneNumbers if hasattr(intelligence, 'phoneNumbers') else [],
                "suspiciousKeywords": intelligence.suspiciousKeywords if hasattr(intelligence, 'suspiciousKeywords') else []
            }


# Global callback handler
guvi_callback = GUVICallback()
