"""Break-glass mode for emergency policy bypass."""
import time
from typing import Dict, Any, Optional
from src.pep.audit_logger import AuditLogger


class BreakGlassMode:
    """Break-glass mode for emergency policy bypass."""
    
    def __init__(self, audit_logger: AuditLogger):
        """Initialize break-glass mode.
        
        Args:
            audit_logger: Audit logger for break-glass events
        """
        self.audit_logger = audit_logger
        self.active_sessions = {}
    
    def activate(
        self,
        user_id: str,
        reason: str,
        duration_minutes: int = 15
    ) -> str:
        """Activate break-glass mode for a user.
        
        Args:
            user_id: User ID
            reason: Reason for activation
            duration_minutes: Duration in minutes (default: 15)
            
        Returns:
            Break-glass session ID
        """
        session_id = f"break-glass-{int(time.time())}"
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "reason": reason,
            "expires_at": time.time() + (duration_minutes * 60),
            "activated_at": time.time()
        }
        
        # Log activation
        self.audit_logger.log_break_glass_activation(
            session_id=session_id,
            user_id=user_id,
            reason=reason
        )
        
        return session_id
    
    def is_active(self, session_id: str) -> bool:
        """Check if break-glass mode is active.
        
        Args:
            session_id: Break-glass session ID
            
        Returns:
            True if active, False otherwise
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        if time.time() > session["expires_at"]:
            del self.active_sessions[session_id]
            return False
        
        return True
    
    def deactivate(self, session_id: str):
        """Deactivate break-glass mode.
        
        Args:
            session_id: Break-glass session ID
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

