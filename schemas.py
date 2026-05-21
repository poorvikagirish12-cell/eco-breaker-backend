from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# ================================================================================
# USER SCHEMAS
# ================================================================================
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    user_id: int
    is_verified_author: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# ================================================================================
# AUTHOR SCHEMAS
# ================================================================================
class AuthorApplicationCreate(BaseModel):
    application_text: str

class AuthorApplicationResponse(BaseModel):
    application_id: int
    user_id: int
    application_text: str
    status: str
    applied_at: datetime

# ================================================================================
# TAG SCHEMAS
# ================================================================================
class TagCreate(BaseModel):
    name: str

class TagResponse(BaseModel):
    tag_id: int
    name: str
    created_at: datetime

class TagAffinity(BaseModel):
    name: str
    affinity_score: int

class TagUsage(BaseModel):
    name: str
    usage_count: int

# ================================================================================
# ARTICLE SCHEMAS
# ================================================================================
class ArticleBase(BaseModel):
    title: str
    content: str

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class ArticleResponse(ArticleBase):
    article_id: int
    author_id: int
    view_count: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

class ArticleListResponse(BaseModel):
    article_id: int
    title: str
    author_id: int
    view_count: int
    status: str
    published_at: Optional[datetime] = None

# ================================================================================
# INTERACTION SCHEMAS
# ================================================================================
class ViewInteraction(BaseModel):
    view_duration_seconds: int

class HistoryResponse(BaseModel):
    article_id: int
    title: str
    viewed_at: datetime
    view_duration_seconds: int

# ================================================================================
# ADMIN / REPORTS SCHEMAS
# ================================================================================
class CountReport(BaseModel):
    count: int
