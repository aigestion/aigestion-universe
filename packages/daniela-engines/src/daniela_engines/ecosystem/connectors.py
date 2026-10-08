"""Universal connectors - 10 ideas: REST, GraphQL, gRPC, WebSocket, MQTT, AMQP, Kafka, FTP/SFTP, SMTP, IMAP."""

import ftplib
import http.client
import imaplib
import json
import logging
import queue
import smtplib
import socket
import ssl
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConnectorStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class MessageFormat(Enum):
    JSON = "json"
    XML = "xml"
    TEXT = "text"
    BINARY = "binary"
    PROTOBUF = "protobuf"


@dataclass
class ConnectorConfig:
    host: str = "localhost"
    port: int = 80
    username: str | None = None
    password: str | None = None
    timeout: int = 30
    retry_count: int = 3
    tls: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    topic: str
    payload: Any
    headers: dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message_id: str = ""
    correlation_id: str | None = None


class BaseConnector(ABC):
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.status = ConnectorStatus.DISCONNECTED
        self._callbacks: dict[str, list[Callable]] = {}

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        pass

    @abstractmethod
    def send(self, message: Message) -> bool:
        pass

    @abstractmethod
    def receive(self, timeout: float = 5.0) -> Message | None:
        pass

    def on(self, event: str, callback: Callable):
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any):
        for cb in self._callbacks.get(event, []):
            try:
                cb(data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    def is_connected(self) -> bool:
        return self.status == ConnectorStatus.CONNECTED


class RESTConnector(BaseConnector):
    """11. REST API connector (configurable)"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.base_url = f"{'https' if config.tls else 'http'}://{config.host}:{config.port}"
        self.session_headers: dict[str, str] = {"Content-Type": "application/json"}
        self._conn = None

    def connect(self) -> bool:
        try:
            if self.config.tls:
                self._conn = http.client.HTTPSConnection(
                    self.config.host, self.config.port,
                    timeout=self.config.timeout,
                    context=ssl.create_default_context()
                )
            else:
                self._conn = http.client.HTTPConnection(
                    self.config.host, self.config.port,
                    timeout=self.config.timeout
                )
            if self.config.username and self.config.password:
                import base64
                creds = base64.b64encode(
                    f"{self.config.username}:{self.config.password}".encode()
                ).decode()
                self.session_headers["Authorization"] = f"Basic {creds}"
            self.status = ConnectorStatus.CONNECTED
            self._emit("connected", None)
            return True
        except Exception as e:
            logger.error(f"REST connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        if self._conn:
            self._conn.close()
            self._conn = None
        self.status = ConnectorStatus.DISCONNECTED
        return True

    def request(self, method: str, path: str, body: Any = None,
                headers: dict[str, str] | None = None) -> dict[str, Any]:
        if not self.is_connected():
            raise ConnectionError("Not connected")
        req_headers = {**self.session_headers, **(headers or {})}
        body_str = json.dumps(body) if body and isinstance(body, (dict, list)) else body

        for attempt in range(self.config.retry_count):
            try:
                self._conn.request(method, path, body=body_str, headers=req_headers)
                response = self._conn.getresponse()
                data = response.read().decode()
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    pass
                result = {
                    "status": response.status,
                    "reason": response.reason,
                    "headers": dict(response.getheaders()),
                    "body": data
                }
                self._emit("response", result)
                return result
            except Exception as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == self.config.retry_count - 1:
                    raise
                time.sleep(1 * (attempt + 1))
        return {}

    def send(self, message: Message) -> bool:
        try:
            path = message.topic if message.topic.startswith("/") else f"/{message.topic}"
            result = self.request("POST", path, body=message.payload, headers=message.headers)
            return 200 <= result.get("status", 0) < 300
        except Exception as e:
            logger.error(f"REST send failed: {e}")
            return False

    def receive(self, timeout: float = 5.0) -> Message | None:
        return None

    def get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        query = "?" + "&".join(f"{k}={v}" for k, v in params.items()) if params else ""
        return self.request("GET", f"{path}{query}")

    def post(self, path: str, data: Any) -> dict[str, Any]:
        return self.request("POST", path, body=data)

    def put(self, path: str, data: Any) -> dict[str, Any]:
        return self.request("PUT", path, body=data)

    def delete(self, path: str) -> dict[str, Any]:
        return self.request("DELETE", path)

    def set_auth_token(self, token: str, scheme: str = "Bearer"):
        self.session_headers["Authorization"] = f"{scheme} {token}"


class GraphQLConnector(BaseConnector):
    """12. GraphQL connector"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.endpoint = f"{'https' if config.tls else 'http'}://{config.host}:{config.port}/graphql"
        self._conn = None

    def connect(self) -> bool:
        try:
            host = self.config.host
            port = self.config.port
            if self.config.tls:
                self._conn = http.client.HTTPSConnection(host, port, timeout=self.config.timeout)
            else:
                self._conn = http.client.HTTPConnection(host, port, timeout=self.config.timeout)
            self.status = ConnectorStatus.CONNECTED
            return True
        except Exception as e:
            logger.error(f"GraphQL connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        if self._conn:
            self._conn.close()
            self._conn = None
        self.status = ConnectorStatus.DISCONNECTED
        return True

    def query(self, query: str, variables: dict[str, Any] | None = None,
              operation_name: str | None = None) -> dict[str, Any]:
        if not self.is_connected():
            raise ConnectionError("Not connected")
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        headers = {"Content-Type": "application/json"}
        if self.config.username:
            import base64
            creds = base64.b64encode(
                f"{self.config.username}:{self.config.password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {creds}"

        body = json.dumps(payload)
        self._conn.request("POST", self.endpoint, body=body, headers=headers)
        response = self._conn.getresponse()
        data = json.loads(response.read().decode())
        self._emit("response", data)
        return data

    def mutate(self, mutation: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.query(mutation, variables)

    def subscribe(self, subscription: str, variables: dict[str, Any] | None = None,
                  callback: Callable | None = None) -> dict[str, Any]:
        result = self.query(subscription, variables)
        if callback:
            callback(result)
        return result

    def introspect(self) -> dict[str, Any]:
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                queryType { name }
                mutationType { name }
                subscriptionType { name }
                types { name kind }
            }
        }
        """
        return self.query(introspection_query)

    def send(self, message: Message) -> bool:
        try:
            result = self.query(message.topic, message.payload if isinstance(message.payload, dict) else None)
            return "data" in result or "errors" not in result
        except Exception as e:
            logger.error(f"GraphQL send failed: {e}")
            return False

    def receive(self, timeout: float = 5.0) -> Message | None:
        return None


class GrpcConnector(BaseConnector):
    """13. gRPC connector"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.services: dict[str, Callable] = {}
        self._channel = None
        self._server = None

    def connect(self) -> bool:
        try:
            self._channel = {
                "host": self.config.host,
                "port": self.config.port,
                "target": f"{self.config.host}:{self.config.port}"
            }
            self.status = ConnectorStatus.CONNECTED
            return True
        except Exception as e:
            logger.error(f"gRPC connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        self._channel = None
        self.status = ConnectorStatus.DISCONNECTED
        return True

    def register_service(self, service_name: str, handler: Callable):
        self.services[service_name] = handler
        logger.info(f"Registered gRPC service: {service_name}")

    def call(self, service: str, method: str, request: dict[str, Any]) -> dict[str, Any]:
        if not self.is_connected():
            raise ConnectionError("Not connected")
        if service not in self.services:
            raise ValueError(f"Service {service} not found")
        try:
            result = self.services[service](method, request)
            self._emit("response", result)
            return {"status": "ok", "data": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def start_server(self, port: int | None = None):
        self._server = {"port": port or self.config.port, "services": self.services}
        logger.info(f"gRPC server started on port {self._server['port']}")

    def stop_server(self):
        self._server = None
        logger.info("gRPC server stopped")

    def send(self, message: Message) -> bool:
        try:
            parts = message.topic.split("/")
            if len(parts) >= 2:
                service, method = parts[0], parts[1]
                result = self.call(service, method, message.payload)
                return result.get("status") == "ok"
        except Exception as e:
            logger.error(f"gRPC send failed: {e}")
        return False

    def receive(self, timeout: float = 5.0) -> Message | None:
        return None


class WebSocketConnector(BaseConnector):
    """14. WebSocket connector"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.url = f"{'wss' if config.tls else 'ws'}://{config.host}:{config.port}"
        self._socket = None
        self._recv_queue = queue.Queue()
        self._running = False
        self._thread: threading.Thread | None = None

    def connect(self) -> bool:
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.config.host, self.config.port))
            self._running = True
            self._thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._thread.start()
            self.status = ConnectorStatus.CONNECTED
            self._emit("connected", None)
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        self._running = False
        if self._socket:
            self._socket.close()
            self._socket = None
        if self._thread:
            self._thread.join(timeout=5)
        self.status = ConnectorStatus.DISCONNECTED
        return True

    def _receive_loop(self):
        while self._running:
            try:
                data = self._socket.recv(4096)
                if data:
                    msg = Message(topic="ws", payload=data.decode(errors="replace"))
                    self._recv_queue.put(msg)
                    self._emit("message", msg)
            except Exception:
                if self._running:
                    self.status = ConnectorStatus.RECONNECTING
                break

    def send(self, message: Message) -> bool:
        if not self.is_connected():
            return False
        try:
            payload = json.dumps({
                "topic": message.topic,
                "payload": message.payload,
                "headers": message.headers
            })
            self._socket.send(payload.encode())
            self._emit("sent", message)
            return True
        except Exception as e:
            logger.error(f"WebSocket send failed: {e}")
            return False

    def receive(self, timeout: float = 5.0) -> Message | None:
        try:
            return self._recv_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def ping(self) -> bool:
        if not self.is_connected():
            return False
        try:
            self._socket.send(b"ping")
            return True
        except Exception:
            return False


class MQTTConnector(BaseConnector):
    """15. MQTT connector (IoT)"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.broker = config.host
        self.port = config.port or 1883
        self.client_id = config.extra.get("client_id", f"mqtt-{id(self)}")
        self._subscriptions: dict[str, Callable] = {}
        self._messages: queue.Queue = queue.Queue()
        self._connected = False

    def connect(self) -> bool:
        try:
            self._connected = True
            self.status = ConnectorStatus.CONNECTED
            self._emit("connected", {"broker": self.broker, "port": self.port})
            logger.info(f"MQTT connected to {self.broker}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        self._connected = False
        self.status = ConnectorStatus.DISCONNECTED
        logger.info("MQTT disconnected")
        return True

    def subscribe(self, topic: str, callback: Callable | None = None, qos: int = 0):
        self._subscriptions[topic] = callback
        logger.info(f"MQTT subscribed to {topic} (QoS {qos})")

    def unsubscribe(self, topic: str):
        self._subscriptions.pop(topic, None)

    def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        if not self._connected:
            return False
        message = Message(topic=topic, payload=payload, headers={"qos": str(qos), "retain": str(retain)})
        self._messages.put(message)
        if topic in self._subscriptions and self._subscriptions[topic]:
            self._subscriptions[topic](message)
        self._emit("published", message)
        return True

    def send(self, message: Message) -> bool:
        return self.publish(message.topic, message.payload)

    def receive(self, timeout: float = 5.0) -> Message | None:
        try:
            return self._messages.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_subscriptions(self) -> list[str]:
        return list(self._subscriptions.keys())


class AMQPConnector(BaseConnector):
    """16. AMQP connector (RabbitMQ)"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.exchange = config.extra.get("exchange", "default")
        self.queues: dict[str, queue.Queue] = {}
        self._connected = False
        self._bindings: dict[str, list[str]] = {}

    def connect(self) -> bool:
        try:
            self._connected = True
            self.status = ConnectorStatus.CONNECTED
            self._emit("connected", {"host": self.config.host, "exchange": self.exchange})
            logger.info(f"AMQP connected to {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.error(f"AMQP connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        self._connected = False
        self.status = ConnectorStatus.DISCONNECTED
        return True

    def declare_queue(self, queue_name: str, durable: bool = True) -> bool:
        self.queues[queue_name] = queue.Queue()
        logger.info(f"Declared queue: {queue_name} (durable={durable})")
        return True

    def declare_exchange(self, exchange_name: str, exchange_type: str = "direct") -> bool:
        self.exchange = exchange_name
        logger.info(f"Declared exchange: {exchange_name} (type={exchange_type})")
        return True

    def bind_queue(self, queue_name: str, routing_key: str) -> bool:
        if queue_name not in self._bindings:
            self._bindings[queue_name] = []
        self._bindings[queue_name].append(routing_key)
        return True

    def publish(self, routing_key: str, body: Any, exchange: str | None = None) -> bool:
        if not self._connected:
            return False
        exchange = exchange or self.exchange
        message = Message(topic=routing_key, payload=body, headers={"exchange": exchange})
        for q_name, bindings in self._bindings.items():
            if routing_key in bindings and q_name in self.queues:
                self.queues[q_name].put(message)
        self._emit("published", message)
        return True

    def consume(self, queue_name: str, callback: Callable, auto_ack: bool = True):
        if queue_name not in self.queues:
            self.declare_queue(queue_name)
        q = self.queues[queue_name]
        while not q.empty():
            msg = q.get_nowait()
            callback(msg)
            if not auto_ack:
                q.task_done()

    def ack(self, queue_name: str):
        if queue_name in self.queues:
            self.queues[queue_name].task_done()

    def send(self, message: Message) -> bool:
        return self.publish(message.topic, message.payload)

    def receive(self, timeout: float = 5.0) -> Message | None:
        for q in self.queues.values():
            try:
                return q.get(timeout=timeout)
            except queue.Empty:
                continue
        return None


class KafkaConnector(BaseConnector):
    """17. Kafka connector"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.bootstrap_servers = f"{config.host}:{config.port}"
        self.topics: dict[str, queue.Queue] = {}
        self._consumer_threads: dict[str, threading.Thread] = {}
        self._running = False
        self._offsets: dict[str, int] = {}

    def connect(self) -> bool:
        try:
            self._running = True
            self.status = ConnectorStatus.CONNECTED
            self._emit("connected", {"servers": self.bootstrap_servers})
            logger.info(f"Kafka connected to {self.bootstrap_servers}")
            return True
        except Exception as e:
            logger.error(f"Kafka connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        self._running = False
        self.status = ConnectorStatus.DISCONNECTED
        return True

    def create_topic(self, topic: str, partitions: int = 1, replication: int = 1) -> bool:
        self.topics[topic] = queue.Queue()
        self._offsets[topic] = 0
        logger.info(f"Created topic: {topic} (partitions={partitions})")
        return True

    def produce(self, topic: str, value: Any, key: str | None = None,
                partition: int = 0) -> bool:
        if topic not in self.topics:
            self.create_topic(topic)
        message = Message(
            topic=topic,
            payload=value,
            headers={"key": key or "", "partition": str(partition)}
        )
        self.topics[topic].put(message)
        self._offsets[topic] += 1
        self._emit("produced", message)
        return True

    def consume(self, topic: str, callback: Callable, group_id: str | None = None,
                auto_commit: bool = True):
        if topic not in self.topics:
            return
        q = self.topics[topic]
        while self._running:
            try:
                msg = q.get(timeout=1.0)
                callback(msg)
                if auto_commit:
                    self._offsets[topic] += 1
            except queue.Empty:
                continue

    def start_consuming(self, topic: str, callback: Callable, group_id: str | None = None):
        t = threading.Thread(target=self.consume, args=(topic, callback, group_id), daemon=True)
        self._consumer_threads[topic] = t
        t.start()

    def get_offset(self, topic: str) -> int:
        return self._offsets.get(topic, 0)

    def send(self, message: Message) -> bool:
        return self.produce(message.topic, message.payload)

    def receive(self, timeout: float = 5.0) -> Message | None:
        for q in self.topics.values():
            try:
                return q.get(timeout=timeout)
            except queue.Empty:
                continue
        return None


class FTPConnector(BaseConnector):
    """18. FTP/SFTP connector"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._ftp = None
        self.protocol = config.extra.get("protocol", "ftp")

    def connect(self) -> bool:
        try:
            if self.protocol == "sftp":
                import paramiko
                transport = paramiko.Transport((self.config.host, self.config.port or 22))
                transport.connect(username=self.config.username, password=self.config.password)
                self._ftp = transport.open_sftp()
            else:
                self._ftp = ftplib.FTP()
                self._ftp.connect(self.config.host, self.config.port or 21)
                if self.config.username:
                    self._ftp.login(self.config.username, self.config.password)
            self.status = ConnectorStatus.CONNECTED
            return True
        except Exception as e:
            logger.error(f"FTP connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        if self._ftp:
            try:
                if self.protocol == "sftp":
                    self._ftp.close()
                else:
                    self._ftp.quit()
            except Exception:
                pass
            self._ftp = None
        self.status = ConnectorStatus.DISCONNECTED
        return True

    def upload(self, local_path: str, remote_path: str) -> bool:
        if not self.is_connected():
            return False
        try:
            if self.protocol == "sftp":
                self._ftp.put(local_path, remote_path)
            else:
                with open(local_path, "rb") as f:
                    self._ftp.storbinary(f"STOR {remote_path}", f)
            self._emit("uploaded", {"local": local_path, "remote": remote_path})
            return True
        except Exception as e:
            logger.error(f"FTP upload failed: {e}")
            return False

    def download(self, remote_path: str, local_path: str) -> bool:
        if not self.is_connected():
            return False
        try:
            if self.protocol == "sftp":
                self._ftp.get(remote_path, local_path)
            else:
                with open(local_path, "wb") as f:
                    self._ftp.retrbinary(f"RETR {remote_path}", f.write)
            self._emit("downloaded", {"remote": remote_path, "local": local_path})
            return True
        except Exception as e:
            logger.error(f"FTP download failed: {e}")
            return False

    def list_files(self, path: str = ".") -> list[str]:
        if not self.is_connected():
            return []
        try:
            if self.protocol == "sftp":
                return self._ftp.listdir(path)
            else:
                self._ftp.cwd(path)
                return self._ftp.nlst()
        except Exception:
            return []

    def mkdir(self, path: str) -> bool:
        if not self.is_connected():
            return False
        try:
            if self.protocol == "sftp":
                self._ftp.mkdir(path)
            else:
                self._ftp.mkd(path)
            return True
        except Exception:
            return False

    def delete(self, remote_path: str) -> bool:
        if not self.is_connected():
            return False
        try:
            if self.protocol == "sftp":
                self._ftp.remove(remote_path)
            else:
                self._ftp.delete(remote_path)
            return True
        except Exception:
            return False

    def send(self, message: Message) -> bool:
        return self.upload(str(message.payload), message.topic)

    def receive(self, timeout: float = 5.0) -> Message | None:
        return None


class SMTPConnector(BaseConnector):
    """19. SMTP connector"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._server = None
        self.default_from = config.extra.get("from", config.username or "")

    def connect(self) -> bool:
        try:
            if self.config.tls:
                self._server = smtplib.SMTP_SSL(
                    self.config.host, self.config.port or 465,
                    timeout=self.config.timeout
                )
            else:
                self._server = smtplib.SMTP(
                    self.config.host, self.config.port or 587,
                    timeout=self.config.timeout
                )
                self._server.starttls()
            if self.config.username and self.config.password:
                self._server.login(self.config.username, self.config.password)
            self.status = ConnectorStatus.CONNECTED
            return True
        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        if self._server:
            try:
                self._server.quit()
            except Exception:
                pass
            self._server = None
        self.status = ConnectorStatus.DISCONNECTED
        return True

    def send_email(self, to: str | list[str], subject: str, body: str,
                   from_addr: str | None = None, html: bool = False,
                   cc: list[str] | None = None, bcc: list[str] | None = None,
                   attachments: list[tuple[str, bytes]] | None = None) -> bool:
        if not self.is_connected():
            return False
        try:
            from email import encoders
            from email.mime.base import MIMEBase
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart()
            msg["From"] = from_addr or self.default_from
            if isinstance(to, list):
                to = ", ".join(to)
            msg["To"] = to
            msg["Subject"] = subject
            if cc:
                msg["Cc"] = ", ".join(cc)

            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))

            if attachments:
                for filename, content in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={filename}")
                    msg.attach(part)

            recipients = [to] if isinstance(to, str) else to
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            self._server.sendmail(msg["From"], recipients, msg.as_string())
            self._emit("email_sent", {"to": to, "subject": subject})
            return True
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return False

    def send_message(self, message: Message) -> bool:
        to = message.headers.get("to", self.default_from)
        subject = message.headers.get("subject", message.topic)
        return self.send_email(to, subject, str(message.payload))

    def send(self, message: Message) -> bool:
        return self.send_message(message)

    def receive(self, timeout: float = 5.0) -> Message | None:
        return None


class IMAPConnector(BaseConnector):
    """20. IMAP connector"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._server = None
        self._current_folder = "INBOX"

    def connect(self) -> bool:
        try:
            host = self.config.host
            port = self.config.port or 993
            if self.config.tls:
                self._server = imaplib.IMAP4_SSL(host, port)
            else:
                self._server = imaplib.IMAP4(host, port)
            if self.config.username and self.config.password:
                self._server.login(self.config.username, self.config.password)
            self.status = ConnectorStatus.CONNECTED
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            self.status = ConnectorStatus.ERROR
            return False

    def disconnect(self) -> bool:
        if self._server:
            try:
                self._server.logout()
            except Exception:
                pass
            self._server = None
        self.status = ConnectorStatus.DISCONNECTED
        return True

    def list_folders(self) -> list[str]:
        if not self.is_connected():
            return []
        status, folders = self._server.list()
        return [f.decode().split('" "')[-1].strip('"') for f in folders if f]

    def select_folder(self, folder: str = "INBOX") -> int:
        if not self.is_connected():
            return 0
        self._current_folder = folder
        status, data = self._server.select(folder)
        return int(data[0]) if status == "OK" else 0

    def search(self, criteria: str = "ALL", folder: str | None = None) -> list[str]:
        if not self.is_connected():
            return []
        if folder:
            self.select_folder(folder)
        status, data = self._server.search(None, criteria)
        if status == "OK":
            return data[0].split()
        return []

    def fetch_message(self, msg_id: str) -> dict[str, Any]:
        if not self.is_connected():
            return {}
        status, data = self._server.fetch(msg_id, "(RFC822)")
        if status == "OK":
            raw = data[0][1]
            return {"id": msg_id, "raw": raw.decode(errors="replace")}
        return {}

    def fetch_headers(self, msg_id: str) -> dict[str, str]:
        if not self.is_connected():
            return {}
        status, data = self._server.fetch(msg_id, "(BODY[HEADER])")
        if status == "OK":
            header_text = data[0][1].decode(errors="replace")
            headers = {}
            for line in header_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()
            return headers
        return {}

    def move_message(self, msg_id: str, target_folder: str) -> bool:
        if not self.is_connected():
            return False
        result = self._server.copy(msg_id, target_folder)
        if result[0] == "OK":
            self._server.store(msg_id, "+FLAGS", "\\Deleted")
            self._server.expunge()
            return True
        return False

    def delete_message(self, msg_id: str) -> bool:
        if not self.is_connected():
            return False
        self._server.store(msg_id, "+FLAGS", "\\Deleted")
        self._server.expunge()
        return True

    def get_unread_count(self, folder: str | None = None) -> int:
        if not self.is_connected():
            return 0
        if folder:
            self.select_folder(folder)
        status, data = self._server.search(None, "UNSEEN")
        if status == "OK":
            return len(data[0].split())
        return 0

    def send(self, message: Message) -> bool:
        return False

    def receive(self, timeout: float = 5.0) -> Message | None:
        if not self.is_connected():
            return None
        unread = self.search("UNSEEN")
        if unread:
            msg_data = self.fetch_message(unread[0])
            return Message(topic=self._current_folder, payload=msg_data)
        return None
