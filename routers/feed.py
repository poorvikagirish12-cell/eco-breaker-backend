from fastapi import APIRouter
from typing import List
import schemas
from database import get_connection

router = APIRouter(prefix="/api/feed", tags=["Feed"])


@router.get("", response_model=List[schemas.ArticleListResponse])
def get_contrarian_feed():
    """
    26. Fetch personalized contrarian feed (THE CORE ALGORITHM).
    Step 1 — Find user's TOP tags (highest affinity).
    Step 2 — Return PUBLISHED articles that do NOT have those tags.
    Step 3 — Exclude articles already viewed by the user.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Step 1: top tags for the (mock) current user
        cur.execute(
            """
            SELECT tag_id FROM user_preferences
            WHERE user_id = 1
            ORDER BY affinity_score DESC
            LIMIT 5
            """
        )
        top_tag_ids = [r["tag_id"] for r in cur.fetchall()]

        # Step 2 & 3: articles without those tags, not yet viewed
        if top_tag_ids:
            cur.execute(
                """
                SELECT a.article_id, a.title, a.author_id, a.view_count, a.status, a.published_at
                FROM articles a
                WHERE a.status = 'PUBLISHED'
                  AND a.article_id NOT IN (
                      SELECT article_id FROM article_tags WHERE tag_id = ANY(%s)
                  )
                  AND a.article_id NOT IN (
                      SELECT article_id FROM view_logs WHERE user_id = 1
                  )
                ORDER BY a.published_at DESC
                LIMIT 20
                """,
                (top_tag_ids,),
            )
        else:
            # No preferences yet — return latest published articles
            cur.execute(
                """
                SELECT article_id, title, author_id, view_count, status, published_at
                FROM articles WHERE status = 'PUBLISHED'
                ORDER BY published_at DESC LIMIT 20
                """
            )

        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
