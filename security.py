import hashlib
import os
import hmac
import base64
import json
import time
from fastapi import Header, HTTPException, Depends
from database import get_connection

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-fallback-key-change-in-prod-12345")

# ==============================================================================
# PASSWORD HASHING (PBKDF2-HMAC-SHA256)
# ==============================================================================
def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with a random 16-byte salt
    and 100,000 iterations. Returns string formatted as pbkdf2_sha256$100000$salt$hash.
    """
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"pbkdf2_sha256$100000${salt.hex()}${pwd_hash.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies a password against a PBKDF2 hash.
    Also supports legacy plain-text passwords stored with a "plain:" prefix.
    """
    if not hashed:
        return False
    if hashed.startswith("plain:"):
        return hashed == f"plain:{password}"
    
    parts = hashed.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False
    
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        original_hash = bytes.fromhex(parts[3])
        
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(new_hash, original_hash)
    except Exception:
        return False


# ==============================================================================
# SECURE TOKEN MANAGEMENT (HMAC-SHA256 Signed JSON Payload)
# ==============================================================================
def create_token(user_id: int) -> str:
    """
    Creates a secure, signed token containing the user_id and expiration timestamp.
    """
    payload = {
        "user_id": user_id,
        "exp": time.time() + (86400 * 30)  # 30 days expiration
    }
    payload_bytes = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8').rstrip('=')
    
    # Calculate signature
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        payload_bytes.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_bytes = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{payload_bytes}.{sig_bytes}"


def verify_token(token: str) -> int:
    """
    Verifies the signature and expiration of a token, returning the user_id.
    Returns None if signature is invalid or token is expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_bytes, sig_bytes = parts
        
        # Verify signature
        pad_payload = payload_bytes + '=' * (4 - len(payload_bytes) % 4)
        pad_sig = sig_bytes + '=' * (4 - len(sig_bytes) % 4)
        
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            payload_bytes.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        if not hmac.compare_digest(base64.urlsafe_b64decode(pad_sig), expected_sig):
            return None
            
        payload = json.loads(base64.urlsafe_b64decode(pad_payload).decode('utf-8'))
        if payload.get("exp", 0) < time.time():
            return None  # Token has expired
            
        return payload.get("user_id")
    except Exception:
        return None


# ==============================================================================
# FASTAPI DEPENDENCIES
# ==============================================================================
def get_current_user_id(authorization: str = Header(None)) -> int:
    """
    Dependency to get the authenticated user_id from the Authorization header.
    Throws 401 Unauthorized if token is missing, invalid, or expired.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format. Must be Bearer <token>")
    
    token = authorization.split(" ")[1]
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
    
    # Check if the user is active in the database
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT is_active FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Authenticated user not found")
        if not row["is_active"]:
            raise HTTPException(status_code=401, detail="User account is deactivated")
        return user_id
    finally:
        conn.close()


def get_current_admin_user_id(current_user_id: int = Depends(get_current_user_id)) -> int:
    """
    Dependency to check if the current user has admin privileges.
    Throws 403 Forbidden if the user is not an admin.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Verify if is_admin column exists in database schema
        cur.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'is_admin'
        """)
        has_admin_col = cur.fetchone()
        
        if has_admin_col:
            cur.execute("SELECT is_admin FROM users WHERE user_id = %s", (current_user_id,))
            row = cur.fetchone()
            if not row or not row.get("is_admin", False):
                raise HTTPException(status_code=403, detail="Admin privileges required")
        else:
            # Fallback check based on email domain/patterns
            cur.execute("SELECT email, username FROM users WHERE user_id = %s", (current_user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=403, detail="Admin privileges required")
            email = row["email"].lower()
            username = row["username"].lower()
            if email != "admin@echobreaker.com" and "admin" not in username:
                raise HTTPException(status_code=403, detail="Admin privileges required")
                
        return current_user_id
    finally:
        conn.close()
