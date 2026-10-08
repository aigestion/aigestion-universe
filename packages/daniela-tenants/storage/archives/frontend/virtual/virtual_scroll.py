# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
import json, time

virt_bp = Blueprint("virtual_scroll", __name__)

@virt_bp.route("/api/frontend/virtual/status")
def v_status():
    return jsonify({"items": 10000, "visible": 50, "rendered": 52, "fps": 60})

@virt_bp.route("/api/frontend/virtual/render", methods=["POST"])
def v_render():
    data = request.json or {}
    scroll_pos = data.get("scroll_pos", 0)
    item_height = data.get("item_height", 40)
    container_height = data.get("container_height", 500)
    start = scroll_pos // item_height
    end = start + (container_height // item_height) + 2
    return jsonify({"start": start, "end": end, "rendered": end - start})

@virt_bp.route("/api/frontend/virtual/web")
def v_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Virtual Scroll</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.list{height:400px;overflow-y:auto;border:1px solid #333;border-radius:8px}
.item{height:40px;border-bottom:1px solid #222;display:flex;align-items:center;padding:0 15px;will-change:transform}
.item:nth-child(even){background:#111} .item:nth-child(odd){background:#0d0d1a}
.stats{display:flex;gap:15px;margin:20px 0}
.stat{background:#111;border:1px solid #333;border-radius:8px;padding:15px}
</style></head><body><h1>VIRTUAL SCROLL</h1>
<div class="stats"><div class="stat"><div class="num" id="visible">50</div><p>Visible</p></div><div class="stat"><div class="num" id="rendered">52</div><p>Rendered</p></div><div class="stat"><div class="num" id="fps">60</div><p>FPS</p></div></div>
<div class="list" id="list"></div>
<script>const total=10000;const list=document.getElementById('list');let startIdx=0;const itemH=40;function render(){const scrollTop=list.scrollTop;startIdx=Math.floor(scrollTop/itemH);const visible=Math.ceil(list.clientHeight/itemH);const endIdx=startIdx+visible+2;let html='';for(let i=startIdx;i<endIdx&&i<total;i++){html+='<div class="item" style="transform:translateY('+(i*itemH)+'px)">Item '+i+'</div>'}list.innerHTML=html;document.getElementById('visible').textContent=visible;document.getElementById('rendered').textContent=endIdx-startIdx}list.addEventListener('scroll',render);render();for(let i=0;i<total;i++){const div=document.createElement('div');div.style.height='40px';list.appendChild(div)}</script></body></html>"""
