from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
import schemas
from database import get_connection
from security import get_current_user_id

router = APIRouter(prefix="/api/articles", tags=["Articles"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.ArticleResponse)
def create_article(article: schemas.ArticleCreate, current_user_id: int = Depends(get_current_user_id)):
    """13. Create a new article as a draft"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO articles (author_id, title, content, status, view_count)
            VALUES (%s, %s, %s, 'DRAFT', 0)
            RETURNING article_id, author_id, title, content, view_count, status,
                      created_at, updated_at, published_at
            """,
            (current_user_id, article.title, article.content),
        )
        conn.commit()
        return dict(cur.fetchone())
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("", response_model=List[schemas.ArticleListResponse])
def search_filter_sort_articles(
    search: Optional[str] = Query(None),
    tag: Optional[int] = Query(None),
    sort: Optional[str] = Query(None),
):
    """34/35/37. Search, filter, or sort published articles"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if tag:
            cur.execute(
                """
                SELECT a.article_id, a.title, a.author_id, a.view_count, a.status, a.published_at
                FROM articles a
                JOIN article_tags at2 ON a.article_id = at2.article_id
                WHERE at2.tag_id = %s AND a.status = 'PUBLISHED'
                ORDER BY a.published_at DESC
                """,
                (tag,),
            )
        elif search:
            cur.execute(
                """
                SELECT article_id, title, author_id, view_count, status, published_at
                FROM articles
                WHERE title ILIKE %s AND status = 'PUBLISHED'
                ORDER BY published_at DESC
                """,
                (f"%{search}%",),
            )
        elif sort == "trending":
            cur.execute(
                """
                SELECT article_id, title, author_id, view_count, status, published_at
                FROM articles WHERE status = 'PUBLISHED'
                ORDER BY view_count DESC LIMIT 20
                """
            )
        else:
            cur.execute(
                """
                SELECT article_id, title, author_id, view_count, status, published_at
                FROM articles WHERE status = 'PUBLISHED'
                ORDER BY published_at DESC
                """
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/{article_id}", response_model=schemas.ArticleResponse)
def read_article(article_id: int):
    """27. Read a single, full article"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT article_id, author_id, title, content, view_count, status,
                   created_at, updated_at, published_at
            FROM articles WHERE article_id = %s AND status = 'PUBLISHED'
            """,
            (article_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)
    finally:
        conn.close()


@router.put("/{article_id}", response_model=schemas.ArticleResponse)
def update_draft(article_id: int, article_update: schemas.ArticleUpdate, current_user_id: int = Depends(get_current_user_id)):
    """14. Save edits to an existing draft"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Verify authorship to prevent IDOR
        cur.execute("SELECT author_id FROM articles WHERE article_id = %s", (article_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        if row["author_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this article")

        if article_update.title:
            cur.execute("UPDATE articles SET title=%s, updated_at=NOW() WHERE article_id=%s AND author_id=%s",
                        (article_update.title, article_id, current_user_id))
        if article_update.content:
            cur.execute("UPDATE articles SET content=%s, updated_at=NOW() WHERE article_id=%s AND author_id=%s",
                        (article_update.content, article_id, current_user_id))
        conn.commit()
        cur.execute("SELECT article_id, author_id, title, content, view_count, status, created_at, updated_at, published_at FROM articles WHERE article_id=%s", (article_id,))
        row = cur.fetchone()
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(article_id: int, current_user_id: int = Depends(get_current_user_id)):
    """17. Delete an article permanently"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Verify authorship to prevent IDOR
        cur.execute("SELECT author_id FROM articles WHERE article_id = %s", (article_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        if row["author_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this article")

        cur.execute("DELETE FROM articles WHERE article_id=%s AND author_id=%s", (article_id, current_user_id))
        conn.commit()
    finally:
        conn.close()


@router.patch("/{article_id}/publish", response_model=schemas.ArticleResponse)
def publish_article(article_id: int, current_user_id: int = Depends(get_current_user_id)):
    """15. Publish a draft article"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Verify authorship to prevent IDOR
        cur.execute("SELECT author_id FROM articles WHERE article_id = %s", (article_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        if row["author_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to publish this article")

        cur.execute(
            """
            UPDATE articles SET status='PUBLISHED', published_at=NOW()
            WHERE article_id=%s AND author_id=%s
            RETURNING article_id, author_id, title, content, view_count, status,
                      created_at, updated_at, published_at
            """,
            (article_id, current_user_id),
        )
        conn.commit()
        row = cur.fetchone()
        return dict(row)
    finally:
        conn.close()


@router.patch("/{article_id}/unpublish", response_model=schemas.ArticleResponse)
def unpublish_article(article_id: int, current_user_id: int = Depends(get_current_user_id)):
    """16. Unpublish a live article"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Verify authorship to prevent IDOR
        cur.execute("SELECT author_id FROM articles WHERE article_id = %s", (article_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        if row["author_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to unpublish this article")

        cur.execute(
            """
            UPDATE articles SET status='DRAFT', published_at=NULL
            WHERE article_id=%s AND author_id=%s
            RETURNING article_id, author_id, title, content, view_count, status,
                      created_at, updated_at, published_at
            """,
            (article_id, current_user_id),
        )
        conn.commit()
        row = cur.fetchone()
        return dict(row)
    finally:
        conn.close()


@router.post("/{article_id}/tags", status_code=status.HTTP_201_CREATED)
def assign_tag(article_id: int, tag_id: int, current_user_id: int = Depends(get_current_user_id)):
    """23. Assign a tag to an article"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Verify authorship to prevent IDOR
        cur.execute("SELECT author_id FROM articles WHERE article_id = %s", (article_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        if row["author_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify tags on this article")

        cur.execute(
            "INSERT INTO article_tags (article_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (article_id, tag_id),
        )
        conn.commit()
        return {"message": "Tag assigned to article"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/{article_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag(article_id: int, tag_id: int, current_user_id: int = Depends(get_current_user_id)):
    """24. Remove a tag from an article"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Verify authorship to prevent IDOR
        cur.execute("SELECT author_id FROM articles WHERE article_id = %s", (article_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        if row["author_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify tags on this article")

        cur.execute("DELETE FROM article_tags WHERE article_id=%s AND tag_id=%s", (article_id, tag_id))
        conn.commit()
    except HTTPException:
        raise
    finally:
        conn.close()


@router.get("/{article_id}/tags", response_model=List[schemas.TagResponse])
def view_article_tags(article_id: int):
    """25. View all tags on a specific article"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT t.tag_id, t.name, t.created_at
            FROM tags t JOIN article_tags at2 ON t.tag_id = at2.tag_id
            WHERE at2.article_id = %s
            """,
            (article_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

