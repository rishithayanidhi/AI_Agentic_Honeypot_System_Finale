from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from src.models.schemas import Message, ExtractedIntelligence, IntentRecord, IntentDriftAnalysis


@dataclass
class SessionData:
    """Stores session state and conversation data"""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    scam_detected: bool = False
    intelligence: ExtractedIntelligence = field(default_factory=ExtractedIntelligence)
    agent_notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    engagement_active: bool = False
    persona: str = "cautious_user"  # The persona the agent is currently using
    
    # Intent Drift Tracking fields (new)
    intent_history: List[IntentRecord] = field(default_factory=list)
    current_intent: Optional[str] = None
    drift_analysis: Optional[IntentDriftAnalysis] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "session_id": self.session_id,
            "messages": [m.model_dump() for m in self.messages],
            "scam_detected": self.scam_detected,
            "intelligence": self.intelligence.model_dump(),
            "agent_notes": self.agent_notes,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "engagement_active": self.engagement_active,
            "persona": self.persona,
            "intent_history": [ir.model_dump() for ir in self.intent_history],
            "current_intent": self.current_intent,
            "drift_analysis": self.drift_analysis.model_dump() if self.drift_analysis else None
        }
