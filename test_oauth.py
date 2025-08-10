"""
OAuth2 Implementation Test Module

This module implements OAuth2 authentication with JWT tokens.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt
from typing import Dict, Any

app = FastAPI()
security = HTTPBearer()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def verify_token(token: str = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token and return payload.
    
    Args:
        token: Bearer token from request
        
    Returns:
        Token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/protected")
async def protected_endpoint(current_user: dict = Depends(verify_token)):
    """Protected endpoint requiring authentication."""
    return {"message": "Hello, authenticated user!", "user": current_user}

class OAuthManager:
    """OAuth2 management class."""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
    
    def create_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT token for user."""
        return jwt.encode(user_data, self.secret_key, algorithm=self.algorithm)
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token."""
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])