"""
External integrations (Ideas 41-50).
GitHub, Slack, Telegram, Google Calendar, Jira, Docker, Cloud storage,
Stripe, CRM, and Analytics integrations.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    GITHUB = "github"
    SLACK = "slack"
    TELEGRAM = "telegram"
    GOOGLE_CALENDAR = "google_calendar"
    JIRA = "jira"
    DOCKER = "docker"
    CLOUD_STORAGE = "cloud_storage"
    STRIPE = "stripe"
    CRM = "crm"
    ANALYTICS = "analytics"


@dataclass
class IntegrationConfig:
    integration_type: IntegrationType
    api_key: str | None = None
    base_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["integration_type"] = self.integration_type.value
        if d.get("api_key"):
            d["api_key"] = d["api_key"][:8] + "..." if len(d["api_key"]) > 8 else "***"
        return d


from dataclasses import asdict


class GitHubIntegration:
    """Idea 41: GitHub integration (PR, issues, releases)."""

    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url

    def _request(self, method: str, endpoint: str, data: dict | None = None) -> dict:
        import urllib.error
        import urllib.request
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "aig-AutoEngine",
        }
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {"error": e.code, "message": e.read().decode(errors="ignore")[:500]}

    def list_repos(self, org: str | None = None) -> dict:
        endpoint = f"/orgs/{org}/repos" if org else "/user/repos"
        return self._request("GET", endpoint)

    def create_issue(self, owner: str, repo: str, title: str,
                     body: str = "", labels: list[str] | None = None) -> dict:
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        return self._request("POST", f"/repos/{owner}/{repo}/issues", payload)

    def list_issues(self, owner: str, repo: str, state: str = "open") -> dict:
        return self._request("GET", f"/repos/{owner}/{repo}/issues?state={state}")

    def create_pull_request(self, owner: str, repo: str, title: str,
                            head: str, base: str, body: str = "") -> dict:
        return self._request("POST", f"/repos/{owner}/{repo}/pulls",
                             {"title": title, "head": head, "base": base, "body": body})

    def create_release(self, owner: str, repo: str, tag_name: str,
                       name: str, body: str = "") -> dict:
        return self._request("POST", f"/repos/{owner}/{repo}/releases",
                             {"tag_name": tag_name, "name": name, "body": body})

    def list_workflow_runs(self, owner: str, repo: str) -> dict:
        return self._request("GET", f"/repos/{owner}/{repo}/actions/runs")


class SlackIntegration:
    """Idea 42: Slack integration (messages, channels)."""

    def __init__(self, bot_token: str, webhook_url: str | None = None):
        self.bot_token = bot_token
        self.webhook_url = webhook_url

    def send_message(self, channel: str, text: str, blocks: list | None = None) -> dict:
        import urllib.request
        payload = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.bot_token}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def send_webhook(self, text: str, channel: str | None = None) -> dict:
        import urllib.request
        payload = {"text": text}
        if channel:
            payload["channel"] = channel
        req = urllib.request.Request(
            self.webhook_url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {"status": resp.status}
        except Exception as e:
            return {"error": str(e)}

    def list_channels(self) -> dict:
        import urllib.request
        req = urllib.request.Request(
            "https://slack.com/api/conversations.list",
            headers={"Authorization": f"Bearer {self.bot_token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}


class TelegramIntegration:
    """Idea 43: Telegram integration (bot API)."""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, chat_id: str, text: str,
                     parse_mode: str | None = None) -> dict:
        import urllib.request
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        req = urllib.request.Request(
            f"{self.base_url}/sendMessage",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def get_updates(self, offset: int | None = None, limit: int = 100) -> dict:
        import urllib.request
        params = f"?limit={limit}"
        if offset:
            params += f"&offset={offset}"
        req = urllib.request.Request(f"{self.base_url}/getUpdates{params}")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def get_me(self) -> dict:
        import urllib.request
        req = urllib.request.Request(f"{self.base_url}/getMe")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}


class GoogleCalendarIntegration:
    """Idea 44: Google Calendar integration."""

    def __init__(self, credentials_path: str = ""):
        self.credentials_path = credentials_path
        self.base_url = "https://www.googleapis.com/calendar/v3"

    def list_calendars(self, access_token: str) -> dict:
        import urllib.request
        req = urllib.request.Request(
            f"{self.base_url}/users/me/calendarList",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def list_events(self, access_token: str, calendar_id: str = "primary",
                    max_results: int = 10) -> dict:
        import urllib.request
        now = datetime.utcnow().isoformat() + "Z"
        req = urllib.request.Request(
            f"{self.base_url}/calendars/{calendar_id}/events?timeMin={now}&maxResults={max_results}&singleEvents=True&orderBy=startTime",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def create_event(self, access_token: str, calendar_id: str, summary: str,
                     start_time: str, end_time: str, description: str = "",
                     attendees: list[str] | None = None) -> dict:
        import urllib.request
        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_time, "timeZone": "UTC"},
            "end": {"dateTime": end_time, "timeZone": "UTC"},
        }
        if attendees:
            event["attendees"] = [{"email": a} for a in attendees]
        req = urllib.request.Request(
            f"{self.base_url}/calendars/{calendar_id}/events",
            data=json.dumps(event).encode(),
            headers={"Authorization": f"Bearer {access_token}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}


class JiraIntegration:
    """Idea 45: Jira integration (create/update issues)."""

    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (email, api_token)

    def _request(self, method: str, endpoint: str, data: dict | None = None) -> dict:
        import base64
        import urllib.request
        url = f"{self.base_url}/rest/api/3{endpoint}"
        auth_str = base64.b64encode(f"{self.auth[0]}:{self.auth[1]}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_str}",
                   "Content-Type": "application/json"}
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def create_issue(self, project_key: str, summary: str, issue_type: str = "Task",
                     description: str = "", priority: str = "Medium") -> dict:
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
            }
        }
        if description:
            payload["fields"]["description"] = {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph",
                             "content": [{"type": "text", "text": description}]}],
            }
        return self._request("POST", "/issue", payload)

    def update_issue(self, issue_key: str, fields: dict[str, Any]) -> dict:
        return self._request("PUT", f"/issue/{issue_key}", {"fields": fields})

    def get_issue(self, issue_key: str) -> dict:
        return self._request("GET", f"/issue/{issue_key}")

    def list_issues(self, jql: str = "assignee = currentUser()") -> dict:
        import urllib.parse
        encoded_jql = urllib.parse.quote(jql)
        return self._request("GET", f"/search?jql={encoded_jql}")

    def add_comment(self, issue_key: str, body: str) -> dict:
        return self._request("POST", f"/issue/{issue_key}/comment",
                             {"body": {"type": "doc", "version": 1,
                                       "content": [{"type": "paragraph",
                                                     "content": [{"type": "text", "text": body}]}]}})


class DockerIntegration:
    """Idea 46: Docker integration (build/deploy)."""

    def __init__(self, docker_host: str = "unix:///var/run/docker.sock"):
        self.docker_host = docker_host

    def _run_cmd(self, args: list[str]) -> dict:
        import subprocess
        result = subprocess.run(["docker"] + args, capture_output=True, text=True, timeout=120)
        return {"returncode": result.returncode, "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()}

    def build(self, path: str = ".", tag: str = "latest", dockerfile: str = "Dockerfile") -> dict:
        return self._run_cmd(["build", "-t", tag, "-f", dockerfile, path])

    def run(self, image: str, name: str | None = None, detach: bool = True,
            ports: dict[str, str] | None = None, env: dict[str, str] | None = None) -> list[str]:
        args = ["run"]
        if detach:
            args.append("-d")
        if name:
            args.extend(["--name", name])
        if ports:
            for host_port, container_port in ports.items():
                args.extend(["-p", f"{host_port}:{container_port}"])
        if env:
            for k, v in env.items():
                args.extend(["-e", f"{k}={v}"])
        args.append(image)
        return self._run_cmd(args)

    def stop(self, container: str) -> dict:
        return self._run_cmd(["stop", container])

    def remove(self, container: str) -> dict:
        return self._run_cmd(["rm", container])

    def list_containers(self, all_containers: bool = True) -> dict:
        args = ["ps"]
        if all_containers:
            args.append("-a")
        args.extend(["--format", "{{json .}}"])
        return self._run_cmd(args)

    def pull(self, image: str) -> dict:
        return self._run_cmd(["pull", image])

    def images(self) -> dict:
        return self._run_cmd(["images", "--format", "{{json .}}"])


class CloudStorageIntegration:
    """Idea 47: Cloud storage (S3/GCS/Azure Blob)."""

    def __init__(self, provider: str = "s3", **kwargs):
        self.provider = provider
        self.config = kwargs

    def upload(self, bucket: str, key: str, file_path: str,
               content_type: str = "application/octet-stream") -> dict:
        import subprocess
        if self.provider == "s3":
            cmd = ["aws", "s3", "cp", file_path, f"s3://{bucket}/{key}",
                   "--content-type", content_type]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {"status": "ok" if result.returncode == 0 else "error",
                    "output": result.stdout + result.stderr}
        elif self.provider == "gcs":
            cmd = ["gsutil", "cp", file_path, f"gs://{bucket}/{key}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {"status": "ok" if result.returncode == 0 else "error",
                    "output": result.stdout + result.stderr}
        return {"error": f"Unsupported provider: {self.provider}"}

    def download(self, bucket: str, key: str, file_path: str) -> dict:
        import subprocess
        if self.provider == "s3":
            cmd = ["aws", "s3", "cp", f"s3://{bucket}/{key}", file_path]
        elif self.provider == "gcs":
            cmd = ["gsutil", "cp", f"gs://{bucket}/{key}", file_path]
        else:
            return {"error": f"Unsupported provider: {self.provider}"}
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return {"status": "ok" if result.returncode == 0 else "error",
                "output": result.stdout + result.stderr}

    def list_objects(self, bucket: str, prefix: str = "") -> dict:
        import subprocess
        if self.provider == "s3":
            cmd = ["aws", "s3", "ls", f"s3://{bucket}/{prefix}", "--recursive"]
        elif self.provider == "gcs":
            cmd = ["gsutil", "ls", f"gs://{bucket}/{prefix}"]
        else:
            return {"error": f"Unsupported provider: {self.provider}"}
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return {"status": "ok", "objects": result.stdout.strip().split("\n") if result.stdout else []}

    def delete(self, bucket: str, key: str) -> dict:
        import subprocess
        if self.provider == "s3":
            cmd = ["aws", "s3", "rm", f"s3://{bucket}/{key}"]
        elif self.provider == "gcs":
            cmd = ["gsutil", "rm", f"gs://{bucket}/{key}"]
        else:
            return {"error": f"Unsupported provider: {self.provider}"}
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return {"status": "ok" if result.returncode == 0 else "error"}


class StripeIntegration:
    """Idea 48: Payment webhook integration (Stripe)."""

    def __init__(self, secret_key: str, webhook_secret: str | None = None):
        self.secret_key = secret_key
        self.webhook_secret = webhook_secret
        self.base_url = "https://api.stripe.com/v1"

    def _request(self, method: str, endpoint: str, data: dict | None = None) -> dict:
        import urllib.parse
        import urllib.request
        url = f"{self.base_url}{endpoint}"
        body = urllib.parse.urlencode(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method,
                                     headers={"Authorization": f"Bearer {self.secret_key}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def create_payment_intent(self, amount: int, currency: str = "usd",
                              description: str = "") -> dict:
        data = {"amount": amount, "currency": currency}
        if description:
            data["description"] = description
        return self._request("POST", "/payment_intents", data)

    def create_charge(self, amount: int, currency: str, source: str,
                      description: str = "") -> dict:
        data = {"amount": amount, "currency": currency, "source": source}
        if description:
            data["description"] = description
        return self._request("POST", "/charges", data)

    def create_customer(self, email: str, name: str = "") -> dict:
        data = {"email": email}
        if name:
            data["name"] = name
        return self._request("POST", "/customers", data)

    def list_charges(self, limit: int = 10) -> dict:
        return self._request("GET", f"/charges?limit={limit}")

    def create_refund(self, charge_id: str, amount: int | None = None) -> dict:
        data = {"charge": charge_id}
        if amount:
            data["amount"] = amount
        return self._request("POST", "/refunds", data)

    def verify_webhook(self, payload: bytes, sig_header: str) -> bool:
        if not self.webhook_secret:
            return True
        import hmac
        elements = dict(item.split("=", 1) for item in sig_header.split(","))
        timestamp = elements.get("t", "")
        expected_sig = elements.get("v1", "")
        signed_payload = f"{timestamp}.{payload.decode()}"
        computed = hmac.new(
            self.webhook_secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, expected_sig)


class CrmIntegration:
    """Idea 49: CRM integration (Salesforce-like)."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _request(self, method: str, endpoint: str, data: dict | None = None) -> dict:
        import urllib.request
        url = f"{self.base_url}/api{endpoint}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method,
                                     headers={"Authorization": f"Bearer {self.api_key}",
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def create_contact(self, first_name: str, last_name: str, email: str,
                       phone: str = "", company: str = "") -> dict:
        data = {"first_name": first_name, "last_name": last_name, "email": email}
        if phone:
            data["phone"] = phone
        if company:
            data["company"] = company
        return self._request("POST", "/contacts", data)

    def update_contact(self, contact_id: str, fields: dict[str, Any]) -> dict:
        return self._request("PUT", f"/contacts/{contact_id}", fields)

    def get_contact(self, contact_id: str) -> dict:
        return self._request("GET", f"/contacts/{contact_id}")

    def search_contacts(self, query: str) -> dict:
        import urllib.parse
        return self._request("GET", f"/contacts?search={urllib.parse.quote(query)}")

    def create_opportunity(self, name: str, stage: str, amount: float,
                           contact_id: str | None = None) -> dict:
        data = {"name": name, "stage": stage, "amount": amount}
        if contact_id:
            data["contact_id"] = contact_id
        return self._request("POST", "/opportunities", data)

    def list_opportunities(self, stage: str | None = None) -> dict:
        endpoint = "/opportunities"
        if stage:
            endpoint += f"?stage={stage}"
        return self._request("GET", endpoint)


class AnalyticsIntegration:
    """Idea 50: Analytics integration (Google Analytics-like)."""

    def __init__(self, api_key: str, property_id: str | None = None):
        self.api_key = api_key
        self.property_id = property_id
        self.base_url = "https://analyticsdata.googleapis.com/v1beta"

    def _request(self, method: str, endpoint: str, data: dict | None = None) -> dict:
        import urllib.request
        url = f"{self.base_url}{endpoint}?key={self.api_key}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def run_report(self, date_ranges: list[dict] | None = None,
                   metrics: list[dict] | None = None,
                   dimensions: list[dict] | None = None) -> dict:
        payload = {
            "dateRanges": date_ranges or [{"startDate": "30daysAgo", "endDate": "today"}],
            "metrics": metrics or [{"name": "sessions"}, {"name": "totalUsers"}],
            "dimensions": dimensions or [{"name": "date"}],
        }
        return self._request("POST", f"/properties/{self.property_id}:runReport", payload)

    def track_event(self, client_id: str, event_name: str,
                    params: dict | None = None) -> dict:
        payload = {
            "client_id": client_id,
            "events": [{"name": event_name, "params": params or {}}],
        }
        return self._request("POST", "/mp/collect", payload)

    def list_events(self) -> dict:
        return self._request("GET", f"/properties/{self.property_id}/eventDefinitions")

    def get_realtime(self, minutes: int = 30) -> dict:
        payload = {
            "dateRanges": [{"startDate": "today", "endDate": "today"}],
            "metrics": [{"name": "activeUsers"}],
            "minuteRanges": [{"startMinutesAgo": minutes, "endMinutesAgo": 0}],
        }
        return self._request("POST", f"/properties/{self.property_id}:runRealtimeReport", payload)


class IntegrationManager:
    """External integrations (Ideas 41-50)."""

    def __init__(self):
        self.configs: dict[str, IntegrationConfig] = {}
        self._instances: dict[str, Any] = {}

    def configure(self, name: str, integration_type: str, **kwargs) -> IntegrationConfig:
        config = IntegrationConfig(
            integration_type=IntegrationType(integration_type),
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"),
            extra={k: v for k, v in kwargs.items() if k not in ("api_key", "base_url")},
        )
        self.configs[name] = config
        return config

    def get_integration(self, name: str) -> Any:
        if name in self._instances:
            return self._instances[name]

        config = self.configs.get(name)
        if not config:
            return None

        kwargs = {"api_key": config.api_key}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        kwargs.update(config.extra)

        instance = None
        if config.integration_type == IntegrationType.GITHUB:
            instance = GitHubIntegration(token=config.api_key or "", **{k: v for k, v in kwargs.items() if k in ("base_url",)})
        elif config.integration_type == IntegrationType.SLACK:
            instance = SlackIntegration(bot_token=config.api_key or "", webhook_url=config.extra.get("webhook_url"))
        elif config.integration_type == IntegrationType.TELEGRAM:
            instance = TelegramIntegration(bot_token=config.api_key or "")
        elif config.integration_type == IntegrationType.JIRA:
            instance = JiraIntegration(base_url=config.base_url or "", email=config.extra.get("email", ""), api_token=config.api_key or "")
        elif config.integration_type == IntegrationType.DOCKER:
            instance = DockerIntegration(docker_host=config.extra.get("docker_host", "unix:///var/run/docker.sock"))
        elif config.integration_type == IntegrationType.STRIPE:
            instance = StripeIntegration(secret_key=config.api_key or "", webhook_secret=config.extra.get("webhook_secret"))
        elif config.integration_type == IntegrationType.CRM:
            instance = CrmIntegration(base_url=config.base_url or "", api_key=config.api_key or "")
        elif config.integration_type == IntegrationType.ANALYTICS:
            instance = AnalyticsIntegration(api_key=config.api_key or "", property_id=config.extra.get("property_id"))
        elif config.integration_type == IntegrationType.CLOUD_STORAGE:
            instance = CloudStorageIntegration(provider=config.extra.get("provider", "s3"))
        elif config.integration_type == IntegrationType.GOOGLE_CALENDAR:
            instance = GoogleCalendarIntegration(credentials_path=config.extra.get("credentials_path", ""))

        if instance:
            self._instances[name] = instance
        return instance

    def list_integrations(self) -> list[dict]:
        return [{"name": n, **c.to_dict()} for n, c in self.configs.items()]

    def remove(self, name: str) -> bool:
        self.configs.pop(name, None)
        self._instances.pop(name, None)
        return True
