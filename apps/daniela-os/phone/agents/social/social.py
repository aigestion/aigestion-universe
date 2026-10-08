"""Social: Publica contenido en redes sociales automáticamente."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import Agent


class SocialAgent(Agent):
    """Agente que publica en redes sociales."""

    def __init__(self, config: dict | None = None):
        super().__init__("social", config)
        self.posts_file = Path(__file__).parent / "posts.json"
        self.posts = self._load_posts()

    def _load_posts(self) -> dict:
        if self.posts_file.exists():
            return json.loads(self.posts_file.read_text())
        return {"posts": [], "last_post": None}

    def _save_posts(self):
        self.posts_file.write_text(json.dumps(self.posts, indent=2))

    def post_tiktok(self, video_path: str, description: str) -> bool:
        """Publica en TikTok."""
        try:
            from tiktok_uploader import upload_video

            upload_video(video_path, description, cookies="cookies.txt")
            return True
        except Exception as e:
            self.log(f"Error publicando en TikTok: {e}", "error")
            return False

    def post_twitter(self, text: str, media: str | None = None) -> bool:
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
            return True
        except Exception as e:
            self.log(f"Error publicando en Twitter: {e}", "error")
            return False

    def post_instagram(self, media_path: str, caption: str) -> bool:
        """Publica en Instagram."""
        try:
            from instagrapi import Client

            cl = Client()
            cl.login(os.getenv("INSTAGRAM_USER"), os.getenv("INSTAGRAM_PASS"))
            cl.photo_upload(media_path, caption)
            return True
        except Exception as e:
            self.log(f"Error publicando en Instagram: {e}", "error")
            return False

    def run(self) -> dict[str, Any]:
        """Ejecuta el ciclo de publicación."""
        self.start()
        try:
            # Buscar videos pendientes de publicar
            output_dir = Path(os.path.expanduser("~/videos/output"))
            pending = list(output_dir.glob("*.mp4"))[:5]

            published = []
            for video_path in pending:
                caption = f"🎬 {video_path.stem}\n\n#viral #tiktok #ai"
                if self.post_tiktok(str(video_path), caption):
                    published.append({"platform": "tiktok", "file": str(video_path)})

            self.posts["posts"].extend(published)
            self.posts["last_post"] = datetime.now().isoformat()
            self._save_posts()

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(published)} posts"
            self.save_metrics()
            self.log(f"Publicados: {len(published)} posts")
            return {"published": published}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
