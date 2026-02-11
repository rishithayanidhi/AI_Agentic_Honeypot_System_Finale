from typing import Dict, Optional
from datetime import datetime, timedelta
from src.models.session import SessionData
from config import settings


class SessionManager:
    """Manages session state across multiple requests"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve a session by ID"""
        session = self.sessions.get(session_id)
        
        # Check if session has expired
        if session:
            timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
            if datetime.now() - session.last_activity > timeout:
                self.delete_session(session_id)
                return None
        
        return session
    
    def create_session(self, session_id: str) -> SessionData:
        """Create a new session"""
        session = SessionData(session_id=session_id)
        self.sessions[session_id] = session
        return session
    
    def get_or_create_session(self, session_id: str) -> SessionData:
        """Get existing session or create new one"""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        return session
    
    def update_session(self, session: SessionData):
        """Update session data"""
        session.last_activity = datetime.now()
        self.sessions[session.session_id] = session
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
        current_time = datetime.now()
        
        expired = [
            sid for sid, session in self.sessions.items()
            if current_time - session.last_activity > timeout
        ]
        
        for sid in expired:
            self.delete_session(sid)


# Global session manager instance
session_manager = SessionManager()
