import bpy
from math import radians
import argparse
import sys

def create_bone(name, head, tail, roll):
    bpy.ops.object.mode_set(mode='EDIT')
    armature = bpy.context.object
    bone = armature.data.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.roll = radians(roll)
    bpy.ops.object.mode_set(mode='OBJECT')

parser = argparse.ArgumentParser()
parser.add_argument("-g", "--glb", type=str, help="The glb file path.")
args = parser.parse_args()

glb_path = args.glb
bpy.ops.import_scene.gltf(filepath=glb_path)

imported_objects = bpy.context.selected_objects

obj_mesh = bpy.context.selected_objects[0]
obj_mesh.scale = (0.5, 0.5, 0.5)

bpy.context.view_layer.objects.active = obj_mesh
bpy.ops.object.transform_apply(location=True, scale=True, rotation=True)
obj_mesh.rotation_euler = (radians(90), 0, radians(90))
obj_mesh.location = (0, 0, 0.35)

bpy.ops.object.mode_set(mode='OBJECT')

bpy.context.view_layer.objects.active = obj_mesh
obj_mesh.select_set(True)

bpy.ops.object.mode_set(mode='EDIT')

bpy.ops.mesh.remove_doubles()

bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
armature = bpy.context.object

create_bone('Body', (0, 0, 0.23), (0, 0, 0.43), 0)
create_bone('Head', (0, 0, 0.45), (0, 0, 0.6), 0)
create_bone('Leg.L', (0.04, 0, 0.22), (0.06, 0, 0.11), 0)
create_bone('Foot.L', (0.06, 0, 0.11), (0.08, 0, 0), 0)
create_bone('Arm.L', (0.04, 0, 0.4), (0.16, 0, 0.4), 0)
create_bone('Hand.L', (0.16, 0, 0.4), (0.28, 0, 0.4), 0)
create_bone('Leg.R', (-0.04, 0, 0.22), (-0.06, 0, 0.11), 0)
create_bone('Foot.R', (-0.06, 0, 0.11), (-0.08, 0, 0), 0)
create_bone('Arm.R', (-0.04, 0, 0.4), (-0.16, 0, 0.4), 0)
create_bone('Hand.R', (-0.16, 0, 0.4), (-0.28, 0, 0.4), 0)

bpy.ops.object.mode_set(mode='EDIT')
body_bone = armature.data.edit_bones['Body']
head_bone = armature.data.edit_bones['Head']
head_bone.parent = body_bone

leg_l_bone = armature.data.edit_bones['Leg.L']
leg_l_bone.parent = body_bone
foot_l_bone = armature.data.edit_bones['Foot.L']
foot_l_bone.parent = leg_l_bone

arm_l_bone = armature.data.edit_bones['Arm.L']
arm_l_bone.parent = body_bone
hand_l_bone = armature.data.edit_bones['Hand.L']
hand_l_bone.parent = arm_l_bone

leg_r_bone = armature.data.edit_bones['Leg.R']
leg_r_bone.parent = body_bone
foot_r_bone = armature.data.edit_bones['Foot.R']
foot_r_bone.parent = leg_r_bone

arm_r_bone = armature.data.edit_bones['Arm.R']
arm_r_bone.parent = body_bone
hand_r_bone = armature.data.edit_bones['Hand.R']
hand_r_bone.parent = arm_r_bone

bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='DESELECT')
obj_mesh.select_set(True)
armature.select_set(True)

bpy.context.view_layer.objects.active = armature

bpy.ops.object.parent_set(type='ARMATURE_AUTO')
armature.select_set(False)
# bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')

for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj != obj_mesh:
        bpy.data.objects.remove(obj)

armature.location = (0, 0, 0)

glb_out_path = "./rigged.glb"
bpy.ops.export_scene.gltf(
    filepath=glb_out_path,
    export_format='GLB',
)
