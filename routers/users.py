from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import schemas
from database import get_connection
from security import get_current_user_id, verify_password, hash_password

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=schemas.UserResponse)
def view_profile(current_user_id: int = Depends(get_current_user_id)):
    """4. View own account profile"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = %s", (current_user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)
    finally:
        conn.close()


@router.patch("/me", response_model=schemas.UserResponse)
def update_profile(user_update: schemas.UserUpdate, current_user_id: int = Depends(get_current_user_id)):
    """5 & 6. Update own username / email"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if user_update.username:
            cur.execute("UPDATE users SET username=%s WHERE user_id=%s", (user_update.username, current_user_id))
        if user_update.email:
            cur.execute("UPDATE users SET email=%s WHERE user_id=%s", (user_update.email, current_user_id))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE user_id = %s", (current_user_id,))
        row = cur.fetchone()
        return dict(row)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
def change_password(data: schemas.PasswordChange, current_user_id: int = Depends(get_current_user_id)):
    """7. Change account password"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE user_id=%s", (current_user_id,))
        row = cur.fetchone()
        if not row or not verify_password(data.old_password, row["password_hash"]):
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        
        hashed_new_password = hash_password(data.new_password)
        cur.execute(
            "UPDATE users SET password_hash=%s WHERE user_id=%s",
            (hashed_new_password, current_user_id)
        )
        conn.commit()
        return {"message": "Password updated successfully"}
    finally:
        conn.close()


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(current_user_id: int = Depends(get_current_user_id)):
    """8. Delete own account permanently"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE user_id=%s", (current_user_id,))
        conn.commit()
    finally:
        conn.close()


@router.get("/me/saved-articles", response_model=List[schemas.ArticleListResponse])
def view_saved_articles(current_user_id: int = Depends(get_current_user_id)):
    """33. View all own saved/bookmarked articles"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.article_id, a.title, a.author_id, a.view_count, a.status, a.published_at,
                   u.username AS author_name, u.is_verified_author
            FROM articles a
            JOIN users u ON a.author_id = u.user_id
            JOIN article_interactions ai ON a.article_id = ai.article_id
            WHERE ai.user_id = %s AND ai.interaction_type = 'SAVE'
            ORDER BY ai.created_at DESC
            """,
            (current_user_id,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/me/preferences", response_model=List[schemas.TagAffinity])
def view_tag_preferences(current_user_id: int = Depends(get_current_user_id)):
    """38. View own current tag affinity scores"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT t.name, up.affinity_score
            FROM user_preferences up
            JOIN tags t ON up.tag_id = t.tag_id
            WHERE up.user_id = %s
            ORDER BY up.affinity_score DESC
            """,
            (current_user_id,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.delete("/me/preferences", status_code=status.HTTP_204_NO_CONTENT)
def reset_preferences(current_user_id: int = Depends(get_current_user_id)):
    """39. Reset all own tag affinity scores"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM user_preferences WHERE user_id=%s", (current_user_id,))
        conn.commit()
    finally:
        conn.close()


@router.get("/me/history", response_model=List[schemas.HistoryResponse])
def view_reading_history(current_user_id: int = Depends(get_current_user_id)):
    """40. View own full reading history"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.article_id, a.title, vl.viewed_at, vl.view_duration_seconds
            FROM view_logs vl
            JOIN articles a ON vl.article_id = a.article_id
            WHERE vl.user_id = %s
            ORDER BY vl.viewed_at DESC
            """,
            (current_user_id,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.delete("/me/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_reading_history(current_user_id: int = Depends(get_current_user_id)):
    """41. Clear own reading history"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM view_logs WHERE user_id=%s", (current_user_id,))
        conn.commit()
    finally:
        conn.close()

