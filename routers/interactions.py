from fastapi import APIRouter, HTTPException, status
import schemas
from database import get_connection

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])


@router.post("/view", status_code=status.HTTP_201_CREATED)
def log_view_interaction(interaction: schemas.ViewInteraction, article_id: int):
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
            VALUES (1, %s, %s)
            """,
            (article_id, interaction.view_duration_seconds),
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

        # Update user affinity scores for each tag (mock user_id = 1)
        for tag_row in tag_rows:
            tag_id = tag_row["tag_id"]
            cur.execute(
                """
                INSERT INTO user_preferences (user_id, tag_id, affinity_score)
                VALUES (1, %s, 1)
                ON CONFLICT (user_id, tag_id)
                DO UPDATE SET affinity_score = user_preferences.affinity_score + 1, updated_at = NOW()
                """,
                (tag_id,),
            )

        conn.commit()
        return {"message": "View logged and preferences updated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.post("/like", status_code=status.HTTP_201_CREATED)
def like_article(article_id: int):
    """
    29. Like an article
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO article_interactions (user_id, article_id, interaction_type)
            VALUES (1, %s, 'LIKE')
            ON CONFLICT DO NOTHING
            """,
            (article_id,),
        )
        conn.commit()
        return {"message": "Article liked"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/like/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlike_article(article_id: int):
    """
    30. Unlike an article
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM article_interactions
            WHERE user_id = 1 AND article_id = %s AND interaction_type = 'LIKE'
            """,
            (article_id,),
        )
        conn.commit()
    finally:
        conn.close()


@router.post("/save", status_code=status.HTTP_201_CREATED)
def save_article(article_id: int):
    """
    31. Save/bookmark an article for later reading
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO article_interactions (user_id, article_id, interaction_type)
            VALUES (1, %s, 'SAVE')
            ON CONFLICT DO NOTHING
            """,
            (article_id,),
        )
        conn.commit()
        return {"message": "Article saved"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/save/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_article(article_id: int):
    """
    32. Remove a saved/bookmarked article
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM article_interactions
            WHERE user_id = 1 AND article_id = %s AND interaction_type = 'SAVE'
            """,
            (article_id,),
        )
        conn.commit()
    finally:
        conn.close()
