import uuid
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AuthToken:
    """موجودیت توکن احراز هویت (Reset/Verify)."""
    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str
    token_type: str  # 'reset_password' or 'verify_email'
    expires_at: datetime
    created_at: datetime
