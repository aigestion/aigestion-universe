# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

cmd_bp = Blueprint("command_palette", __name__)

COMMANDS = [
    {"name": "Focus Mode", "shortcut": "Ctrl+Shift+F", "action": "focus"},
    {"name": "Search", "shortcut": "Ctrl+K", "action": "search"},
    {"name": "Quick Settings", "shortcut": "Ctrl+,", "action": "settings"},
    {"name": "Toggle Theme", "shortcut": "Ctrl+D", "action": "theme"},
    {"name": "Kill All", "shortcut": "Ctrl+Shift+K", "action": "kill"},
    {"name": "Dashboard", "shortcut": "Ctrl+/", "action": "dashboard"},
    {"name": "Terminal", "shortcut": "Ctrl+`", "action": "terminal"},
    {"name": "New System", "shortcut": "Ctrl+N", "action": "new"}
]

@cmd_bp.route("/api/frontend/cmd/status")
def c_status():
    return jsonify({"commands": COMMANDS, "palette_open": False})

@cmd_bp.route("/api/frontend/cmd/web")
def c_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Command Palette</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.palette{max-width:500px;margin:0 auto}
.input{width:100%;background:#111;border:2px solid #00f0ff;color:#00f0ff;padding:15px;font-size:18px;border-radius:12px;font-family:monospace;margin-bottom:20px}
.cmd{background:#111;border:1px solid #333;border-radius:8px;padding:12px 15px;margin:5px 0;cursor:pointer;display:flex;justify-content:space-between}
.cmd:hover{border-color:#00f0ff}
.shortcut{color:#666;font-size:11px}
</style></head><body><div class="palette"><h2>COMMAND PALETTE</h2>
<input class="input" placeholder="Type a command... Ctrl+K" id="input">
<div id="commands"></div></div>
<script>const cmds=[{n:'Focus Mode',s:'Ctrl+Shift+F'},{n:'Search',s:'Ctrl+K'},{n:'Quick Settings',s:'Ctrl+,'},{n:'Toggle Theme',s:'Ctrl+D'},{n:'Kill All',s:'Ctrl+Shift+K'},{n:'Dashboard',s:'Ctrl+/'},{n:'Terminal',s:'Ctrl+`'},{n:'New System',s:'Ctrl+N'}];
const container=document.getElementById('commands');container.innerHTML=cmds.map(c=>'<div class="cmd"><span>'+c.n+'</span><span class="shortcut">'+c.s+'</span></div>').join('')</script></body></html>"""
