from fastapi import APIRouter, status, HTTPException, Depends
from typing import List
import schemas
from database import get_connection
from security import get_current_admin_user_id

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin_user_id)]
)



@router.put("/authors/{user_id}/approve", status_code=status.HTTP_200_OK)
def approve_author(user_id: int):
    """
    10. Admin approves an author application
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE users
            SET is_verified_author = TRUE
            WHERE user_id = %s
            """,
            (user_id,),
        )
        cur.execute(
            """
            UPDATE author_applications
            SET status = 'APPROVED'
            WHERE user_id = %s
            """,
            (user_id,),
        )
        conn.commit()
        return {"message": "Author approved"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.put("/authors/{user_id}/revoke", status_code=status.HTTP_200_OK)
def revoke_author(user_id: int):
    """
    11. Admin revokes author status from a user
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE users
            SET is_verified_author = FALSE
            WHERE user_id = %s
            """,
            (user_id,),
        )
        cur.execute(
            """
            UPDATE author_applications
            SET status = 'REJECTED'
            WHERE user_id = %s
            """,
            (user_id,),
        )
        conn.commit()
        return {"message": "Author revoked"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("/authors", response_model=List[schemas.UserResponse])
def view_verified_authors():
    """
    12. Admin views list of all verified authors
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM users
            WHERE is_verified_author = TRUE
            ORDER BY username ASC
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/reports/user-count", response_model=schemas.CountReport)
def report_user_count():
    """
    42. Admin views total count of all registered users
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM users")
        row = cur.fetchone()
        return {"count": row["count"] if row else 0}
    finally:
        conn.close()


@router.get("/reports/article-count", response_model=schemas.CountReport)
def report_article_count():
    """
    43. Admin views total count of all published articles
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM articles WHERE status = 'PUBLISHED'")
        row = cur.fetchone()
        return {"count": row["count"] if row else 0}
    finally:
        conn.close()


@router.get("/reports/total-views", response_model=schemas.CountReport)
def report_total_views():
    """
    44. Admin views total platform-wide article views
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(view_count), 0) as count FROM articles")
        row = cur.fetchone()
        return {"count": row["count"] if row else 0}
    finally:
        conn.close()


@router.get("/reports/top-articles", response_model=List[schemas.ArticleListResponse])
def report_top_articles():
    """
    45. Admin views list of the top 10 most-read articles on the platform
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT article_id, title, author_id, view_count, status, published_at
            FROM articles
            WHERE status = 'PUBLISHED'
            ORDER BY view_count DESC
            LIMIT 10
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/reports/top-tags", response_model=List[schemas.TagUsage])
def report_top_tags():
    """
    46. Admin views list of the top 5 most-interacted tags on the platform
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT t.name, COUNT(at2.article_tag_id) as usage_count
            FROM article_tags at2
            JOIN tags t ON at2.tag_id = t.tag_id
            GROUP BY t.name
            ORDER BY usage_count DESC
            LIMIT 5
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_article(article_id: int):
    """
    47. Admin hard-deletes any article (moderation)
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM articles WHERE article_id = %s", (article_id,))
        conn.commit()
    finally:
        conn.close()


@router.put("/users/{user_id}/deactivate", status_code=status.HTTP_200_OK)
def deactivate_user(user_id: int):
    """
    48. Admin deactivates (suspends) a user account
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = FALSE WHERE user_id = %s", (user_id,))
        conn.commit()
        return {"message": "User deactivated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.put("/users/{user_id}/activate", status_code=status.HTTP_200_OK)
def activate_user(user_id: int):
    """
    49. Admin reactivates a suspended user account
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = TRUE WHERE user_id = %s", (user_id,))
        conn.commit()
        return {"message": "User activated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("/users", response_model=List[schemas.UserResponse])
def admin_view_all_users():
    """
    50. Admin views full list of all platform users
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
