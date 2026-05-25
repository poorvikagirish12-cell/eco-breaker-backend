from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import schemas
from database import get_connection
from security import get_current_user_id

router = APIRouter(prefix="/api/authors", tags=["Authors"])


@router.post("/apply", status_code=status.HTTP_201_CREATED, response_model=schemas.AuthorApplicationResponse)
def apply_for_author(application: schemas.AuthorApplicationCreate, current_user_id: int = Depends(get_current_user_id)):
    """9. Apply to become a verified author"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO author_applications (user_id, application_text, status)
            VALUES (%s, %s, 'PENDING')
            RETURNING application_id, user_id, application_text, status, applied_at
            """,
            (current_user_id, application.application_text),
        )
        conn.commit()
        return dict(cur.fetchone())
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("/me/articles", response_model=List[schemas.ArticleListResponse])
def view_my_articles(current_user_id: int = Depends(get_current_user_id)):
    """18. View all of own articles (drafts + published)"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT article_id, title, content, author_id, view_count, status, published_at
            FROM articles WHERE author_id = %s
            ORDER BY created_at DESC
            """,
            (current_user_id,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/{user_id}/articles", response_model=List[schemas.ArticleListResponse])
def view_author_articles(user_id: int):
    """36. View all published articles by a specific author"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT article_id, title, content, author_id, view_count, status, published_at
            FROM articles WHERE author_id = %s AND status = 'PUBLISHED'
            ORDER BY published_at DESC
            """,
            (user_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

