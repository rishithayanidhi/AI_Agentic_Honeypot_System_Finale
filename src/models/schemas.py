from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


class Message(BaseModel):
    """Represents a single message in the conversation"""
    sender: Optional[str] = "scammer"  # "scammer" or "user"
    text: Optional[str] = ""  # Make optional for flexible parsing
    timestamp: Optional[Union[str, int]] = None  # Accept both string and integer timestamps
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def convert_timestamp(cls, v):
        """Convert integer timestamp to ISO string format"""
        if v is None:
            return datetime.now().isoformat()
        if isinstance(v, int):
            # Convert milliseconds timestamp to ISO format
            return datetime.fromtimestamp(v / 1000).isoformat()
        return v


class Metadata(BaseModel):
    """Additional metadata about the conversation"""
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"


class EmptyRequest(BaseModel):
    """Accepts completely empty body for GUVI endpoint tester"""
    pass


class SimpleIncomingRequest(BaseModel):
    """Simplified incoming API request structure (for testing)"""
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    message: Optional[Union[str, Dict[str, Any]]] = Field(default=None)  # Accept both string and dict
    conversationHistory: Optional[List[Any]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True  # Allow both session_id and sessionId


class IncomingRequest(BaseModel):
    """Full incoming API request structure"""
    sessionId: Optional[str] = None
    message: Optional[Union[Message, str, Dict[str, Any]]] = None  # Accept Message object, string, or dict
    conversationHistory: Optional[List[Any]] = Field(default_factory=list)  # Accept any format
    metadata: Optional[Union[Metadata, Dict[str, Any]]] = None  # Accept Metadata or dict
    
    class Config:
        populate_by_name = True


class IntelligenceItem(BaseModel):
    """Individual intelligence item with confidence score"""
    value: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    context: Optional[str] = None  # Context where found
    firstSeen: Optional[str] = None  # Timestamp first extracted
    occurrences: int = 1  # How many times seen


class ExtractedIntelligence(BaseModel):
    """Intelligence extracted from the scammer"""
    # GUVI-compatible fields (backward compatible)
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)
    
    # Enhanced confidence-weighted fields (internal use)
    bankAccountsDetailed: List[IntelligenceItem] = Field(default_factory=list, exclude=True)
    upiIdsDetailed: List[IntelligenceItem] = Field(default_factory=list, exclude=True)
    phishingLinksDetailed: List[IntelligenceItem] = Field(default_factory=list, exclude=True)
    phoneNumbersDetailed: List[IntelligenceItem] = Field(default_factory=list, exclude=True)
    suspiciousKeywordsDetailed: List[IntelligenceItem] = Field(default_factory=list, exclude=True)
    
    # Overall confidence metrics
    overallConfidence: float = Field(default=0.0, ge=0.0, le=1.0, exclude=True)
    highConfidenceCount: int = Field(default=0, exclude=True)  # Items with confidence > 0.7
    
    def sync_from_detailed(self):
        """Sync simple lists from detailed items for GUVI compatibility"""
        self.bankAccounts = [item.value for item in self.bankAccountsDetailed]
        self.upiIds = [item.value for item in self.upiIdsDetailed]
        self.phishingLinks = [item.value for item in self.phishingLinksDetailed]
        self.phoneNumbers = [item.value for item in self.phoneNumbersDetailed]
        self.suspiciousKeywords = [item.value for item in self.suspiciousKeywordsDetailed]
        
        # Calculate overall confidence
        all_items = (
            self.bankAccountsDetailed + self.upiIdsDetailed + 
            self.phishingLinksDetailed + self.phoneNumbersDetailed +
            self.suspiciousKeywordsDetailed
        )
        if all_items:
            self.overallConfidence = sum(item.confidence for item in all_items) / len(all_items)
            self.highConfidenceCount = sum(1 for item in all_items if item.confidence > 0.7)
        else:
            self.overallConfidence = 0.0
            self.highConfidenceCount = 0
    
    def get_high_confidence_items(self, threshold: float = 0.7) -> Dict[str, List[IntelligenceItem]]:
        """Get only high-confidence intelligence items"""
        return {
            "bankAccounts": [item for item in self.bankAccountsDetailed if item.confidence >= threshold],
            "upiIds": [item for item in self.upiIdsDetailed if item.confidence >= threshold],
            "phishingLinks": [item for item in self.phishingLinksDetailed if item.confidence >= threshold],
            "phoneNumbers": [item for item in self.phoneNumbersDetailed if item.confidence >= threshold],
            "suspiciousKeywords": [item for item in self.suspiciousKeywordsDetailed if item.confidence >= threshold]
        }


class EngagementMetrics(BaseModel):
    """Metrics about the engagement"""
    engagementDurationSeconds: int = 0
    totalMessagesExchanged: int = 0


class APIResponse(BaseModel):
    """API response structure"""
    status: str = "success"
    scamDetected: bool
    agentResponse: Optional[str] = None  # The response to send back to scammer
    engagementMetrics: Optional[EngagementMetrics] = None
    extractedIntelligence: Optional[ExtractedIntelligence] = None
    agentNotes: Optional[str] = None
    sessionComplete: bool = False  # Whether the conversation has ended


class GUVICallbackPayload(BaseModel):
    """Payload to send to GUVI evaluation endpoint"""
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: Dict[str, Any]
    agentNotes: str
