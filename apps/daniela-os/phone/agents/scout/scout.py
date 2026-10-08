"""Scout: Descubre información relevante automáticamente."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import Agent
from ..subagents.scout_subagents import RedditSubagent, RSSSubagent, YouTubeSubagent


class ScoutAgent(Agent):
    """Agente que descubre información relevante 24/7."""

    def __init__(self, config: dict | None = None):
        super().__init__("scout", config)
        self.videos_dir = Path(os.path.expanduser("~/videos/interesting"))
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.discovered_file = Path(__file__).parent / "discovered.json"
        self.discovered = self._load_discovered()

        # Subagentes
        self.add_subagent(YouTubeSubagent())
        self.add_subagent(RSSSubagent())
        self.add_subagent(RedditSubagent())

    def _load_discovered(self) -> dict:
        """Carga el historial de descubrimientos."""
        if self.discovered_file.exists():
            return json.loads(self.discovered_file.read_text())
        return {"videos": [], "links": [], "last_scan": None}

    def _save_discovered(self):
        """Guarda el historial."""
        self.discovered_file.write_text(json.dumps(self.discovered, indent=2))

    def scan_youtube(self, channels: list[str]) -> list[dict]:
        """Escanea canales de YouTube para videos nuevos."""
        results = []
        for channel in channels:
            try:
                cmd = [
                    "yt-dlp",
                    "--flat-playlist",
                    "--print",
                    "%(id)s %(title)s %(upload_date)s",
                    f"https://www.youtube.com/{channel}/videos",
                    "--playlist-end",
                    "5",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        parts = line.split(" ", 2)
                        if len(parts) >= 2:
                            results.append(
                                {
                                    "source": "youtube",
                                    "channel": channel,
                                    "id": parts[0],
                                    "title": parts[1],
                                    "url": f"https://youtube.com/watch?v={parts[0]}",
                                    "discovered": datetime.now().isoformat(),
                                }
                            )
            except Exception as e:
                self.log(f"Error escaneando {channel}: {e}", "error")
        return results

    def scan_rss(self, feeds: list[str]) -> list[dict]:
        """Escanea feeds RSS."""
        import feedparser

        results = []
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    results.append(
                        {
                            "source": "rss",
                            "feed": feed_url,
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "published": entry.get("published", ""),
                            "discovered": datetime.now().isoformat(),
                        }
                    )
            except Exception as e:
                self.log(f"Error escaneando RSS {feed_url}: {e}", "error")
        return results

    def download_video(self, video_id: str) -> str | None:
        """Descarga un video interesante."""
        output_path = self.videos_dir / f"{video_id}.mp4"
        if output_path.exists():
            return str(output_path)
        try:
            cmd = [
                "yt-dlp",
                "-f",
                "best[height<=720]",
                "-o",
                str(output_path),
                f"https://youtube.com/watch?v={video_id}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                return str(output_path)
        except Exception as e:
            self.log(f"Error descargando {video_id}: {e}", "error")
        return None

    def run(self) -> dict[str, Any]:
        """Ejecuta el ciclo de descubrimiento."""
        self.start()
        try:
            # Ejecutar subagentes
            subagent_results = self.run_subagents()

            # Escanear canales configurados
            channels = self.config.get("channels", [])
            videos = self.scan_youtube(channels)

            # Escanear RSS
            feeds = self.config.get("feeds", [])
            links = self.scan_rss(feeds)

            # Guardar descubrimientos
            self.discovered["videos"].extend(videos)
            self.discovered["links"].extend(links)
            self.discovered["last_scan"] = datetime.now().isoformat()
            self._save_discovered()

            # Actualizar métricas
            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = (
                f"{len(videos)} videos, {len(links)} links, {len(subagent_results)} subagentes"
            )
            self.save_metrics()

            self.log(f"Descubiertos: {len(videos)} videos, {len(links)} links")
            return {"videos": videos, "links": links, "subagents": subagent_results}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
