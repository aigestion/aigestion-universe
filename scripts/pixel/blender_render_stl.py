"""Render headless Blender: importa STL, estudio basico, PNG.

Uso: blender --background --python blender_render_stl.py -- <stl> <png>
Se ejecuta como script de Blender (nivel superior, sin main()).
"""

import sys

import bpy

stl_path, png_path = sys.argv[-2], sys.argv[-1]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.cycles.device = "CPU"
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.film_transparent = True
scene.render.filepath = png_path

bpy.ops.wm.stl_import(filepath=stl_path)
obj = bpy.context.selected_objects[0]

mat = bpy.data.materials.new("alu")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.55, 0.58, 0.62, 1.0)
bsdf.inputs["Metallic"].default_value = 0.9
bsdf.inputs["Roughness"].default_value = 0.35
obj.data.materials.append(mat)

cam = bpy.data.cameras.new("cam")
cam_obj = bpy.data.objects.new("cam", cam)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = (120, -120, 90)
cons = cam_obj.constraints.new(type="TRACK_TO")
cons.target = obj
cons.track_axis = "TRACK_NEGATIVE_Z"
cons.up_axis = "UP_Y"

sun = bpy.data.lights.new("sol", type="SUN")
sun.energy = 4.0
sun_obj = bpy.data.objects.new("sol", sun)
scene.collection.objects.link(sun_obj)

world = bpy.data.worlds.new("mundo")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.4
scene.world = world

bpy.ops.render.render(write_still=True)
print("RENDER_OK", png_path)
