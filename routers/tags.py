from fastapi import APIRouter, HTTPException, status
from typing import List
import schemas
from database import get_connection

router = APIRouter(prefix="/api/tags", tags=["Tags"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.TagResponse)
def create_tag(tag: schemas.TagCreate):
    """19. Admin creates a new global tag"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tags (name) VALUES (%s) RETURNING tag_id, name, created_at",
            (tag.name,),
        )
        conn.commit()
        return dict(cur.fetchone())
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("", response_model=List[schemas.TagResponse])
def list_tags():
    """22. View the complete list of all available tags"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT tag_id, name, created_at FROM tags ORDER BY name ASC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.put("/{tag_id}", response_model=schemas.TagResponse)
def rename_tag(tag_id: int, tag: schemas.TagCreate):
    """20. Admin renames an existing tag"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tags SET name=%s WHERE tag_id=%s RETURNING tag_id, name, created_at",
            (tag.name, tag_id),
        )
        conn.commit()
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tag not found")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int):
    """21. Admin deletes a tag"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM tags WHERE tag_id=%s", (tag_id,))
        conn.commit()
    finally:
        conn.close()
