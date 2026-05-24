from fastapi import APIRouter, HTTPException, status
import schemas
from database import get_connection
from security import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate):
    """
    1. Register a new reader account
    Inserts a new row into users with a secure PBKDF2 hash.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        password_hash = hash_password(user.password)
        cur.execute(
            """
            INSERT INTO users (username, email, password_hash, is_verified_author, is_active)
            VALUES (%s, %s, %s, FALSE, TRUE)
            RETURNING user_id, username, email, is_verified_author, is_active, created_at, last_login
            """,
            (user.username, user.email, password_hash),
        )
        conn.commit()
        row = cur.fetchone()
        user_data = dict(row)
        # Generate token for auto-login on client side
        user_data["token"] = create_token(user_data["user_id"])
        return user_data
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(credentials: schemas.UserLogin):
    """
    2. Log in with email and password
    Returns a secure HMAC-SHA256 signed token on success.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, email, password_hash FROM users WHERE email = %s AND is_active = TRUE",
            (credentials.email,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(credentials.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        cur.execute(
            "UPDATE users SET last_login = NOW() WHERE user_id = %s", (row["user_id"],)
        )
        conn.commit()
        
        token = create_token(row["user_id"])
        return {"message": "Login successful", "token": token}
    finally:
        conn.close()


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user():
    """
    3. Log out of the current session (stateless — client discards token)
    """
    return {"message": "Logout successful"}

