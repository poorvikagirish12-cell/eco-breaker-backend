from fastapi import APIRouter, HTTPException, status
import schemas
from database import get_connection

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate):
    """
    1. Register a new reader account
    Inserts a new row into users with hashed_password placeholder.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        # NOTE: In production replace "plain:" prefix with a real bcrypt hash.
        password_hash = f"plain:{user.password}"
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
        return dict(row)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(credentials: schemas.UserLogin):
    """
    2. Log in with email and password
    Returns a mock JWT token on success.
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
        # NOTE: replace with real bcrypt check in production
        if row["password_hash"] != f"plain:{credentials.password}":
            raise HTTPException(status_code=401, detail="Invalid credentials")
        cur.execute(
            "UPDATE users SET last_login = NOW() WHERE user_id = %s", (row["user_id"],)
        )
        conn.commit()
        return {"message": "Login successful", "token": f"mock-jwt-{row['user_id']}"}
    finally:
        conn.close()


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user():
    """
    3. Log out of the current session (stateless — client discards token)
    """
    return {"message": "Logout successful"}
