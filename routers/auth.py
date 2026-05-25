import os
import secrets
import time
from fastapi import APIRouter, HTTPException, status, Query
import schemas
from database import get_connection
from security import hash_password, verify_password, create_token
from email_service import send_verification_email

router = APIRouter(prefix="/api/auth", tags=["Auth"])

VERIFICATION_TOKEN_EXPIRY_SECONDS = 86400  # 24 hours


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate):
    """
    1. Register a new reader account.
    Sends an email verification link; clicking it auto-grants author access.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        password_hash = hash_password(user.password)

        # Generate a secure verification token (URL-safe, 48 hex chars)
        verification_token = secrets.token_urlsafe(36)
        token_expiry_seconds = time.time() + VERIFICATION_TOKEN_EXPIRY_SECONDS

        cur.execute(
            """
            INSERT INTO users (username, email, password_hash, is_verified_author, is_active,
                               email_verified, email_verification_token, email_token_expires_at)
            VALUES (%s, %s, %s, FALSE, TRUE, FALSE, %s,
                    TO_TIMESTAMP(%s))
            RETURNING user_id, username, email, is_verified_author, is_active, created_at, last_login
            """,
            (user.username, user.email, password_hash, verification_token, token_expiry_seconds),
        )
        conn.commit()
        row = cur.fetchone()
        user_data = dict(row)

        # Generate token for auto-login on client side
        user_data["token"] = create_token(user_data["user_id"])

        # Send verification email (non-blocking — failure doesn't break registration)
        try:
            send_verification_email(user.email, user.username, verification_token)
        except Exception as e:
            print(f"[Auth] Warning: Could not send verification email: {e}")

        return user_data
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(token: str = Query(..., description="Email verification token")):
    """
    Verify a user's email using the token sent on registration.
    On success, grants full is_verified_author = TRUE status automatically.
    """
    if not token:
        raise HTTPException(status_code=400, detail="Verification token is required")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT user_id, email, username, email_verified, email_token_expires_at
            FROM users
            WHERE email_verification_token = %s
            """,
            (token,),
        )
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=400, detail="Invalid verification token")

        if row["email_verified"]:
            return {"message": "Email already verified. You are a verified author!", "already_verified": True}

        # Check expiry
        if row["email_token_expires_at"]:
            import datetime
            expiry = row["email_token_expires_at"]
            now = datetime.datetime.now(datetime.timezone.utc)
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=datetime.timezone.utc)
            if now > expiry:
                raise HTTPException(
                    status_code=400,
                    detail="Verification token has expired. Please request a new one."
                )

        # Mark verified and grant author status
        cur.execute(
            """
            UPDATE users
            SET email_verified = TRUE,
                is_verified_author = TRUE,
                email_verification_token = NULL,
                email_token_expires_at = NULL
            WHERE user_id = %s
            """,
            (row["user_id"],),
        )
        conn.commit()

        return {
            "message": f"Email verified! Welcome, {row['username']}. You now have full author access.",
            "user_id": row["user_id"],
            "email": row["email"],
        }
    finally:
        conn.close()


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification(email: str = Query(...)):
    """
    Resend the email verification link for a given email address.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, username, email, email_verified FROM users WHERE email = %s AND is_active = TRUE",
            (email,),
        )
        row = cur.fetchone()

        if not row:
            # Don't reveal whether user exists
            return {"message": "If that email is registered, a verification link has been sent."}

        if row["email_verified"]:
            return {"message": "Email is already verified. No action needed."}

        # Generate a fresh token
        new_token = secrets.token_urlsafe(36)
        token_expiry_seconds = time.time() + VERIFICATION_TOKEN_EXPIRY_SECONDS

        cur.execute(
            """
            UPDATE users
            SET email_verification_token = %s,
                email_token_expires_at = TO_TIMESTAMP(%s)
            WHERE user_id = %s
            """,
            (new_token, token_expiry_seconds, row["user_id"]),
        )
        conn.commit()

        try:
            send_verification_email(row["email"], row["username"], new_token)
        except Exception as e:
            print(f"[Auth] Warning: Could not resend verification email: {e}")

        return {"message": "If that email is registered, a verification link has been sent."}
    finally:
        conn.close()


@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(credentials: schemas.UserLogin):
    """
    2. Log in with email and password.
    Returns a secure HMAC-SHA256 signed token on success.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, email, username, password_hash, email_verified FROM users WHERE email = %s AND is_active = TRUE",
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
        return {
            "message": "Login successful",
            "token": token,
            "username": row["username"],
            "email_verified": row.get("email_verified", False),
        }
    finally:
        conn.close()


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user():
    """
    3. Log out of the current session (stateless — client discards token)
    """
    return {"message": "Logout successful"}
