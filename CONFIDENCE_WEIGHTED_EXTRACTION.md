# 🎯 Confidence-Weighted Intelligence Extraction

## ✅ Feature Status: 100% COMPLETE

### Overview

Enhanced intelligence extraction system that assigns confidence scores to each extracted item based on contextual analysis, pattern quality, and repetition tracking.

---

## 🚀 Key Features Implemented

### 1. **Contextual Confidence Scoring**

Each extracted item receives a confidence score (0.0 - 1.0) based on:

- **Urgency keywords** nearby (urgent, immediate, now) → +0.1 to +0.2
- **Sensitive keywords** (OTP, password, CVV) → +0.15 to +0.25
- **Type-specific context**:
  - Bank accounts with "transfer", "IFSC" → +0.2
  - UPI IDs with valid providers (paytm, phonepe) → +0.3
  - Phone numbers in Indian format → +0.2
  - HTTPS links with short URLs → +0.25

### 2. **Pattern Quality Assessment**

- **Bank Accounts**: Longer accounts (12+ digits) get higher confidence
- **UPI IDs**: Validated against known provider list (paytm, phonepe, gpay, etc.)
- **Phone Numbers**: Indian format validation (10 digits, starts with 6-9)
- **Links**: Short URLs (bit.ly, tinyurl) flagged as more suspicious

### 3. **Repetition-Based Confidence Boosting**

- Items mentioned multiple times get confidence boost (+0.05 per occurrence, max +0.2)
- Tracks `occurrences` count and `firstSeen` timestamp
- Scammers often repeat critical info → higher confidence

### 4. **GUVI Format Compatibility** ⚡

**Backward Compatible!** No breaking changes:

```python
# External API response (unchanged for GUVI)
{
  "bankAccounts": ["123456789012"],  # Simple list
  "upiIds": ["scammer@paytm"],
  ...
}

# Internal enhanced tracking (hidden from GUVI)
{
  "bankAccountsDetailed": [
    {
      "value": "123456789012",
      "confidence": 0.85,
      "occurrences": 2,
      "firstSeen": "2026-02-11T10:00:00",
      "context": "URGENT! Your account 123456..."
    }
  ],
  ...
}
```

### 5. **New Intelligence Analytics Endpoint**

```bash
GET /api/session/{session_id}/intelligence?threshold=0.7
```

Returns:

- Overall confidence score
- High confidence item count
- Detailed items with confidence, occurrences, timestamps
- Confidence distribution (very high / high / medium / low)

---

## 📊 Data Model

### IntelligenceItem

```python
{
  "value": str,              # Extracted value
  "confidence": float,       # 0.0 - 1.0 confidence score
  "context": str,            # First 100 chars of source message
  "firstSeen": str,          # ISO timestamp
  "occurrences": int         # How many times seen
}
```

### Enhanced ExtractedIntelligence

```python
{
  # GUVI-compatible (unchanged)
  "bankAccounts": List[str],
  "upiIds": List[str],
  "phishingLinks": List[str],
  "phoneNumbers": List[str],
  "suspiciousKeywords": List[str],

  # Enhanced internal tracking (excluded from GUVI response)
  "bankAccountsDetailed": List[IntelligenceItem],
  "upiIdsDetailed": List[IntelligenceItem],
  "phishingLinksDetailed": List[IntelligenceItem],
  "phoneNumbersDetailed": List[IntelligenceItem],
  "suspiciousKeywordsDetailed": List[IntelligenceItem],

  # Analytics
  "overallConfidence": float,      # Average confidence
  "highConfidenceCount": int       # Items with confidence > 0.7
}
```

---

## 🔥 Confidence Calculation Formula

### Base Score

```
base_confidence = 0.5
```

### Context Boosters

```python
urgency_boost = min(urgency_keywords_count * 0.1, 0.2)
sensitive_boost = min(sensitive_keywords_count * 0.15, 0.25)
type_specific_boost = 0.0 to 0.3  # Varies by item type
```

### Repetition Boost

```python
repetition_boost = min(occurrences * 0.05, 0.2)
```

### Final Confidence

```python
confidence = min(base_confidence + context_boost + repetition_boost, 1.0)
```

---

## 🧪 Testing

### Run Test Suite

```bash
# Start server
python main.py

# In another terminal, run tests
python test_confidence_extraction.py
```

### Test Scenarios Covered

1. **Bank Fraud** - Account + urgency + OTP (High confidence ~0.85)
2. **UPI Fraud** - Valid UPI providers + payment context (High confidence ~0.90)
3. **Phishing Links** - Short URLs + click urgency (High confidence ~0.80)
4. **Repetition Boost** - Phone number repeated 3x (Confidence increases each time)
5. **Mixed Context** - Multiple items with varying confidence levels

---

## 📈 Confidence Distribution Ranges

| Range       | Label     | Meaning                         |
| ----------- | --------- | ------------------------------- |
| 0.90 - 1.00 | Very High | Highly reliable, strong context |
| 0.70 - 0.89 | High      | Reliable, good context          |
| 0.50 - 0.69 | Medium    | Possible, needs verification    |
| 0.00 - 0.49 | Low       | Uncertain, weak indicators      |

---

## 🎯 Real-World Example

### Input Message

```
"URGENT! Your SBI bank account 123456789012 will be blocked.
Share OTP to verify immediately."
```

### Extracted Intelligence

```json
{
  "bankAccounts": ["123456789012"], // GUVI format

  "bankAccountsDetailed": [
    // Internal tracking
    {
      "value": "123456789012",
      "confidence": 0.85,
      "context": "URGENT! Your SBI bank account 123456789012...",
      "occurrences": 1,
      "firstSeen": "2026-02-11T10:00:00Z"
    }
  ],

  "suspiciousKeywordsDetailed": [
    { "value": "urgent", "confidence": 0.8, "occurrences": 1 },
    { "value": "blocked", "confidence": 0.75, "occurrences": 1 },
    { "value": "otp", "confidence": 0.85, "occurrences": 1 },
    { "value": "verify", "confidence": 0.7, "occurrences": 1 }
  ],

  "overallConfidence": 0.79,
  "highConfidenceCount": 4
}
```

---

## 💡 Benefits for Grand Finale

### 1. **Advanced Analytics**

- Judges can see not just "what" was extracted, but "how confident" the system is
- Demonstrates sophisticated AI decision-making

### 2. **Intelligence Quality Metrics**

- Overall confidence score shows conversation effectiveness
- High confidence count indicates successful information extraction

### 3. **Temporal Tracking**

- `firstSeen` timestamps show when intelligence was first discovered
- `occurrences` show scammer persistence on specific details

### 4. **Flexible Filtering**

- Can query for only high-confidence items (threshold parameter)
- Reduces false positives in final intelligence reports

### 5. **Production Ready**

- Zero breaking changes to existing GUVI integration
- Backward compatible API responses
- Enhanced internal analytics

---

## 🔧 Code Architecture

### Modified Files

1. **schemas.py** - Added `IntelligenceItem` and enhanced `ExtractedIntelligence`
2. **intelligence_extractor.py** - Complete rewrite with confidence scoring
3. **main.py** - Added confidence logging and new analytics endpoint

### Key Methods

- `_calculate_context_confidence()` - Analyzes message context
- `_track_and_update_item()` - Handles repetition tracking
- `_merge_detailed_items()` - Merges intelligence with confidence preservation
- `sync_from_detailed()` - Maintains GUVI compatibility

---

## 📊 Logging Output Example

```
📊 Intelligence Confidence Metrics:
  - Overall Confidence: 0.79
  - High Confidence Items: 4
  - Bank Accounts: 1 items
    • 123456789012 (confidence: 0.85, seen: 1x)
  - UPI IDs: 0 items
  - Phishing Links: 0 items
```

---

## ✅ Completion Checklist

- [x] Contextual confidence scoring
- [x] Pattern quality assessment
- [x] Repetition-based boosting
- [x] Temporal tracking (firstSeen, occurrences)
- [x] GUVI format compatibility
- [x] Detailed intelligence endpoint
- [x] Confidence distribution analytics
- [x] Comprehensive logging
- [x] Test suite with 5 scenarios
- [x] Documentation

---

## 🎉 Status: FEATURE 100% COMPLETE

Ready for grand finale demonstration! 🚀
