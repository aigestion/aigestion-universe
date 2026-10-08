"""Tools para redes sociales."""

import os
from typing import Any


def post_to_tiktok(video_path: str, description: str) -> dict[str, Any]:
    """Publica en TikTok."""
    try:
        from tiktok_uploader import upload_video
        upload_video(video_path, description, cookies="cookies.txt")
        return {"success": True, "platform": "tiktok"}
    except Exception as e:
        return {"error": str(e)}


def post_to_twitter(text: str, media: str | None = None) -> dict[str, Any]:
    """Publica en Twitter/X."""
    try:
        import tweepy
        auth = tweepy.OAuthHandler(
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
        )
        auth.set_access_token(
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_SECRET"),
        )
        api = tweepy.API(auth)
        if media:
            api.update_status_with_media(text, media)
        else:
            api.update_status(text)
        return {"success": True, "platform": "twitter"}
    except Exception as e:
        return {"error": str(e)}


def post_to_instagram(media_path: str, caption: str) -> dict[str, Any]:
    """Publica en Instagram."""
    try:
        from instagrapi import Client
        cl = Client()
        cl.login(os.getenv("INSTAGRAM_USER"), os.getenv("INSTAGRAM_PASS"))
        cl.photo_upload(media_path, caption)
        return {"success": True, "platform": "instagram"}
    except Exception as e:
        return {"error": str(e)}


def get_twitter_trends(woeid: int = 1) -> list[dict[str, Any]]:
    """Obtiene tendencias de Twitter."""
    try:
        import tweepy
        auth = tweepy.OAuthHandler(
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
        )
        auth.set_access_token(
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_SECRET"),
        )
        api = tweepy.API(auth)
        trends = api.get_place_trends(woeid)
        return [{"name": t["name"], "volume": t["tweet_volume"]} for t in trends[0]["trends"]]
    except Exception as e:
        return [{"error": str(e)}]
