"""Turntable headless: orbita la camara alrededor del STL y saca PNGs.

Uso: blender --background --python blender_turntable.py -- <stl> <frames_dir> [fps] [segundos]
Motor EEVEE (rapido CPU). Si falla, el pipeline usa fallback Ken Burns.
"""

import math
import sys
from pathlib import Path

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
stl_path, frames_dir = argv[0], Path(argv[1])
fps = int(argv[2]) if len(argv) > 2 else 10
segundos = int(argv[3]) if len(argv) > 3 else 30
cuadros = fps * segundos

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"  # 4.2+: EEVEE Next (antes BLENDER_EEVEE)
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.frame_start = 1
scene.frame_end = cuadros

bpy.ops.wm.stl_import(filepath=stl_path)
obj = bpy.context.selected_objects[0]
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
obj.location = (0, 0, 0)

mat = bpy.data.materials.new("cian")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.0, 0.78, 1.0, 1.0)
bsdf.inputs["Metallic"].default_value = 0.6
bsdf.inputs["Roughness"].default_value = 0.4
obj.data.materials.append(mat)

cam = bpy.data.cameras.new("cam")
cam_obj = bpy.data.objects.new("cam", cam)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

sun = bpy.data.lights.new("sol", type="SUN")
sun.energy = 3.0
scene.collection.objects.link(bpy.data.objects.new("sol", sun))

radio, altura = 130.0, 80.0
cons = cam_obj.constraints.new(type="TRACK_TO")
cons.target = obj
cons.track_axis = "TRACK_NEGATIVE_Z"
cons.up_axis = "UP_Y"
for f in range(1, cuadros + 1):
    ang = 2 * math.pi * (f - 1) / cuadros
    cam_obj.location = (radio * math.cos(ang), radio * math.sin(ang), altura)
    cam_obj.keyframe_insert(data_path="location", frame=f)

scene.render.filepath = str(frames_dir / "frame_")
bpy.ops.render.render(animation=True)
print(f"TURNTABLE_OK {cuadros} frames -> {frames_dir}")
