from fastapi import APIRouter, HTTPException, status
from typing import List
import schemas
from database import get_connection

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=schemas.UserResponse)
def view_profile():
    """4. View own account profile (mock user_id=1 — replace with JWT auth)"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = 1")
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)
    finally:
        conn.close()


@router.patch("/me", response_model=schemas.UserResponse)
def update_profile(user_update: schemas.UserUpdate):
    """5 & 6. Update own username / email"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if user_update.username:
            cur.execute("UPDATE users SET username=%s WHERE user_id=1", (user_update.username,))
        if user_update.email:
            cur.execute("UPDATE users SET email=%s WHERE user_id=1", (user_update.email,))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE user_id = 1")
        row = cur.fetchone()
        return dict(row)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
def change_password(data: schemas.PasswordChange):
    """7. Change account password"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE user_id=1")
        row = cur.fetchone()
        if not row or row["password_hash"] != f"plain:{data.old_password}":
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        cur.execute(
            "UPDATE users SET password_hash=%s WHERE user_id=1",
            (f"plain:{data.new_password}",)
        )
        conn.commit()
        return {"message": "Password updated successfully"}
    finally:
        conn.close()


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account():
    """8. Delete own account permanently"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE user_id=1")
        conn.commit()
    finally:
        conn.close()


@router.get("/me/saved-articles", response_model=List[schemas.ArticleListResponse])
def view_saved_articles():
    """33. View all own saved/bookmarked articles"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.article_id, a.title, a.author_id, a.view_count, a.status, a.published_at
            FROM articles a
            JOIN article_interactions ai ON a.article_id = ai.article_id
            WHERE ai.user_id = 1 AND ai.interaction_type = 'SAVE'
            ORDER BY ai.created_at DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/me/preferences", response_model=List[schemas.TagAffinity])
def view_tag_preferences():
    """38. View own current tag affinity scores"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT t.name, up.affinity_score
            FROM user_preferences up
            JOIN tags t ON up.tag_id = t.tag_id
            WHERE up.user_id = 1
            ORDER BY up.affinity_score DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.delete("/me/preferences", status_code=status.HTTP_204_NO_CONTENT)
def reset_preferences():
    """39. Reset all own tag affinity scores"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM user_preferences WHERE user_id=1")
        conn.commit()
    finally:
        conn.close()


@router.get("/me/history", response_model=List[schemas.HistoryResponse])
def view_reading_history():
    """40. View own full reading history"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.article_id, a.title, vl.viewed_at, vl.view_duration_seconds
            FROM view_logs vl
            JOIN articles a ON vl.article_id = a.article_id
            WHERE vl.user_id = 1
            ORDER BY vl.viewed_at DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.delete("/me/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_reading_history():
    """41. Clear own reading history"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM view_logs WHERE user_id=1")
        conn.commit()
    finally:
        conn.close()
