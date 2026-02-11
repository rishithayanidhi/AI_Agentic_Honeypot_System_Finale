import re
from typing import List, Set, Dict, Tuple
from datetime import datetime
from src.models.schemas import ExtractedIntelligence, IntelligenceItem, Message


class IntelligenceExtractor:
    """Extracts structured intelligence with confidence weighting from conversations"""
    
    # Regex patterns for extraction
    BANK_ACCOUNT_PATTERN = r'\b\d{9,18}\b'
    UPI_PATTERN = r'\b[\w\.-]+@[\w\.-]+\b'
    PHONE_PATTERN = r'\+?\d{10,15}'
    URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    # UPI provider patterns for validation
    UPI_PROVIDERS = ['paytm', 'phonepe', 'gpay', 'okaxis', 'ybl', 'axl', 'ibl', 'okhdfcbank', 'oksbi', 'fbl', 'icici']
    
    # Common scam keywords
    SCAM_KEYWORDS = [
        'urgent', 'verify', 'suspend', 'block', 'immediate', 'account',
        'security', 'update', 'confirm', 'click', 'link', 'prize',
        'winner', 'congratulations', 'claim', 'expires', 'limited',
        'act now', 'verify now', 'update now', 'confirm now', 'kyc',
        'otp', 'password', 'pin', 'cvv', 'card number', 'expiry'
    ]
    
    # High-urgency keywords that boost confidence
    HIGH_URGENCY_KEYWORDS = ['urgent', 'immediate', 'now', 'expires', 'block', 'suspend']
    
    # Sensitive data keywords that boost confidence
    SENSITIVE_KEYWORDS = ['otp', 'password', 'pin', 'cvv', 'account number']
    
    def __init__(self):
        self.extracted_data = ExtractedIntelligence()
        self.item_tracking: Dict[str, Dict] = {}  # Track items across messages for confidence boosting
    
    def _calculate_context_confidence(self, message: str, extracted_value: str, value_type: str) -> Tuple[float, str]:
        """Calculate confidence score based on context around extracted value"""
        message_lower = message.lower()
        context_snippet = message[:100]  # First 100 chars as context
        base_confidence = 0.5
        confidence_boost = 0.0
        
        # Boost confidence if urgency keywords present
        urgency_count = sum(1 for kw in self.HIGH_URGENCY_KEYWORDS if kw in message_lower)
        confidence_boost += min(urgency_count * 0.1, 0.2)
        
        # Boost confidence if sensitive keywords present
        sensitive_count = sum(1 for kw in self.SENSITIVE_KEYWORDS if kw in message_lower)
        confidence_boost += min(sensitive_count * 0.15, 0.25)
        
        # Type-specific confidence adjustments
        if value_type == 'bank_account':
            # Longer account numbers are more likely valid
            if len(extracted_value) >= 12:
                confidence_boost += 0.15
            # Check if mentioned with bank-related terms
            if any(term in message_lower for term in ['account', 'bank', 'transfer', 'ifsc']):
                confidence_boost += 0.2
        
        elif value_type == 'upi_id':
            # Check if valid UPI provider
            has_valid_provider = any(provider in extracted_value.lower() for provider in self.UPI_PROVIDERS)
            if has_valid_provider:
                confidence_boost += 0.3
            # Check for payment context
            if any(term in message_lower for term in ['upi', 'payment', 'pay', 'send', 'transfer']):
                confidence_boost += 0.15
        
        elif value_type == 'phone_number':
            # Indian phone numbers (10 digits starting with 6-9)
            if re.match(r'^[6-9]\d{9}$', extracted_value.replace('+91', '').replace('91', '')):
                confidence_boost += 0.2
            # Check for contact context
            if any(term in message_lower for term in ['call', 'contact', 'whatsapp', 'number']):
                confidence_boost += 0.1
        
        elif value_type == 'phishing_link':
            # HTTPS is more suspicious (legitimate appearance)
            if extracted_value.startswith('https'):
                confidence_boost += 0.15
            # Short domains or suspicious TLDs
            if any(indicator in extracted_value.lower() for indicator in ['.tk', '.ml', 'bit.ly', 'tinyurl', 'short']):
                confidence_boost += 0.25
            # Click urgency
            if any(term in message_lower for term in ['click', 'verify', 'confirm', 'update']):
                confidence_boost += 0.15
        
        elif value_type == 'keyword':
            # Keywords in ALL CAPS get higher confidence
            if extracted_value.upper() in message:
                confidence_boost += 0.15
            # Repeated keywords
            count = message_lower.count(extracted_value.lower())
            if count > 1:
                confidence_boost += min(count * 0.05, 0.15)
        
        final_confidence = min(base_confidence + confidence_boost, 1.0)
        return final_confidence, context_snippet
    
    def _track_and_update_item(self, value: str, value_type: str, confidence: float, context: str) -> IntelligenceItem:
        """Track item across messages and boost confidence for repeated occurrences"""
        key = f"{value_type}:{value}"
        
        if key in self.item_tracking:
            # Item seen before - boost confidence
            tracked = self.item_tracking[key]
            tracked['occurrences'] += 1
            # Confidence boost for repetition (max +0.2)
            repetition_boost = min(tracked['occurrences'] * 0.05, 0.2)
            boosted_confidence = min(tracked['base_confidence'] + repetition_boost, 1.0)
            
            return IntelligenceItem(
                value=value,
                confidence=boosted_confidence,
                context=context,
                firstSeen=tracked['firstSeen'],
                occurrences=tracked['occurrences']
            )
        else:
            # First time seeing this item
            self.item_tracking[key] = {
                'base_confidence': confidence,
                'occurrences': 1,
                'firstSeen': datetime.now().isoformat()
            }
            
            return IntelligenceItem(
                value=value,
                confidence=confidence,
                context=context,
                firstSeen=datetime.now().isoformat(),
                occurrences=1
            )
    
    def extract_from_message(self, message: str) -> ExtractedIntelligence:
        """Extract intelligence with confidence weighting from a single message"""
        intel = ExtractedIntelligence()
        
        # Extract bank accounts with confidence
        bank_accounts = re.findall(self.BANK_ACCOUNT_PATTERN, message)
        for account in set(bank_accounts):
            confidence, context = self._calculate_context_confidence(message, account, 'bank_account')
            item = self._track_and_update_item(account, 'bank_account', confidence, context)
            intel.bankAccountsDetailed.append(item)
        
        # Extract UPI IDs with confidence
        upi_ids = re.findall(self.UPI_PATTERN, message)
        # Filter out email-like patterns that aren't UPI
        valid_upi_ids = [uid for uid in upi_ids if any(provider in uid.lower() for provider in self.UPI_PROVIDERS)]
        for upi_id in set(valid_upi_ids):
            confidence, context = self._calculate_context_confidence(message, upi_id, 'upi_id')
            item = self._track_and_update_item(upi_id, 'upi_id', confidence, context)
            intel.upiIdsDetailed.append(item)
        
        # Extract phone numbers with confidence
        phone_numbers = re.findall(self.PHONE_PATTERN, message)
        for phone in set(phone_numbers):
            confidence, context = self._calculate_context_confidence(message, phone, 'phone_number')
            item = self._track_and_update_item(phone, 'phone_number', confidence, context)
            intel.phoneNumbersDetailed.append(item)
        
        # Extract URLs with confidence
        urls = re.findall(self.URL_PATTERN, message)
        for url in set(urls):
            confidence, context = self._calculate_context_confidence(message, url, 'phishing_link')
            item = self._track_and_update_item(url, 'phishing_link', confidence, context)
            intel.phishingLinksDetailed.append(item)
        
        # Extract suspicious keywords with confidence
        message_lower = message.lower()
        found_keywords = [kw for kw in self.SCAM_KEYWORDS if kw in message_lower]
        for keyword in set(found_keywords):
            confidence, context = self._calculate_context_confidence(message, keyword, 'keyword')
            item = self._track_and_update_item(keyword, 'keyword', confidence, context)
            intel.suspiciousKeywordsDetailed.append(item)
        
        # Sync detailed items to simple lists for GUVI compatibility
        intel.sync_from_detailed()
        
        return intel
    
    def extract_from_conversation(self, messages: List[Message]) -> ExtractedIntelligence:
        """Extract intelligence from entire conversation with confidence tracking"""
        all_intel = ExtractedIntelligence()
        
        # Reset tracking for new extraction
        self.item_tracking.clear()
        
        for msg in messages:
            if msg.sender == "scammer":
                intel = self.extract_from_message(msg.text)
                
                # Merge detailed items (tracking handles deduplication and confidence boosting)
                all_intel.bankAccountsDetailed.extend(intel.bankAccountsDetailed)
                all_intel.upiIdsDetailed.extend(intel.upiIdsDetailed)
                all_intel.phoneNumbersDetailed.extend(intel.phoneNumbersDetailed)
                all_intel.phishingLinksDetailed.extend(intel.phishingLinksDetailed)
                all_intel.suspiciousKeywordsDetailed.extend(intel.suspiciousKeywordsDetailed)
        
        # Deduplicate detailed items by value (keep highest confidence)
        all_intel.bankAccountsDetailed = self._deduplicate_items(all_intel.bankAccountsDetailed)
        all_intel.upiIdsDetailed = self._deduplicate_items(all_intel.upiIdsDetailed)
        all_intel.phoneNumbersDetailed = self._deduplicate_items(all_intel.phoneNumbersDetailed)
        all_intel.phishingLinksDetailed = self._deduplicate_items(all_intel.phishingLinksDetailed)
        all_intel.suspiciousKeywordsDetailed = self._deduplicate_items(all_intel.suspiciousKeywordsDetailed)
        
        # Sync to simple lists for GUVI compatibility
        all_intel.sync_from_detailed()
        
        return all_intel
    
    def _deduplicate_items(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """Deduplicate items, keeping the one with highest confidence"""
        if not items:
            return []
        
        # Group by value
        grouped: Dict[str, IntelligenceItem] = {}
        for item in items:
            if item.value not in grouped or item.confidence > grouped[item.value].confidence:
                grouped[item.value] = item
        
        # Sort by confidence (highest first)
        return sorted(grouped.values(), key=lambda x: x.confidence, reverse=True)
    
    def merge_intelligence(self, existing: ExtractedIntelligence, new: ExtractedIntelligence) -> ExtractedIntelligence:
        """Merge two intelligence objects with confidence preservation"""
        merged = ExtractedIntelligence()
        
        # Merge detailed items
        merged.bankAccountsDetailed = self._merge_detailed_items(
            existing.bankAccountsDetailed, new.bankAccountsDetailed
        )
        merged.upiIdsDetailed = self._merge_detailed_items(
            existing.upiIdsDetailed, new.upiIdsDetailed
        )
        merged.phoneNumbersDetailed = self._merge_detailed_items(
            existing.phoneNumbersDetailed, new.phoneNumbersDetailed
        )
        merged.phishingLinksDetailed = self._merge_detailed_items(
            existing.phishingLinksDetailed, new.phishingLinksDetailed
        )
        merged.suspiciousKeywordsDetailed = self._merge_detailed_items(
            existing.suspiciousKeywordsDetailed, new.suspiciousKeywordsDetailed
        )
        
        # Sync to simple lists for GUVI compatibility
        merged.sync_from_detailed()
        
        return merged
    
    def _merge_detailed_items(self, existing: List[IntelligenceItem], new: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """Merge two lists of intelligence items, updating confidence for duplicates"""
        # Create lookup by value
        merged_dict: Dict[str, IntelligenceItem] = {}
        
        # Add existing items
        for item in existing:
            merged_dict[item.value] = item
        
        # Merge new items
        for item in new:
            if item.value in merged_dict:
                # Item exists - combine occurrences and take max confidence
                existing_item = merged_dict[item.value]
                merged_dict[item.value] = IntelligenceItem(
                    value=item.value,
                    confidence=max(existing_item.confidence, item.confidence),
                    context=existing_item.context,  # Keep original context
                    firstSeen=existing_item.firstSeen,  # Keep first seen
                    occurrences=existing_item.occurrences + item.occurrences
                )
            else:
                # New item
                merged_dict[item.value] = item
        
        # Return sorted by confidence
        return sorted(merged_dict.values(), key=lambda x: x.confidence, reverse=True)
