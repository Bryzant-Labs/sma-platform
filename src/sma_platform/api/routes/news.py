"""News & Discoveries API — research highlights, comments, and RSS feed."""

from __future__ import annotations

import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from ...core.database import execute, execute_script, fetch, fetchrow, fetchval
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Table creation SQL (idempotent)
# ---------------------------------------------------------------------------

_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS news_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'discovery' CHECK (category IN ('discovery', 'gpu_result', 'hypothesis', 'data_update', 'announcement')),
    tags TEXT[] DEFAULT '{}',
    author TEXT DEFAULT 'SMA Research Platform',
    featured BOOLEAN DEFAULT FALSE,
    published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_news_slug ON news_posts(slug);
CREATE INDEX IF NOT EXISTS idx_news_created ON news_posts(created_at DESC);

CREATE TABLE IF NOT EXISTS news_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES news_posts(id) ON DELETE CASCADE,
    author_name TEXT NOT NULL,
    author_email TEXT,
    content TEXT NOT NULL,
    approved BOOLEAN DEFAULT FALSE,
    spam_score NUMERIC DEFAULT 0,
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_comments_post ON news_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_approved ON news_comments(approved);
"""

_tables_ensured = False


async def _ensure_tables() -> None:
    global _tables_ensured
    if _tables_ensured:
        return
    try:
        await execute_script(_TABLES_SQL)
        _tables_ensured = True
    except Exception as e:
        logger.warning("_ensure_tables error (tables may already exist): %s", e)
        _tables_ensured = True


# ---------------------------------------------------------------------------
# Spam detection
# ---------------------------------------------------------------------------

SPAM_WORDS = {
    "buy now", "click here", "free money", "casino", "viagra", "crypto",
    "bitcoin", "earn money", "make money fast", "winner", "congratulations",
    "lottery", "cheap", "discount", "order now", "limited time",
    "act now", "subscribe", "unsubscribe", "pills", "weight loss",
}

# In-memory rate limiter: IP -> list of timestamps
_comment_rate_store: dict[str, list[float]] = defaultdict(list)
_COMMENT_RATE_LIMIT = 3
_COMMENT_RATE_WINDOW = 3600  # 1 hour


def _check_comment_rate(ip: str) -> bool:
    """Return True if comment is allowed, False if rate limited."""
    now = time.time()
    _comment_rate_store[ip] = [t for t in _comment_rate_store[ip] if now - t < _COMMENT_RATE_WINDOW]
    if len(_comment_rate_store[ip]) >= _COMMENT_RATE_LIMIT:
        return False
    _comment_rate_store[ip].append(now)
    return True


def _calculate_spam_score(text: str) -> float:
    """Simple spam scoring: 0.0 (clean) to 1.0 (spam)."""
    score = 0.0
    lower = text.lower()

    # Check URL count
    url_count = len(re.findall(r'https?://\S+', text))
    if url_count > 2:
        score += 0.3

    # All caps check (ignore short texts)
    if len(text) > 20 and text == text.upper():
        score += 0.2

    # Too short
    if len(text.strip()) < 10:
        score += 0.2

    # Common spam words
    for word in SPAM_WORDS:
        if word in lower:
            score += 0.1
            break  # Only count once

    # Repeated characters (e.g. "aaaaaaa" or "!!!!!!!")
    if re.search(r'(.)\1{5,}', text):
        score += 0.1

    return min(score, 1.0)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class CreatePostBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    slug: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: str = Field(default="discovery")
    tags: list[str] = Field(default_factory=list)
    author: str = Field(default="SMA Research Platform")
    featured: bool = Field(default=False)
    published: bool = Field(default=True)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', v):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens, no leading/trailing hyphens")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid = {"discovery", "gpu_result", "hypothesis", "data_update", "announcement"}
        if v not in valid:
            raise ValueError(f"Category must be one of: {', '.join(sorted(valid))}")
        return v


class UpdatePostBody(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    author: str | None = None
    featured: bool | None = None
    published: bool | None = None


class CommentBody(BaseModel):
    author_name: str = Field(..., min_length=1, max_length=200)
    author_email: str | None = Field(default=None, max_length=254)
    content: str = Field(..., min_length=1, max_length=5000)

    @field_validator("author_name")
    @classmethod
    def name_clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name is required")
        return v

    @field_validator("author_email")
    @classmethod
    def email_clean(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("content")
    @classmethod
    def content_clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Comment content is required")
        return v


# ---------------------------------------------------------------------------
# Helper: serialize rows
# ---------------------------------------------------------------------------

def _serialize_post(row: dict) -> dict:
    """Convert a DB row to a JSON-safe dict."""
    d = dict(row)
    for key in ("id", "created_at", "updated_at"):
        if key in d and d[key] is not None:
            d[key] = str(d[key])
    # tags may come as a list already or as a string
    if "tags" in d and isinstance(d["tags"], str):
        d["tags"] = [t.strip() for t in d["tags"].strip("{}").split(",") if t.strip()]
    return d


def _serialize_comment(row: dict) -> dict:
    d = dict(row)
    for key in ("id", "post_id", "created_at", "spam_score"):
        if key in d and d[key] is not None:
            d[key] = str(d[key])
    # Remove sensitive fields from public response
    d.pop("ip_address", None)
    d.pop("author_email", None)
    return d


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/news")
async def list_posts(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    category: str | None = Query(default=None),
    featured: bool | None = Query(default=None),
):
    """List published news posts, newest first, with pagination."""
    await _ensure_tables()

    conditions = ["p.published = TRUE"]
    params: list[Any] = []
    idx = 1

    if category:
        conditions.append(f"p.category = ${idx}")
        params.append(category)
        idx += 1

    if featured is not None:
        conditions.append(f"p.featured = ${idx}")
        params.append(featured)
        idx += 1

    where = " AND ".join(conditions)

    total = await fetchval(
        f"SELECT COUNT(*) FROM news_posts p WHERE {where}", *params
    )
    total = int(total) if total else 0

    offset = (page - 1) * per_page
    rows = await fetch(
        f"SELECT p.id, p.title, p.slug, p.content, p.category, p.tags, p.author, "
        f"p.featured, p.published, p.created_at, p.updated_at, "
        f"COALESCE(cc.cnt, 0) AS comment_count "
        f"FROM news_posts p "
        f"LEFT JOIN ("
        f"  SELECT post_id, COUNT(*) AS cnt FROM news_comments "
        f"  WHERE approved = TRUE GROUP BY post_id"
        f") cc ON cc.post_id = p.id "
        f"WHERE {where} "
        f"ORDER BY p.created_at DESC LIMIT ${idx} OFFSET ${idx + 1}",
        *params, per_page, offset,
    )

    posts = []
    for row in rows:
        post = _serialize_post(row)
        # Add excerpt (first 200 chars of content)
        raw_content = post.get("content", "")
        post["excerpt"] = raw_content[:200] + ("..." if len(raw_content) > 200 else "")
        post["comment_count"] = int(row["comment_count"]) if row["comment_count"] else 0
        posts.append(post)

    return {
        "posts": posts,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, -(-total // per_page)),  # ceil division
    }


@router.get("/news/feed/rss")
async def rss_feed():
    """Generate RSS 2.0 XML feed of published news posts."""
    await _ensure_tables()

    rows = await fetch(
        "SELECT title, slug, content, category, author, created_at "
        "FROM news_posts WHERE published = TRUE "
        "ORDER BY created_at DESC LIMIT 20"
    )

    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    items_xml = []
    for row in rows:
        pub_date = row["created_at"]
        if pub_date:
            try:
                if hasattr(pub_date, "strftime"):
                    pub_date = pub_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
                else:
                    pub_date = str(pub_date)
            except Exception:
                pub_date = str(pub_date)

        # Escape XML special characters
        title_escaped = (str(row["title"])
                         .replace("&", "&amp;")
                         .replace("<", "&lt;")
                         .replace(">", "&gt;"))
        content_escaped = (str(row["content"])
                           .replace("&", "&amp;")
                           .replace("<", "&lt;")
                           .replace(">", "&gt;"))

        items_xml.append(f"""    <item>
      <title>{title_escaped}</title>
      <link>https://sma-research.info/news/{row['slug']}</link>
      <guid isPermaLink="true">https://sma-research.info/news/{row['slug']}</guid>
      <description>{content_escaped[:500]}</description>
      <category>{row['category']}</category>
      <author>{row['author']}</author>
      <pubDate>{pub_date}</pubDate>
    </item>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>SMA Research Platform — News &amp; Discoveries</title>
    <link>https://sma-research.info/news</link>
    <description>Research highlights, computational discoveries, and platform updates from the SMA Research Platform.</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="https://sma-research.info/api/v2/news/feed/rss" rel="self" type="application/rss+xml"/>
{chr(10).join(items_xml)}
  </channel>
</rss>"""

    return Response(content=xml, media_type="application/rss+xml; charset=utf-8")


@router.get("/news/{slug}")
async def get_post(slug: str):
    """Get a single post by slug with approved comments."""
    await _ensure_tables()

    row = await fetchrow(
        "SELECT id, title, slug, content, category, tags, author, featured, published, created_at, updated_at "
        "FROM news_posts WHERE slug = $1",
        slug,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")

    post = _serialize_post(row)

    # Fetch approved comments
    comments = await fetch(
        "SELECT id, post_id, author_name, content, approved, created_at "
        "FROM news_comments WHERE post_id = $1::uuid AND approved = TRUE "
        "ORDER BY created_at ASC",
        row["id"],
    )
    post["comments"] = [_serialize_comment(c) for c in comments]

    return post


@router.post("/news", dependencies=[Depends(require_admin_key)])
async def create_post(body: CreatePostBody):
    """Create a new news post. Requires x-admin-key header."""
    await _ensure_tables()

    # Check slug uniqueness
    existing = await fetchval("SELECT COUNT(*) FROM news_posts WHERE slug = $1", body.slug)
    if existing and int(existing) > 0:
        raise HTTPException(status_code=409, detail=f"Slug '{body.slug}' already exists")

    post_id = await fetchval(
        "INSERT INTO news_posts (title, slug, content, category, tags, author, featured, published) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id",
        body.title, body.slug, body.content, body.category,
        body.tags, body.author, body.featured, body.published,
    )

    return {"id": str(post_id), "slug": body.slug, "status": "created"}


@router.put("/news/{slug}", dependencies=[Depends(require_admin_key)])
async def update_post(slug: str, body: UpdatePostBody):
    """Update a news post by slug. Requires x-admin-key header."""
    await _ensure_tables()

    existing = await fetchrow("SELECT id FROM news_posts WHERE slug = $1", slug)
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")

    updates: list[str] = []
    params: list[Any] = []
    idx = 1

    for field_name, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            updates.append(f"{field_name} = ${idx}")
            params.append(value)
            idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append(f"updated_at = NOW()")
    params.append(slug)

    await execute(
        f"UPDATE news_posts SET {', '.join(updates)} WHERE slug = ${idx}",
        *params,
    )

    return {"slug": slug, "status": "updated"}


@router.post("/news/{slug}/comments")
async def submit_comment(slug: str, body: CommentBody, request: Request):
    """Submit a comment on a news post. Public endpoint with spam detection."""
    await _ensure_tables()

    # Find the post
    post = await fetchrow("SELECT id FROM news_posts WHERE slug = $1 AND published = TRUE", slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Rate limit by IP
    client_ip = request.client.host if request.client else "unknown"
    if not _check_comment_rate(client_ip):
        raise HTTPException(status_code=429, detail="Too many comments. Please try again later.")

    # Spam detection
    spam_score = _calculate_spam_score(body.content)

    if spam_score > 0.7:
        # Silently reject — don't tell spammers why
        logger.info("Spam comment rejected (score=%.2f) from IP %s", spam_score, client_ip)
        return {"status": "submitted", "message": "Thank you for your comment. It will appear after review."}

    # Auto-approve if clean, hold for review otherwise
    auto_approve = spam_score < 0.3

    await execute(
        "INSERT INTO news_comments (post_id, author_name, author_email, content, approved, spam_score, ip_address) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7)",
        post["id"], body.author_name, body.author_email, body.content,
        auto_approve, spam_score, client_ip,
    )

    # Notify via Slack
    await _notify_comment_slack(slug, body, spam_score, auto_approve, client_ip)

    if auto_approve:
        return {"status": "approved", "message": "Comment published."}
    else:
        return {"status": "pending", "message": "Thank you for your comment. It will appear after review."}


async def _notify_comment_slack(slug: str, body: CommentBody, spam_score: float, approved: bool, ip: str) -> None:
    """Send comment notification to Slack."""
    from ...core.config import settings

    if not getattr(settings, "slack_bot_token", None) or not getattr(settings, "slack_channel_id", None):
        return

    status = "AUTO-APPROVED" if approved else "PENDING REVIEW"
    text = (
        f"*New Comment on SMA News*\n"
        f"*Post:* /news/{slug}\n"
        f"*From:* {body.author_name}"
        + (f" ({body.author_email})" if body.author_email else "")
        + f"\n*Status:* {status} (spam: {spam_score:.2f})\n"
        f"*IP:* {ip}\n---\n{body.content[:500]}"
    )

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                json={"channel": settings.slack_channel_id, "text": text},
            )
    except Exception as e:
        logger.error("Slack notification failed: %s", e)


@router.get("/news/admin/comments", dependencies=[Depends(require_admin_key)])
async def list_pending_comments(
    approved: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    """List comments for admin moderation. Requires x-admin-key header."""
    await _ensure_tables()

    if approved is None:
        rows = await fetch(
            "SELECT c.id, c.post_id, c.author_name, c.author_email, c.content, "
            "c.approved, c.spam_score, c.ip_address, c.created_at, p.title AS post_title, p.slug AS post_slug "
            "FROM news_comments c JOIN news_posts p ON c.post_id = p.id "
            "ORDER BY c.created_at DESC LIMIT $1",
            limit,
        )
    else:
        rows = await fetch(
            "SELECT c.id, c.post_id, c.author_name, c.author_email, c.content, "
            "c.approved, c.spam_score, c.ip_address, c.created_at, p.title AS post_title, p.slug AS post_slug "
            "FROM news_comments c JOIN news_posts p ON c.post_id = p.id "
            "WHERE c.approved = $1 "
            "ORDER BY c.created_at DESC LIMIT $2",
            approved, limit,
        )

    comments = []
    for row in rows:
        d = dict(row)
        for key in ("id", "post_id", "created_at", "spam_score"):
            if key in d and d[key] is not None:
                d[key] = str(d[key])
        comments.append(d)

    return {"comments": comments, "count": len(comments)}


@router.post("/news/admin/comments/{comment_id}/approve", dependencies=[Depends(require_admin_key)])
async def approve_comment(comment_id: str):
    """Approve a pending comment. Requires x-admin-key header."""
    await _ensure_tables()

    result = await execute(
        "UPDATE news_comments SET approved = TRUE WHERE id = $1::uuid",
        comment_id,
    )

    return {"comment_id": comment_id, "status": "approved"}


@router.post("/news/admin/comments/{comment_id}/reject", dependencies=[Depends(require_admin_key)])
async def reject_comment(comment_id: str):
    """Delete a spam/rejected comment. Requires x-admin-key header."""
    await _ensure_tables()

    await execute("DELETE FROM news_comments WHERE id = $1::uuid", comment_id)

    return {"comment_id": comment_id, "status": "deleted"}
