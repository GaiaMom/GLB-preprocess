import cv2
import bpy
import os
from math import radians, sin
import shutil
import numpy as np
import glob
import time

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--logo", type=str, help="The logo png file.")
parser.add_argument("-g", "--glb", type=str, help="The glb files.")
parser.add_argument("-f", "--folder", type=str, help="Select the folder.")

args = parser.parse_args()

def calculate_new_rotate(bone_name, angle_deg):
    angle_rad = radians(angle_deg)
    if bone_name == 'Arm.R' or bone_name == 'Arm.L':
        return (1.0, sin(angle_rad)/1.7, 0, 0)
    if bone_name == 'Leg.L':
        angle_rad += radians(90)
        return (1.0, 0, 0, sin(angle_rad) + 0.25)
    if bone_name == 'Leg.R':
        angle_rad += radians(90)
        return (1.0, 0, 0, sin(angle_rad) - 0.25)
    if bone_name == 'Hand.R':
        return (1.0, -1 * sin(angle_rad), 0, 0)
    if bone_name == 'Hand.L':
        return (1.0, sin(angle_rad), 0, 0)
    if bone_name == 'Foot.R':
        return (1.0, 0, 0, -1 * sin(angle_rad))
    if bone_name == 'Foot.L':
        return (1.0, 0, 0, -1 * sin(angle_rad))

def update_bone_rotations(data, armature):
    new_angles = {
        'Arm.R': data['RightShoulder'],
        'Arm.L': data['LeftShoulder'],
        'Leg.R': data['RHipJoint'],
        'Leg.L': data['LHipJoint'],
        'Hand.R': data['RightArm'],
        'Hand.L': data['LeftArm'],
        'Foot.R': data['RightLeg'],
        'Foot.L': data['LeftLeg'],
    }
    armature.location.z = data['y_position']
    armature.location.x = data['x_position']

    for bone_name, angle in new_angles.items():
        bone = armature.pose.bones.get(bone_name)
        if bone:
            new_rotate = calculate_new_rotate(bone_name, angle)
            bone.rotation_quaternion = new_rotate
            print(f"{bone_name} bone rotated to {new_rotate}")

def read_bone_data(file_path):
    data = {}
    with open(file_path, 'r') as f:
        for line in f:
            key, value = line.split(':')
            data[key.strip()] = float(value.strip())
    return data

def interpolate_data(data_start, data_end, factor):
    interpolated_data = {}
    for key in data_start.keys():
        interpolated_data[key] = data_start[key] + (data_end[key] - data_start[key]) * factor
    return interpolated_data

while not os.path.exists(args.glb):
    time.sleep(1)

bpy.context.scene.world.use_nodes = True
bg_node = bpy.context.scene.world.node_tree.nodes['Background']
bg_node.inputs[0].default_value = (0, 0, 0, 1)

bpy.ops.object.light_add(type='POINT', location=(0, -5, 0))
light = bpy.context.object
light.data.energy = 1000  # Adjust the energy level as needed
light.data.shadow_soft_size = 0.1
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['Cube'].select_set(True)
bpy.ops.object.delete()

glb_path = args.glb
bpy.ops.import_scene.gltf(filepath=glb_path)

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'RENDERED'
                break

bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
current_directory = os.getcwd()

scene_dirs = sorted([d for d in os.listdir(current_directory) if os.path.isdir(d) and d.startswith("scene_") and d.endswith("_animation")])

bpy.ops.object.select_all(action='DESELECT')
armature = None
for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        armature = obj
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
        break

if not armature:
    raise RuntimeError("No armature found in the scene.")

if os.path.exists(args.folder + '/scene'):
    shutil.rmtree(args.folder + '/scene')
    time.sleep(2)
os.mkdir(args.folder + '/scene')

count = 0
for i in range(len(scene_dirs) - 1):
    start_file_path = os.path.join(scene_dirs[i], "1.txt")
    end_file_path = os.path.join(scene_dirs[i+1], "1.txt")

    if os.path.isfile(start_file_path) and os.path.isfile(end_file_path):
        start_data = read_bone_data(start_file_path)
        end_data = read_bone_data(end_file_path)

        for j in range(30): 
            factor = j / 30.0
            interpolated_data = interpolate_data(start_data, end_data, factor)
            update_bone_rotations(interpolated_data, armature)

            armature.scale = (interpolated_data['width_ratio'], interpolated_data['height_ratio'], 1)
            bpy.context.view_layer.update()
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.camera_add(location=(0, -5, 0))
            camera = bpy.context.object
            bpy.context.scene.camera = camera
            camera.rotation_euler = (1.61, 0, 0)  

            os.mkdir(args.folder + '/scene/frame_' + str(count))
            output_image_name = args.folder + '/scene/frame_' + str(count) + '/frame.png'
            
            count += 1
            output_image_path = os.path.join(current_directory, output_image_name)
            bpy.context.scene.render.filepath = output_image_path
            bpy.ops.render.render(write_still=True)

            print(f"Image saved to {output_image_path}")

            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[camera.name].select_set(True)
            bpy.ops.object.delete()

            armature.select_set(True)
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='POSE')

print("All images have been rendered and saved.")
time.sleep(3)
logo = cv2.imread(args.logo)
logo = cv2.resize(logo, (logo.shape[1] // 3, logo.shape[0] // 3)) 
non_white_pixels = np.where((logo[:, :, :3] != [255, 255, 255]).any(axis=2))
output_video_path = args.folder + '/scene/output.mp4'

png_files = []
img = cv2.imread(args.folder + "/scene/frame_0/frame.png")
fps = 120
video = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (img.shape[1], img.shape[0]))

for i in range(30 * (len(scene_dirs) - 1)):
    png_files.append(args.folder + "/scene/frame_" + str(i) + "/frame.png")
print(png_files)
for png_file in png_files:
    print("hello", (png_file))
    img = cv2.imread(png_file)
    img[-logo.shape[0]-30:, -logo.shape[1]-30:][non_white_pixels] = logo[non_white_pixels]
    video.write(img)
    video.write(img)
    video.write(img)
    video.write(img)
    video.write(img)
    video.write(img)
    video.write(img)
    
video.release()

# Remove all directories ending with '_animation'
# current_directory = os.getcwd()
# for dir_name in scene_dirs:
#     dir_path = os.path.join(current_directory, dir_name)
#     shutil.rmtree(dir_path)
#     print(f"Removed directory: {dir_path}")
# if os.path.exists('rigged.glb'):
#     os.remove('rigged.glb')
# print(f"Removed file: glb")

