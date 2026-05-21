from fastapi import APIRouter, HTTPException, status
from typing import List
import schemas
from database import get_connection

router = APIRouter(prefix="/api/authors", tags=["Authors"])


@router.post("/apply", status_code=status.HTTP_201_CREATED, response_model=schemas.AuthorApplicationResponse)
def apply_for_author(application: schemas.AuthorApplicationCreate):
    """9. Apply to become a verified author"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO author_applications (user_id, application_text, status)
            VALUES (1, %s, 'PENDING')
            RETURNING application_id, user_id, application_text, status, applied_at
            """,
            (application.application_text,),
        )
        conn.commit()
        return dict(cur.fetchone())
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("/me/articles", response_model=List[schemas.ArticleListResponse])
def view_my_articles():
    """18. View all of own articles (drafts + published)"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT article_id, title, author_id, view_count, status, published_at
            FROM articles WHERE author_id = 1
            ORDER BY created_at DESC
            """
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
            SELECT article_id, title, author_id, view_count, status, published_at
            FROM articles WHERE author_id = %s AND status = 'PUBLISHED'
            ORDER BY published_at DESC
            """,
            (user_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
