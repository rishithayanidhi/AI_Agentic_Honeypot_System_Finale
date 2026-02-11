"""
Intent Drift Analyzer - Tracks and analyzes scammer intent changes over conversation
"""

from typing import List, Optional, Dict, Tuple
from datetime import datetime
import logging

from src.models.schemas import (
    IntentRecord, DriftEvent, IntentDriftAnalysis, 
    DriftMagnitude, ScammerBehaviorType
)

logger = logging.getLogger(__name__)


class IntentDriftAnalyzer:
    """Analyzes intent drift patterns in scammer conversations"""
    
    # Intent similarity matrix - how different are intent pairs (0.0 = same, 1.0 = completely different)
    INTENT_SIMILARITY_MATRIX = {
        ('bank_fraud', 'bank_fraud'): 0.0,
        ('bank_fraud', 'upi_fraud'): 0.3,  # Both financial fraud
        ('bank_fraud', 'phishing'): 0.6,   # Different approach
        ('bank_fraud', 'fake_offer'): 0.8,  # Very different
        ('bank_fraud', 'other'): 0.7,
        
        ('upi_fraud', 'upi_fraud'): 0.0,
        ('upi_fraud', 'phishing'): 0.5,
        ('upi_fraud', 'fake_offer'): 0.8,
        ('upi_fraud', 'other'): 0.7,
        
        ('phishing', 'phishing'): 0.0,
        ('phishing', 'fake_offer'): 0.6,
        ('phishing', 'other'): 0.6,
        
        ('fake_offer', 'fake_offer'): 0.0,
        ('fake_offer', 'other'): 0.5,
        
        ('other', 'other'): 0.0,
    }
    
    def __init__(self):
        pass
    
    def calculate_intent_similarity(self, intent1: str, intent2: str) -> float:
        """Calculate similarity/distance between two intents (0.0 = same, 1.0 = very different)"""
        if intent1 == intent2:
            return 0.0
        
        # Normalize intent names
        intent1 = intent1.lower()
        intent2 = intent2.lower()
        
        # Check matrix (order doesn't matter)
        key1 = (intent1, intent2)
        key2 = (intent2, intent1)
        
        if key1 in self.INTENT_SIMILARITY_MATRIX:
            return self.INTENT_SIMILARITY_MATRIX[key1]
        elif key2 in self.INTENT_SIMILARITY_MATRIX:
            return self.INTENT_SIMILARITY_MATRIX[key2]
        else:
            # Unknown intents - assume moderate difference
            return 0.5
    
    def classify_drift_magnitude(self, similarity_score: float) -> DriftMagnitude:
        """Classify drift magnitude based on similarity score"""
        if similarity_score < 0.1:
            return DriftMagnitude.NONE
        elif similarity_score < 0.4:
            return DriftMagnitude.LOW
        elif similarity_score < 0.7:
            return DriftMagnitude.MEDIUM
        else:
            return DriftMagnitude.HIGH
    
    def detect_drift(
        self, 
        current_intent: str, 
        current_confidence: float,
        previous_intent: Optional[str],
        message_number: int
    ) -> Optional[DriftEvent]:
        """Detect if intent drift occurred"""
        if not previous_intent or previous_intent == current_intent:
            return None
        
        # Calculate drift
        similarity = self.calculate_intent_similarity(previous_intent, current_intent)
        magnitude = self.classify_drift_magnitude(similarity)
        
        drift_event = DriftEvent(
            from_intent=previous_intent,
            to_intent=current_intent,
            timestamp=datetime.now().isoformat(),
            message_number=message_number,
            drift_magnitude=magnitude.value,
            drift_score=similarity
        )
        
        logger.info(f"⚠️ DRIFT DETECTED: {previous_intent} → {current_intent} (magnitude: {magnitude.value}, score: {similarity:.2f})")
        
        return drift_event
    
    def track_intent(
        self,
        intent: str,
        confidence: float,
        message_number: int,
        reasoning: Optional[str] = None
    ) -> IntentRecord:
        """Create intent record for tracking"""
        return IntentRecord(
            intent=intent,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            message_number=message_number,
            reasoning=reasoning
        )
    
    def analyze_drift_pattern(self, intent_history: List[IntentRecord]) -> IntentDriftAnalysis:
        """Perform complete drift analysis on conversation"""
        
        if not intent_history:
            return IntentDriftAnalysis(
                behavior_type=ScammerBehaviorType.UNKNOWN,
                interpretation="No intent data available"
            )
        
        # Calculate drift events
        drift_events = []
        for i in range(1, len(intent_history)):
            prev_intent = intent_history[i-1].intent
            curr_intent = intent_history[i].intent
            
            if prev_intent != curr_intent:
                similarity = self.calculate_intent_similarity(prev_intent, curr_intent)
                magnitude = self.classify_drift_magnitude(similarity)
                
                drift_events.append(DriftEvent(
                    from_intent=prev_intent,
                    to_intent=curr_intent,
                    timestamp=intent_history[i].timestamp,
                    message_number=intent_history[i].message_number,
                    drift_magnitude=magnitude.value,
                    drift_score=similarity
                ))
        
        # Calculate metrics
        total_drifts = len(drift_events)
        total_messages = len(intent_history)
        drift_rate = total_drifts / total_messages if total_messages > 0 else 0.0
        
        # Count unique intents
        unique_intents = list(set(record.intent for record in intent_history))
        intent_diversity = len(unique_intents)
        
        # Find primary intent (most frequent)
        intent_counts = {}
        for record in intent_history:
            intent_counts[record.intent] = intent_counts.get(record.intent, 0) + 1
        primary_intent = max(intent_counts, key=intent_counts.get) if intent_counts else None
        
        # Stability score (inverse of drift rate)
        stability_score = 1.0 - drift_rate
        
        # Classify behavior type
        behavior_type = self._classify_behavior(
            drift_rate=drift_rate,
            intent_diversity=intent_diversity,
            total_messages=total_messages,
            drift_events=drift_events
        )
        
        # Generate interpretation
        interpretation = self._generate_interpretation(
            behavior_type=behavior_type,
            drift_rate=drift_rate,
            intent_diversity=intent_diversity,
            primary_intent=primary_intent,
            total_drifts=total_drifts
        )
        
        analysis = IntentDriftAnalysis(
            total_drifts=total_drifts,
            drift_rate=round(drift_rate, 3),
            intent_diversity=intent_diversity,
            stability_score=round(stability_score, 3),
            primary_intent=primary_intent,
            drift_events=drift_events,
            intent_timeline=intent_history,
            behavior_type=behavior_type,
            interpretation=interpretation
        )
        
        logger.info(f"📊 Drift Analysis Complete: {total_drifts} drifts, {drift_rate:.2%} rate, behavior: {behavior_type.value}")
        
        return analysis
    
    def _classify_behavior(
        self,
        drift_rate: float,
        intent_diversity: int,
        total_messages: int,
        drift_events: List[DriftEvent]
    ) -> ScammerBehaviorType:
        """Classify scammer behavior based on drift patterns"""
        
        # Professional: Low drift, focused on one strategy
        if drift_rate < 0.2 and intent_diversity <= 2:
            return ScammerBehaviorType.PROFESSIONAL_FOCUSED
        
        # Amateur/Desperate: High drift, trying many things
        if drift_rate > 0.4 or intent_diversity >= 4:
            return ScammerBehaviorType.AMATEUR_DESPERATE
        
        # Adaptive/Testing: Moderate drift, strategic changes
        if 0.2 <= drift_rate <= 0.4 and intent_diversity == 3:
            # Check if drifts are strategic (mostly medium/high magnitude)
            high_magnitude_drifts = sum(
                1 for event in drift_events 
                if event.drift_magnitude in [DriftMagnitude.MEDIUM.value, DriftMagnitude.HIGH.value]
            )
            if high_magnitude_drifts >= len(drift_events) * 0.6:
                return ScammerBehaviorType.ADAPTIVE_TESTING
        
        return ScammerBehaviorType.UNKNOWN
    
    def _generate_interpretation(
        self,
        behavior_type: ScammerBehaviorType,
        drift_rate: float,
        intent_diversity: int,
        primary_intent: Optional[str],
        total_drifts: int
    ) -> str:
        """Generate human-readable interpretation of drift pattern"""
        
        if behavior_type == ScammerBehaviorType.PROFESSIONAL_FOCUSED:
            return (
                f"Professional scammer behavior detected. Focused on {primary_intent} strategy "
                f"with minimal drift ({drift_rate:.1%}). Likely experienced and confident."
            )
        
        elif behavior_type == ScammerBehaviorType.AMATEUR_DESPERATE:
            return (
                f"Amateur/desperate scammer detected. High drift rate ({drift_rate:.1%}) "
                f"with {intent_diversity} different tactics tried. Likely inexperienced or frustrated."
            )
        
        elif behavior_type == ScammerBehaviorType.ADAPTIVE_TESTING:
            return (
                f"Adaptive scammer behavior. {total_drifts} strategic shifts detected. "
                f"Testing different approaches to find victim's vulnerability."
            )
        
        else:
            return (
                f"Drift pattern analysis: {total_drifts} intent changes across {intent_diversity} "
                f"different scam types. Primary tactic: {primary_intent or 'unknown'}."
            )
    
    def get_drift_summary(self, analysis: IntentDriftAnalysis) -> Dict:
        """Get summary dictionary for API responses"""
        return {
            "totalDrifts": analysis.total_drifts,
            "driftRate": analysis.drift_rate,
            "intentDiversity": analysis.intent_diversity,
            "stabilityScore": analysis.stability_score,
            "primaryIntent": analysis.primary_intent,
            "behaviorType": analysis.behavior_type.value,
            "interpretation": analysis.interpretation,
            "driftEvents": [
                {
                    "fromIntent": event.from_intent,
                    "toIntent": event.to_intent,
                    "magnitude": event.drift_magnitude,
                    "messageNumber": event.message_number,
                    "timestamp": event.timestamp
                }
                for event in analysis.drift_events
            ]
        }


# Global intent drift analyzer instance
intent_drift_analyzer = IntentDriftAnalyzer()
