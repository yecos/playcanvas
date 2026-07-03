"""
analytics_collector.py - Recolecta metricas de engagement de cada post

Conecta con APIs oficiales de cada plataforma para obtener:
  - Instagram: likes, comments, saves, reach, impressions
  - Twitter/X: likes, retweets, replies, impressions
  - Facebook: reactions, comments, shares
  - Pinterest: saves, clicks, impressions
  - YouTube: views, likes, comments

Las metricas se guardan en SQLite (analytics.db) junto con el post_id,
prompt, workflow usado, fecha de publicacion. Esto permite analisis
posterior de que prompts/workflows generan mas engagement.

Uso:
    # Recolectar metricas de todos los posts publicados
    python analytics_collector.py collect

    # Ver resumen
    python analytics_collector.py summary

    # Top 10 posts por engagement
    python analytics_collector.py top
"""
import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, banner, ROOT_DIR

DB_PATH = ROOT_DIR / "analytics.db"


# ============================================================
# Database
# ============================================================

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            external_id TEXT,
            prompt TEXT,
            workflow TEXT,
            caption TEXT,
            published_at TIMESTAMP,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            reach INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0,
            raw_data TEXT,
            UNIQUE(post_id, platform)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_post ON analytics(post_id)
    """)
    conn.commit()
    conn.close()


# ============================================================
# Platform collectors
# ============================================================

def collect_instagram(post_id: str, external_id: str) -> Dict:
    """Obtiene metricas de un post de Instagram."""
    try:
        from instagrapi import Client
    except ImportError:
        return {"error": "instagrapi not installed"}

    try:
        session_file = ROOT_DIR / "ig_session.json"
        cl = Client()
        if session_file.exists():
            cl.load_settings(str(session_file))

        media_id = external_id
        media_info = cl.media_info(media_id)

        return {
            "likes": media_info.like_count or 0,
            "comments": media_info.comment_count or 0,
            "saves": 0,  # requiere Graph API
            "impressions": 0,
            "reach": 0,
            "raw_data": str(media_info)[:500]
        }
    except Exception as e:
        return {"error": str(e)}


def collect_twitter(post_id: str, external_id: str) -> Dict:
    """Obtiene metricas de un tweet."""
    try:
        import tweepy
    except ImportError:
        return {"error": "tweepy not installed"}

    try:
        client = tweepy.Client(
            bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"),
            consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
            consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
            access_token=os.environ["TWITTER_ACCESS_TOKEN"],
            access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        )
        # Get tweet with public metrics
        tweet = client.get_tweet(
            int(external_id),
            tweet_fields=["public_metrics"]
        )
        if not tweet.data:
            return {"error": "Tweet no encontrado"}

        metrics = tweet.data.public_metrics or {}
        return {
            "likes": metrics.get("like_count", 0),
            "comments": metrics.get("reply_count", 0),
            "shares": metrics.get("retweet_count", 0),
            "impressions": metrics.get("impression_count", 0),
            "raw_data": str(metrics)[:500]
        }
    except Exception as e:
        return {"error": str(e)}


def collect_facebook(post_id: str, external_id: str) -> Dict:
    """Obtiene metricas de un post de Facebook Page."""
    try:
        import facebook
    except ImportError:
        return {"error": "facebook-sdk not installed"}

    try:
        graph = facebook.GraphAPI(access_token=os.environ["FB_PAGE_TOKEN"])
        # Pedir metricas publicas
        post_data = graph.get_object(
            id=external_id,
            fields="message,created_time,likes.summary(true),comments.summary(true),shares"
        )

        return {
            "likes": post_data.get("likes", {}).get("summary", {}).get("total_count", 0),
            "comments": post_data.get("comments", {}).get("summary", {}).get("total_count", 0),
            "shares": post_data.get("shares", {}).get("count", 0),
            "raw_data": str(post_data)[:500]
        }
    except Exception as e:
        return {"error": str(e)}


def collect_pinterest(post_id: str, external_id: str) -> Dict:
    """Pinterest metrics requieren Business account + API v5."""
    return {"error": "Pinterest analytics requiere API v5 Business (no implementado)"}


def collect_youtube(post_id: str, external_id: str) -> Dict:
    """Obtiene metricas de un video de YouTube."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return {"error": "google-api deps not installed"}

    try:
        token_file = ROOT_DIR / "youtube_token.json"
        if not token_file.exists():
            return {"error": "YouTube no autenticado (falta youtube_token.json)"}

        creds = Credentials.from_authorized_user_file(
            str(token_file),
            ["https://www.googleapis.com/auth/youtube.readonly"]
        )
        yt = build("youtube", "v3", credentials=creds)

        # Obtener statistics
        response = yt.videos().list(
            part="statistics",
            id=external_id
        ).execute()

        if not response.get("items"):
            return {"error": "Video no encontrado"}

        stats = response["items"][0].get("statistics", {})
        return {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "raw_data": str(stats)[:500]
        }
    except Exception as e:
        return {"error": str(e)}


COLLECTORS = {
    "instagram": collect_instagram,
    "twitter":   collect_twitter,
    "facebook":  collect_facebook,
    "pinterest": collect_pinterest,
    "youtube":   collect_youtube,
    # tiktok no tiene API publica de analytics
}


# ============================================================
# Main collection logic
# ============================================================

def collect_all():
    """Recolecta metricas de todos los posts publicados."""
    init_db()
    cal_file = ROOT_DIR / "config" / "calendar.json"
    if not cal_file.exists():
        error("calendar.json no existe")
        return

    with open(cal_file, "r", encoding="utf-8") as f:
        cal = json.load(f)

    collected = 0
    errors = 0

    for post in cal.get("posts", []):
        if post.get("status") not in ("published", "partial"):
            continue

        post_id = post["id"]
        results = post.get("publish_results", {})

        for platform, result in results.items():
            if not result.get("success"):
                continue

            external_id = result.get("media_id") or result.get("tweet_id") or \
                          result.get("post_id") or result.get("video_id")

            if not external_id:
                continue

            collector = COLLECTORS.get(platform)
            if not collector:
                continue

            info(f"  {post_id} / {platform} ({external_id})...")
            metrics = collector(post_id, str(external_id))

            if "error" in metrics:
                warn(f"    {metrics['error']}")
                errors += 1
                continue

            # Calcular engagement rate
            engagement = (metrics.get("likes", 0) +
                          metrics.get("comments", 0) +
                          metrics.get("shares", 0) +
                          metrics.get("saves", 0))
            impressions = metrics.get("impressions", 0) or metrics.get("views", 0)
            er = (engagement / impressions * 100) if impressions > 0 else 0

            # Guardar en DB
            conn = sqlite3.connect(str(DB_PATH))
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO analytics
                    (post_id, platform, external_id, prompt, workflow, caption,
                     published_at, collected_at, likes, comments, shares, saves,
                     impressions, reach, views, engagement_rate, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_id, platform, str(external_id),
                    post.get("prompt", "")[:500],
                    post.get("workflow", ""),
                    post.get("caption", "")[:500],
                    post.get("published_at"),
                    datetime.now().isoformat(),
                    metrics.get("likes", 0),
                    metrics.get("comments", 0),
                    metrics.get("shares", 0),
                    metrics.get("saves", 0),
                    metrics.get("impressions", 0),
                    metrics.get("reach", 0),
                    metrics.get("views", 0),
                    er,
                    metrics.get("raw_data", "")[:1000]
                ))
                conn.commit()
                collected += 1
                ok(f"    likes={metrics.get('likes', 0)} "
                   f"comments={metrics.get('comments', 0)} "
                   f"ER={er:.1f}%")
            finally:
                conn.close()

    banner("RESUMEN ANALYTICS")
    ok(f"Posts procesados: {collected}")
    if errors:
        warn(f"Errores: {errors}")


def print_summary():
    """Muestra resumen agregado."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            platform,
            COUNT(*) as n_posts,
            SUM(likes) as total_likes,
            SUM(comments) as total_comments,
            SUM(shares) as total_shares,
            AVG(engagement_rate) as avg_er
        FROM analytics
        GROUP BY platform
    """).fetchall()

    banner("RESUMEN DE ANALYTICS")
    if not rows:
        info("No hay datos aun. Ejecuta: python analytics_collector.py collect")
        return

    cprint(f"  {'Plataforma':15} {'Posts':8} {'Likes':10} {'Comments':10} {'Shares':10} {'ER%':8}",
           '\033[1m')
    for r in rows:
        cprint(f"  {r['platform']:15} {r['n_posts']:8} {r['total_likes'] or 0:10} "
               f"{r['total_comments'] or 0:10} {r['total_shares'] or 0:10} "
               f"{(r['avg_er'] or 0):.2f}%",
               '\033[96m')
    conn.close()


def print_top(n: int = 10):
    """Top N posts por engagement rate."""
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT post_id, platform, prompt, workflow,
               likes, comments, impressions, views, engagement_rate
        FROM analytics
        WHERE engagement_rate > 0
        ORDER BY engagement_rate DESC
        LIMIT ?
    """, (n,)).fetchall()

    banner(f"TOP {n} POSTS POR ENGAGEMENT")
    if not rows:
        info("No hay datos aun.")
        return

    for i, r in enumerate(rows, 1):
        cprint(f"\n  #{i} - {r['post_id']} [{r['platform']}] "
               f"ER={r['engagement_rate']:.2f}%", '\033[1m')
        cprint(f"     Workflow: {r['workflow']}", '\033[90m')
        cprint(f"     Prompt: {r['prompt'][:80]}...", '\033[90m')
        cprint(f"     Likes: {r['likes']} | Comments: {r['comments']} | "
               f"Views: {r['views'] or r['impressions']}", '\033[90m')

    conn.close()


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Analytics collector")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("collect", help="Recolectar metricas de todos los posts")
    sub.add_parser("summary", help="Resumen agregado por plataforma")
    p_top = sub.add_parser("top", help="Top N posts por engagement")
    p_top.add_argument("--n", type=int, default=10)

    args = parser.parse_args()

    if args.cmd == "collect":
        collect_all()
    elif args.cmd == "summary":
        print_summary()
    elif args.cmd == "top":
        print_top(args.n)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
