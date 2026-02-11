# AI Agentic Honeypot System

An AI-powered honeypot system that detects scam messages, autonomously engages scammers in multi-turn conversations, and extracts actionable intelligence.

## 🎯 Features

- **Scam Detection**: AI-powered detection of various scam types (bank fraud, UPI fraud, phishing, fake offers)
- **Autonomous AI Agent**: Multi-turn conversation handler with believable human personas
- **Intelligence Extraction**: Automatically extracts bank accounts, UPI IDs, phishing links, phone numbers, and suspicious keywords
- **Session Management**: Tracks conversations across multiple messages
- **REST API**: Secure REST API with API key authentication
- **GUVI Integration**: Automatic callback to GUVI evaluation endpoint
- **Multiple Personas**: Agent can adopt different personas (cautious user, eager victim, confused elderly, busy professional)

## 📋 Requirements

- Python 3.9+
- OpenAI API key OR Anthropic API key
- Internet connection

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the project directory
cd "AI Scammer Detection"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
# API Configuration
API_KEY=your-secret-api-key-here
PORT=8000
HOST=0.0.0.0

# LLM Provider (openai or anthropic)
LLM_PROVIDER=openai

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Configuration (if using Anthropic)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# GUVI Callback
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult

# Session Configuration
SESSION_TIMEOUT_MINUTES=30
MAX_MESSAGES_PER_SESSION=50
```

### 3. Run the Server

```bash
# Make sure virtual environment is activated
python main.py
```

The server will start at `http://localhost:8000`

## 📡 API Usage

### Authentication

All API requests require an API key in the header:

```
x-api-key: your-secret-api-key-here
Content-Type: application/json
```

### Endpoints

#### 1. Health Check

```bash
GET /health
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T10:00:00",
  "active_sessions": 5,
  "llm_provider": "openai"
}
```

#### 2. Send Message (Main Endpoint)

```bash
POST /api/message
```

**Request Body** (First Message):

```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today. Verify immediately.",
    "timestamp": "2026-01-26T10:15:30Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Request Body** (Follow-up Message):

```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Share your UPI ID to avoid suspension.",
    "timestamp": "2026-01-26T10:17:10Z"
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Your bank account will be blocked today. Verify immediately.",
      "timestamp": "2026-01-26T10:15:30Z"
    },
    {
      "sender": "user",
      "text": "Why will my account be blocked?",
      "timestamp": "2026-01-26T10:16:10Z"
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response**:

```json
{
  "status": "success",
  "scamDetected": true,
  "agentResponse": "Oh no! Why will it be blocked? What do I need to do?",
  "engagementMetrics": {
    "engagementDurationSeconds": 120,
    "totalMessagesExchanged": 3
  },
  "extractedIntelligence": {
    "bankAccounts": [],
    "upiIds": [],
    "phishingLinks": [],
    "phoneNumbers": [],
    "suspiciousKeywords": ["verify", "urgent", "block"]
  },
  "agentNotes": "Scam detected: bank_fraud. Using urgency tactics.",
  "sessionComplete": false
}
```

#### 3. Get Session Info

```bash
GET /api/session/{session_id}
```

#### 4. Delete Session

```bash
DELETE /api/session/{session_id}
```

## 🧪 Testing

Run the test suite:

```bash
python tests/test_api.py
```

This will run through several test scenarios:

- Bank fraud scenario
- Phishing scenario
- Multi-turn conversation

## 🏗️ Project Structure

```
AI Scammer Detection/
├── main.py                          # FastAPI application entry point
├── config.py                        # Configuration management
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .env                            # Your environment variables (not in git)
├── README.md                        # This file
├── src/
│   ├── models/
│   │   ├── schemas.py              # Pydantic models for API
│   │   └── session.py              # Session data model
│   ├── services/
│   │   ├── session_manager.py      # Session state management
│   │   ├── scam_detector.py        # AI-powered scam detection
│   │   ├── ai_agent.py             # AI agent for conversations
│   │   └── guvi_callback.py        # GUVI endpoint integration
│   └── utils/
│       └── intelligence_extractor.py # Extract structured data
└── tests/
    └── test_api.py                  # API test suite
```

## 🎭 How It Works

1. **Message Reception**: API receives a message from the platform
2. **Scam Detection**: AI analyzes the message for scam indicators
3. **Agent Activation**: If scam detected, AI agent is activated
4. **Persona Selection**: Agent selects appropriate persona based on scam type
5. **Response Generation**: Agent generates human-like response to engage scammer
6. **Intelligence Extraction**: System extracts bank accounts, UPIs, links, etc.
7. **Conversation Management**: Tracks conversation state and decides when to end
8. **GUVI Callback**: Sends final results to evaluation endpoint

## 🤖 AI Agent Personas

The agent can adopt different personas:

- **Cautious User**: Asks clarifying questions, slightly worried
- **Eager Victim**: Willing to help but needs guidance
- **Confused Elderly**: Needs simple explanations, slow to understand
- **Busy Professional**: Wants quick solutions, easily distracted

## 🔍 Intelligence Extraction

The system automatically extracts:

- **Bank Account Numbers**: 9-18 digit sequences
- **UPI IDs**: Patterns like `user@paytm`, `user@phonepe`
- **Phone Numbers**: 10-15 digit numbers with optional +
- **Phishing Links**: HTTP/HTTPS URLs
- **Suspicious Keywords**: Urgency words, scam tactics

## 📊 Evaluation Criteria

The system is designed to excel in:

1. **Scam Detection Accuracy**: High-confidence AI-powered detection
2. **Engagement Quality**: Natural, human-like conversations
3. **Intelligence Extraction**: Comprehensive data gathering
4. **API Stability**: Robust error handling and session management
5. **Ethical Behavior**: No harassment, responsible data handling

## 🔒 Security & Ethics

- ✅ Responsible data handling
- ✅ No impersonation of real individuals
- ✅ No illegal instructions
- ✅ No harassment
- ✅ Secure API key authentication
- ✅ Session timeout and cleanup

## 🐛 Troubleshooting

### API Key Error

```
{"detail": "Invalid API key"}
```

**Solution**: Check that your `x-api-key` header matches the `API_KEY` in `.env`

### LLM API Error

```
Error in scam detection: ...
```

**Solution**: Verify your OpenAI/Anthropic API key is correct and has credits

### Port Already in Use

```
Address already in use
```

**Solution**: Change `PORT` in `.env` or stop other services using port 8000

### Session Not Found

```
{"detail": "Session not found"}
```

**Solution**: Session may have expired (30 min timeout) or never existed

## 📈 Performance Tips

1. **Use GPT-4 for best results**: More natural conversations and better scam detection
2. **Adjust temperature**: Higher = more creative, lower = more consistent
3. **Monitor session cleanup**: Clean up old sessions regularly
4. **Use Redis for production**: Better session management at scale

## 🚀 Deployment

### Deploy to Cloud (Example: Railway)

1. Create `Procfile`:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. Set environment variables in Railway dashboard

3. Deploy from GitHub

### Deploy with Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📞 Support

For issues or questions about the implementation, check:

- API logs in the console
- Test suite output
- Response `agentNotes` field for debugging

## 📄 License

This project is created for the GUVI Hackathon evaluation.

## 🎯 One-Line Summary

Build an AI-powered agentic honeypot API that detects scam messages, engages scammers in multi-turn conversations, extracts intelligence, and reports the final result back to the GUVI evaluation endpoint.
