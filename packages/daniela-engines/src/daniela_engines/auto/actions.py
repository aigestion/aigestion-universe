"""
Action library (Ideas 31-40).
HTTP requests, file ops, DB queries, emails, notifications,
data transformation, image processing, git ops, shell commands, wait/delay.
"""

import csv
import io
import json
import logging
import os
import shutil
import smtplib
import sqlite3
import subprocess
import time
import uuid
import zipfile
from collections.abc import Callable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ActionType(Enum):
    HTTP_REQUEST = "http_request"
    FILE_OPS = "file_ops"
    DATABASE_QUERY = "database_query"
    SEND_EMAIL = "send_email"
    SEND_NOTIFICATION = "send_notification"
    DATA_TRANSFORM = "data_transform"
    IMAGE_PROCESS = "image_process"
    GIT_OPS = "git_ops"
    SHELL_COMMAND = "shell_command"
    WAIT_DELAY = "wait_delay"


class HttpRequestAction:
    """Idea 31: HTTP request action (GET/POST/PUT/DELETE)."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        import urllib.error
        import urllib.parse
        import urllib.request

        method = params.get("method", "GET").upper()
        url = params.get("url", "")
        headers = params.get("headers", {})
        body = params.get("body")
        timeout = params.get("timeout", 30)

        if body and isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        elif body and isinstance(body, str):
            body = body.encode("utf-8")

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                response_body = resp.read().decode("utf-8")
                try:
                    response_body = json.loads(response_body)
                except json.JSONDecodeError:
                    pass
                return {
                    "status_code": resp.status,
                    "headers": dict(resp.headers),
                    "body": response_body,
                }
        except urllib.error.HTTPError as e:
            return {"status_code": e.code, "error": str(e), "body": e.read().decode("utf-8", errors="ignore")}
        except Exception as e:
            return {"error": str(e)}


class FileOpsAction:
    """Idea 32: File operations (copy/move/delete/zip)."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        operation = params.get("operation", "copy")
        source = params.get("source", "")
        destination = params.get("destination", "")

        if operation == "copy":
            src = Path(source)
            dst = Path(destination)
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            elif src.is_dir():
                shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
            return {"operation": "copy", "source": source, "destination": destination, "status": "ok"}

        elif operation == "move":
            shutil.move(str(source), str(destination))
            return {"operation": "move", "source": source, "destination": destination, "status": "ok"}

        elif operation == "delete":
            target = Path(source)
            if target.is_file():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(str(target))
            return {"operation": "delete", "source": source, "status": "ok"}

        elif operation == "zip":
            with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zf:
                src_path = Path(source)
                if src_path.is_file():
                    zf.write(str(src_path), src_path.name)
                elif src_path.is_dir():
                    for file in src_path.rglob("*"):
                        if file.is_file():
                            zf.write(str(file), str(file.relative_to(src_path.parent)))
            return {"operation": "zip", "source": source, "destination": destination, "status": "ok"}

        elif operation == "unzip":
            with zipfile.ZipFile(source, "r") as zf:
                zf.extractall(destination)
            return {"operation": "unzip", "source": source, "destination": destination, "status": "ok"}

        elif operation == "read":
            content = Path(source).read_text(encoding=params.get("encoding", "utf-8"))
            return {"operation": "read", "content": content}

        elif operation == "write":
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
            Path(destination).write_text(params.get("content", ""),
                                         encoding=params.get("encoding", "utf-8"))
            return {"operation": "write", "destination": destination, "status": "ok"}

        elif operation == "list":
            entries = []
            for entry in Path(source).iterdir():
                entries.append({"name": entry.name, "is_dir": entry.is_dir(),
                                "size": entry.stat().st_size if entry.is_file() else 0})
            return {"operation": "list", "entries": entries}

        return {"error": f"Unknown operation: {operation}"}


class DatabaseQueryAction:
    """Idea 33: Database query action."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        db_path = params.get("db_path", "")
        query = params.get("query", "")
        query_params = params.get("params", [])
        fetch_all = params.get("fetch_all", True)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(query, query_params)
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall() if fetch_all else cursor.fetchone()
                result = [dict(row) for row in rows] if isinstance(rows, list) else (dict(rows) if rows else None)
                return {"status": "ok", "rows": result, "count": len(result) if isinstance(result, list) else 1}
            else:
                conn.commit()
                return {"status": "ok", "rows_affected": cursor.rowcount}
        except Exception as e:
            conn.rollback()
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()


class EmailSendAction:
    """Idea 34: Email send action (SMTP)."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        smtp_host = params.get("smtp_host", "smtp.gmail.com")
        smtp_port = params.get("smtp_port", 587)
        username = params.get("username", "")
        password = params.get("password", "")
        from_addr = params.get("from_addr", username)
        to_addrs = params.get("to_addrs", [])
        subject = params.get("subject", "")
        body = params.get("body", "")
        is_html = params.get("is_html", False)
        attachments = params.get("attachments", [])

        if isinstance(to_addrs, str):
            to_addrs = [to_addrs]

        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject

        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type, "utf-8"))

        for att_path in attachments:
            att_path = Path(att_path)
            if att_path.exists():
                with open(att_path, "rb") as f:
                    part = MIMEText(f.read(), "base64", "utf-8")
                    part.add_header("Content-Disposition", f"attachment; filename={att_path.name}")
                    msg.attach(part)

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(from_addr, to_addrs, msg.as_string())
            return {"status": "sent", "to": to_addrs, "subject": subject}
        except Exception as e:
            return {"status": "error", "error": str(e)}


class NotificationAction:
    """Idea 35: Notification action (push/webhook)."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        notify_type = params.get("type", "webhook")
        message = params.get("message", "")
        title = params.get("title", "Notification")

        if notify_type == "webhook":
            url = params.get("url", "")
            payload = {"title": title, "message": message, "timestamp": time.time(),
                       **params.get("extra", {})}
            try:
                import urllib.request
                req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return {"status": "sent", "response": resp.status}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        elif notify_type == "console":
            logger.info(f"[{title}] {message}")
            return {"status": "logged", "message": message}

        return {"status": "unknown_type", "type": notify_type}


class DataTransformAction:
    """Idea 36: Data transformation (JSON/XML/CSV)."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        input_format = params.get("input_format", "json")
        output_format = params.get("output_format", "json")
        data = params.get("data")
        input_path = params.get("input_path")
        output_path = params.get("output_path")

        if input_path:
            input_path = Path(input_path)
            if input_format == "json":
                data = json.loads(input_path.read_text())
            elif input_format == "csv":
                with open(input_path) as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
            elif input_format == "text":
                data = input_path.read_text()

        if output_format == "json":
            result = json.dumps(data, indent=2, default=str)
        elif output_format == "csv" and isinstance(data, list) and data:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            result = output.getvalue()
        elif output_format == "text" and isinstance(data, dict):
            result = "\n".join(f"{k}: {v}" for k, v in data.items())
        else:
            result = str(data)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(result)

        return {"format": output_format, "content": result if len(str(result)) < 10000 else f"[{len(str(result))} chars]"}


class ImageProcessAction:
    """Idea 37: Image processing action (resize/optimize)."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        operation = params.get("operation", "info")
        source = params.get("source", "")
        destination = params.get("destination", "")
        width = params.get("width")
        height = params.get("height")
        quality = params.get("quality", 85)

        try:
            from PIL import Image
        except ImportError:
            return {"error": "Pillow not installed. pip install Pillow"}

        src_path = Path(source)

        if operation == "info":
            with Image.open(src_path) as img:
                return {"width": img.width, "height": img.height, "format": img.format,
                        "mode": img.mode, "size_bytes": src_path.stat().st_size}

        elif operation == "resize":
            with Image.open(src_path) as img:
                new_size = (width or img.width, height or img.height)
                resized = img.resize(new_size, Image.Resampling.LANCZOS)
                dst = Path(destination) if destination else src_path.with_suffix(".resized.jpg")
                resized.save(str(dst), quality=quality)
                return {"status": "resized", "destination": str(dst),
                        "new_size": list(new_size)}

        elif operation == "optimize":
            with Image.open(src_path) as img:
                dst = Path(destination) if destination else src_path.with_suffix(".opt.jpg")
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(str(dst), optimize=True, quality=quality)
                original_size = src_path.stat().st_size
                optimized_size = Path(dst).stat().st_size
                return {"status": "optimized", "destination": str(dst),
                        "original_size": original_size, "optimized_size": optimized_size,
                        "reduction_pct": round((1 - optimized_size / original_size) * 100, 1)}

        elif operation == "convert":
            fmt = params.get("format", "PNG")
            with Image.open(src_path) as img:
                dst = Path(destination) if destination else src_path.with_suffix(f".{fmt.lower()}")
                img.save(str(dst), format=fmt)
                return {"status": "converted", "destination": str(dst), "format": fmt}

        return {"error": f"Unknown operation: {operation}"}


class GitOpsAction:
    """Idea 38: Git operations (commit/push/tag)."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        operation = params.get("operation", "status")
        repo_path = params.get("repo_path", ".")
        command = params.get("command", "")

        def run_git(*args):
            result = subprocess.run(
                ["git"] + list(args), cwd=repo_path,
                capture_output=True, text=True, timeout=60,
            )
            return {"returncode": result.returncode, "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip()}

        if operation == "status":
            return run_git("status", "--porcelain")
        elif operation == "commit":
            message = params.get("message", "Auto commit")
            run_git("add", "-A")
            return run_git("commit", "-m", message)
        elif operation == "push":
            remote = params.get("remote", "origin")
            branch = params.get("branch", "main")
            return run_git("push", remote, branch)
        elif operation == "pull":
            remote = params.get("remote", "origin")
            return run_git("pull", remote)
        elif operation == "tag":
            tag_name = params.get("tag", f"v{uuid.uuid4().hex[:8]}")
            message = params.get("message", "")
            if message:
                return run_git("tag", "-a", tag_name, "-m", message)
            return run_git("tag", tag_name)
        elif operation == "log":
            count = params.get("count", 10)
            return run_git("log", "--oneline", f"-{count}")
        elif operation == "branch":
            return run_git("branch", "-a")
        elif operation == "diff":
            return run_git("diff")
        elif operation == "custom":
            args = command.split()
            return run_git(*args)
        return {"error": f"Unknown git operation: {operation}"}


class ShellCommandAction:
    """Idea 39: Shell command execution."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        command = params.get("command", "")
        cwd = params.get("cwd")
        timeout = params.get("timeout", 60)
        env = params.get("env", {})
        shell = params.get("shell", True)

        full_env = {**os.environ, **env}
        try:
            result = subprocess.run(
                command, shell=shell, cwd=cwd, capture_output=True,
                text=True, timeout=timeout, env=full_env,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout}s", "returncode": -1}
        except Exception as e:
            return {"error": str(e), "returncode": -1}


class WaitDelayAction:
    """Idea 40: Wait/delay action."""

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        seconds = params.get("seconds", 1)
        milliseconds = params.get("milliseconds", 0)
        total = seconds + (milliseconds / 1000)
        time.sleep(total)
        return {"waited": total, "unit": "seconds"}


class ActionLibrary:
    """Action library (Ideas 31-40)."""

    def __init__(self):
        self.handlers: dict[str, Callable] = {
            "http_request": HttpRequestAction().execute,
            "file_ops": FileOpsAction().execute,
            "database_query": DatabaseQueryAction().execute,
            "send_email": EmailSendAction().execute,
            "send_notification": NotificationAction().execute,
            "data_transform": DataTransformAction().execute,
            "image_process": ImageProcessAction().execute,
            "git_ops": GitOpsAction().execute,
            "shell_command": ShellCommandAction().execute,
            "wait_delay": WaitDelayAction().execute,
        }
        self._execution_log: list[dict[str, Any]] = []

    def register(self, action_type: str, handler: Callable):
        self.handlers[action_type] = handler

    def execute(self, action_type: str, params: dict[str, Any]) -> dict[str, Any]:
        handler = self.handlers.get(action_type)
        if not handler:
            return {"error": f"Unknown action type: {action_type}"}
        start = time.time()
        try:
            result = handler(params)
        except Exception as e:
            result = {"error": str(e)}
        elapsed = time.time() - start
        entry = {"action_type": action_type, "result": result,
                 "elapsed_ms": round(elapsed * 1000, 2), "timestamp": time.time()}
        self._execution_log.append(entry)
        return result

    def list_actions(self) -> list[str]:
        return list(self.handlers.keys())

    def get_log(self, action_type: str | None = None, limit: int = 100) -> list[dict]:
        log = self._execution_log
        if action_type:
            log = [e for e in log if e.get("action_type") == action_type]
        return log[-limit:]
