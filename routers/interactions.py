from fastapi import APIRouter, HTTPException, status, Depends
import schemas
from database import get_connection
from security import get_current_user_id

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])


@router.post("/view", status_code=status.HTTP_201_CREATED)
def log_view_interaction(interaction: schemas.ViewInteraction, article_id: int, current_user_id: int = Depends(get_current_user_id)):
    """
    28. Log a view interaction when a user reads an article (CRITICAL — feeds algorithm)
    - INSERT new row in view_logs.
    - UPDATE view_count in articles.
    - UPSERT tag affinity scores in user_preferences.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Insert view log
        cur.execute(
            """
            INSERT INTO view_logs (user_id, article_id, view_duration_seconds)
            VALUES (%s, %s, %s)
            """,
            (current_user_id, article_id, interaction.view_duration_seconds),
        )

        # Update article view count
        cur.execute(
            """
            UPDATE articles
            SET view_count = view_count + 1
            WHERE article_id = %s
            """,
            (article_id,),
        )

        # Get tags for this article
        cur.execute(
            """
            SELECT tag_id FROM article_tags
            WHERE article_id = %s
            """,
            (article_id,),
        )
        tag_rows = cur.fetchall()

        # Update user affinity scores for each tag
        for tag_row in tag_rows:
            tag_id = tag_row["tag_id"]
            cur.execute(
                """
                INSERT INTO user_preferences (user_id, tag_id, affinity_score)
                VALUES (%s, %s, 1)
                ON CONFLICT (user_id, tag_id)
                DO UPDATE SET affinity_score = user_preferences.affinity_score + 1, updated_at = NOW()
                """,
                (current_user_id, tag_id),
            )

        conn.commit()
        return {"message": "View logged and preferences updated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/like", status_code=status.HTTP_201_CREATED)
def like_article(article_id: int, current_user_id: int = Depends(get_current_user_id)):
    """
    29. Like an article
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO article_interactions (user_id, article_id, interaction_type)
            VALUES (%s, %s, 'LIKE')
            ON CONFLICT DO NOTHING
            """,
            (current_user_id, article_id),
        )
        conn.commit()
        return {"message": "Article liked"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/like/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlike_article(article_id: int, current_user_id: int = Depends(get_current_user_id)):
    """
    30. Unlike an article
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM article_interactions
            WHERE user_id = %s AND article_id = %s AND interaction_type = 'LIKE'
            """,
            (current_user_id, article_id),
        )
        conn.commit()
    finally:
        conn.close()


@router.post("/save", status_code=status.HTTP_201_CREATED)
def save_article(article_id: int, current_user_id: int = Depends(get_current_user_id)):
    """
    31. Save/bookmark an article for later reading
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO article_interactions (user_id, article_id, interaction_type)
            VALUES (%s, %s, 'SAVE')
            ON CONFLICT DO NOTHING
            """,
            (current_user_id, article_id),
        )
        conn.commit()
        return {"message": "Article saved"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/save/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_article(article_id: int, current_user_id: int = Depends(get_current_user_id)):
    """
    32. Remove a saved/bookmarked article
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM article_interactions
            WHERE user_id = %s AND article_id = %s AND interaction_type = 'SAVE'
            """,
            (current_user_id, article_id),
        )
        conn.commit()
    finally:
        conn.close()

