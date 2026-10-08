import json
import logging
import sqlite3
import time

from aiohttp import WSMsgType, web

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def init_db():
    conn = sqlite3.connect("daniela_multiuser.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            hash TEXT,
            created_at REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sos_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            status TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()


init_db()

connected_clients = {}
admin_listeners = set()


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    client_email = None

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                action = data.get("action")

                if action == "register":
                    client_email = data.get("email")
                    connected_clients[client_email] = ws
                    logging.info(f"Cliente registrado en WebSocket: {client_email}")
                    await ws.send_str(
                        json.dumps(
                            {
                                "type": "SYS_ALERT",
                                "message": "[GÉNESIS DANIELA OS] Universo Cifrado AES-256 Generado Correctamente.",
                            }
                        )
                    )

                elif action == "register_admin":
                    admin_listeners.add(ws)
                    logging.info("Administrador Overseer conectado al canal de eventos.")
                    await ws.send_str(
                        json.dumps(
                            {
                                "type": "SYS_ALERT",
                                "message": "[OVERSEER ACTIVE] Canal de supervisión listo.",
                            }
                        )
                    )

                elif action == "sos_beacon":
                    status = data.get("status")
                    logging.warning(f"S.O.S. Beacon de {client_email}: {status}")

                    payload = json.dumps(
                        {
                            "type": "SOS_ALERT",
                            "email": client_email,
                            "status": status,
                            "timestamp": time.time(),
                        }
                    )
                    for admin_ws in list(admin_listeners):
                        try:
                            await admin_ws.send_str(payload)
                        except Exception:
                            admin_listeners.remove(admin_ws)

            except Exception as e:
                logging.error(f"Error procesando mensaje WS: {e}")

    if client_email and client_email in connected_clients:
        del connected_clients[client_email]
    if ws in admin_listeners:
        admin_listeners.remove(ws)

    return ws


app = web.Application()
app.router.add_get("/ws", websocket_handler)

if __name__ == "__main__":
    logging.info("Iniciando Tactical Server Multi-Tenant en puerto 8080...")
    web.run_app(app, host="0.0.0.0", port=8080)
