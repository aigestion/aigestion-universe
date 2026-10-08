import socket
import subprocess

PORT = 8095


def send_termux_notify(msg):
    try:
        subprocess.run(
            [
                "termux-notification",
                "--title",
                "DANIELA OS",
                "--content",
                msg,
                "--priority",
                "high",
                "--vibrate",
                "200,100,200",
                "--led-color",
                "00FF88",
            ]
        )
    except Exception as e:
        print(f"Error en termux-notification: {e}")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(5)
    print(f"🔔 Server de notificaciones de Daniela OS activo en puerto {PORT}...")

    while True:
        conn, addr = server.accept()
        data = conn.recv(1024).decode("utf-8", errors="ignore").strip()
        if data.startswith("NOTIFY:"):
            clean_msg = data.replace("NOTIFY:", "", 1)
            send_termux_notify(clean_msg)
        conn.close()


if __name__ == "__main__":
    start_server()
