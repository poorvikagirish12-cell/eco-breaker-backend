from fastapi import APIRouter, Depends
from typing import List
import schemas
from database import get_connection
from security import get_current_user_id

router = APIRouter(prefix="/api/feed", tags=["Feed"])


@router.get("", response_model=List[schemas.ArticleListResponse])
def get_contrarian_feed(
    current_user_id: int = Depends(get_current_user_id),
    diversity_score: int = 50
):
    """
    26. Fetch personalized contrarian feed with diversity slider.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Step 1: top tags for the current user
        cur.execute(
            """
            SELECT tag_id FROM user_preferences
            WHERE user_id = %s
            ORDER BY affinity_score DESC
            LIMIT 5
            """,
            (current_user_id,)
        )
        top_tag_ids = [r["tag_id"] for r in cur.fetchall()]

        # Step 2 & 3: articles without those tags, not yet viewed
        if top_tag_ids:
            cur.execute(
                """
                SELECT a.article_id, a.title, a.content, a.author_id, a.view_count, a.status, a.published_at,
                       u.username AS author_name, u.is_verified_author
                FROM articles a
                JOIN users u ON a.author_id = u.user_id
                WHERE a.status = 'PUBLISHED'
                  AND a.article_id NOT IN (
                      SELECT article_id FROM article_tags WHERE tag_id = ANY(%s)
                  )
                  AND a.article_id NOT IN (
                      SELECT article_id FROM view_logs WHERE user_id = %s
                  )
                ORDER BY a.published_at DESC
                LIMIT 20
                """,
                (top_tag_ids, current_user_id),
            )
        else:
            # No preferences yet — return latest published articles
            cur.execute(
                """
                SELECT a.article_id, a.title, a.content, a.author_id, a.view_count, a.status, a.published_at,
                       u.username AS author_name, u.is_verified_author
                FROM articles a
                JOIN users u ON a.author_id = u.user_id
                WHERE a.status = 'PUBLISHED'
                ORDER BY a.published_at DESC LIMIT 20
                """
            )

        results = [dict(r) for r in cur.fetchall()]
        
        # Add mock AI data and handle diversity filtering manually for now
        # High diversity_score (e.g. 100) -> highly contrarian. Low (e.g. 0) -> highly comfortable.
        # Since the original query was 100% contrarian, we could blend it, but for now we just append the mock data
        for res in results:
            res["ai_summary"] = [
                "The core premise challenges mainstream assumptions.",
                "It highlights systemic inefficiencies often ignored.",
                "Dismantling popular myths is the first step toward genuine progress."
            ]
            res["credibility_score"] = 85.5 + (res["article_id"] % 10)  # mock dynamic score
            
        return results
    finally:
        conn.close()

