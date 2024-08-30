import bpy
import os
import cv2 # "C:\Program Files\Blender Foundation\Blender <version>\python\bin\python.exe" -m pip install opencv-python
import numpy as np

# Clear any existing objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Check if file exists
filepath = r"D:\Projects\GLB-preprocess\characters\1\final.glb"
# Specify the path where you want to save the texture map
export_path = r"./texture_map.png"
# Path to the modified texture map
modified_texture_path = r"./brightened_texture_map.png"
# Applying Gaussian Blur
gaussian_texture_path = 'gaussian_texture_map.png'
# Using Bilateral Filter
filtered_texture_path = 'filtered_texture_map.png'
# Applying Non-Local Means Denoising
denoised_texture_path = 'denoised_texture_map.png'

#brightness
brightness = 1.3

if os.path.exists(filepath):
    bpy.ops.import_scene.gltf(filepath=filepath)
else:
    print("File does not exist:", filepath)

# Apply smooth shading
for obj in bpy.context.selected_objects:
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        
        bpy.ops.object.mode_set(mode='OBJECT')
            
        # Ensure the object has an active material with a texture
        if obj.data.materials:
            mat = obj.data.materials[0]
            if mat.node_tree:
                texture_node = None
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        texture_node = node
                        break

                if texture_node and texture_node.image:
                    # Save the texture image
                    texture_node.image.save_render(filepath=export_path)
                    print(f'Texture saved to {export_path}')

                    # Load the texture map
                    texture_image = cv2.imread(export_path)

                    # Convert image to float to prevent overflow issues
                    texture_image_float = texture_image.astype(np.float32)

                    # Define brightness factor
                    brightness_factor = brightness  # Increase brightness (e.g., 1.5 for 50% brighter)

                    # Adjust brightness
                    bright_texture_image = cv2.convertScaleAbs(texture_image_float * brightness_factor)

                    ## Non-Local Means Denoising method created the smartest uv texture map among below three methods.
                    # # Apply Gaussian Blur
                    # blurred_image = cv2.GaussianBlur(bright_texture_image, (5, 5), 0)

                    # # Apply Bilateral Filter
                    # filtered_image = cv2.bilateralFilter(bright_texture_image, d=9, sigmaColor=75, sigmaSpace=75)

                    # Apply Non-Local Means Denoising
                    denoised_image = cv2.fastNlMeansDenoisingColored(bright_texture_image, None, h=8, hColor=10, templateWindowSize=7, searchWindowSize=21)

                    # Save the modified texture map
                    cv2.imwrite(modified_texture_path, denoised_image)

                    print(f'Modified texture saved to {modified_texture_path}')

                else:
                    print('No image texture found on the material.')
            else:
                print('Material does not use nodes.')
        else:
            print('Object has no materials.')
            
        bpy.ops.object.shade_smooth()

        # Add a Mirror Modifier to achieve symmetry
        mirror_modifier = obj.modifiers.new(name="Mirror", type='MIRROR')
        mirror_modifier.use_axis[0] = True  # X-axis mirroring
        mirror_modifier.use_axis[1] = False  # Y-axis mirroring (if needed)
        mirror_modifier.use_axis[2] = False  # Z-axis mirroring (if needed)

        # Apply the Mirror Modifier
        bpy.ops.object.modifier_apply(modifier="Mirror")

        # Change Base Color node's image as a modified texture image
        if obj:
            # Switch to Object Mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Ensure the object has an active material
            if obj.data.materials:
                mat = obj.data.materials[0]
                
                if mat.use_nodes:
                    # Get the node tree of the material
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    
                    # Check if there is a Principled BSDF node
                    bsdf = None
                    for node in nodes:
                        if node.type == 'BSDF_PRINCIPLED':
                            bsdf = node
                            break
                    
                    if bsdf:
                        # Set the Metallic value to 1
                        bsdf.inputs['Metallic'].default_value = 1.0
                        print('Metallic value set to 1.')
                        
                        # Check if there's an existing texture node connected to Base Color
                        texture_node = None
                        for link in links:
                            if link.to_node == bsdf and link.to_socket.name == 'Base Color':
                                texture_node = link.from_node
                                break
                        
                        if texture_node and texture_node.type == 'TEX_IMAGE':
                            # Load the new image
                            new_image = bpy.data.images.load(os.path.abspath(modified_texture_path))
                            
                            # Update the image in the texture node
                            texture_node.image = new_image
                            print(f'Base Color updated with new image: {modified_texture_path}')
                        else:
                            print('No image texture node found connected to Base Color.')
                    else:
                        print('No Principled BSDF node found in material.')
                else:
                    print('Material does not use nodes.')
            else:
                print('Object has no materials.')
        else:
            print('No active object selected.')

        
# Export the processed GLB file
bpy.ops.export_scene.gltf(filepath=r"D:\Projects\GLB-preprocess\characters\1\output_smoothed.glb", export_format='GLB')
