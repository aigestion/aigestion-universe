import json
import logging
import os
import subprocess

NODES_FILE = os.path.expanduser("~/daniela-os/cloud_nodes.json")


def _init_nodes():
    if not os.path.exists(NODES_FILE):
        with open(NODES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def register_node(alias, host, user="root", port="22"):
    """
    Skill #27: SSH Node Manager.
    Registra un nodo servidor remoto en la base de datos de Daniela.
    """
    _init_nodes()
    try:
        with open(NODES_FILE, "r+", encoding="utf-8") as f:
            nodes = json.load(f)
            nodes[alias.lower()] = {"host": host, "user": user, "port": port}
            f.seek(0)
            json.dump(nodes, f, ensure_ascii=False, indent=2)
            f.truncate()
        return f"🖥️ [NODE MANAGER]: Nodo '{alias}' ({user}@{host}:{port}) registrado."
    except Exception as e:
        logging.error(f"Error registrando nodo: {e}")
        return f"⚠️ [NODE ERROR]: {e}"


def exec_remote_cmd(alias, cmd):
    """Ejecuta un comando remoto en el nodo registrado mediante SSH."""
    _init_nodes()
    try:
        with open(NODES_FILE, encoding="utf-8") as f:
            nodes = json.load(f)

        node = nodes.get(alias.lower())
        if not node:
            return f"⚠️ [NODE ERROR]: Nodo '{alias}' no encontrado. Registralo primero."

        ssh_cmd = [
            "ssh",
            "-o",
            "ConnectTimeout=5",
            "-o",
            "StrictHostKeyChecking=no",
            "-p",
            str(node["port"]),
            f"{node['user']}@{node['host']}",
            cmd,
        ]

        output = subprocess.check_output(ssh_cmd, stderr=subprocess.STDOUT, text=True)
        return f"🌐 [NODE '{alias.upper()}']:\n{output.strip()}"
    except Exception as e:
        return f"❌ [NODE EXEC ERROR]: {e}"
