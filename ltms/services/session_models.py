"""Session data models for LTMC orchestration services."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set


class SessionStatus(Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    MIGRATING = "migrating"
    RECOVERING = "recovering"


@dataclass
class SessionCheckpoint:
    """Represents a session state checkpoint."""
    checkpoint_id: str
    session_id: str
    timestamp: datetime
    state_snapshot: Dict[str, Any]
    participant_states: Dict[str, Any]
    version: int


@dataclass
class SessionInfo:
    """Information about a managed session."""
    session_id: str
    status: SessionStatus
    participants: Set[str]  # Agent IDs
    created_at: datetime
    last_activity: datetime
    expires_at: Optional[datetime]
    persistent_state: Dict[str, Any]
    owned_resources: Set[str]
    metadata: Dict[str, Any]
    checkpoints: List[str]  # Checkpoint IDs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            'session_id': self.session_id,
            'status': self.status.value,
            'participants': list(self.participants),
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'persistent_state': self.persistent_state,
            'owned_resources': list(self.owned_resources),
            'metadata': self.metadata,
            'checkpoints': self.checkpoints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionInfo':
        """Create from dictionary stored in Redis."""
        return cls(
            session_id=data['session_id'],
            status=SessionStatus(data['status']),
            participants=set(data['participants']),
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            persistent_state=data['persistent_state'],
            owned_resources=set(data['owned_resources']),
            metadata=data['metadata'],
            checkpoints=data['checkpoints']
        )