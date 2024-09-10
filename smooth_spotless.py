import bpy
import os
import cv2 # "C:\Program Files\Blender Foundation\Blender <version>\python\bin\python.exe" -m pip install opencv-python
import numpy as np
from sklearn.cluster import KMeans

class ClusteringImgColor:    
    def convert_rgb_to_hsv(image):
        # Convert from RGB to HSV using OpenCV
        return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    def cluster_pixels(image, n_clusters=5):
        # Reshape the image to a 2D array of pixels
        pixels = image.reshape(-1, 3).astype(np.float32)
        
        # Create and fit the KMeans model
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(pixels)
        
        # Get the cluster centers (mean colors)
        cluster_centers = kmeans.cluster_centers_.astype(np.uint8)
        
        # Predict the cluster for each pixel
        labels = kmeans.predict(pixels)
        
        return labels, cluster_centers

    def apply_kmeans_to_image(labels, cluster_centers, image_shape):
        # Map each pixel to its cluster center color
        new_pixels = np.array([cluster_centers[label] for label in labels], dtype=np.uint8)
        
        # Reshape the result back to the original image shape
        new_image = new_pixels.reshape(image_shape)
        
        return new_image

    def convert_hsv_to_rgb(image):
        # Convert from HSV to RGB using OpenCV
        return cv2.cvtColor(image, cv2.COLOR_HSV2RGB)

    def kmean_clustering(image, n_clusters):
        # Convert RGB to HSV
        hsv_image = ClusteringImgColor.convert_rgb_to_hsv(image)
        
        # Cluster the pixels in the HSV color space
        labels, cluster_centers = ClusteringImgColor.cluster_pixels(hsv_image, n_clusters=n_clusters)  # Adjust number of clusters as needed
        
        # Apply the K-Means result to the image
        clustered_hsv_image = ClusteringImgColor.apply_kmeans_to_image(labels, cluster_centers, hsv_image.shape)
        
        # Convert the clustered HSV image back to RGB
        clustered_rgb_image = ClusteringImgColor.convert_hsv_to_rgb(clustered_hsv_image)
        
        # Convert RGB back to BGR for OpenCV
        clustered_bgr_image = cv2.cvtColor(clustered_rgb_image, cv2.COLOR_RGB2BGR)

        return clustered_rgb_image, clustered_bgr_image
    
def kMean_Img(original_img_path, labeled_texture_map, n_cluster=10):
    original_img = cv2.imread(original_img_path)
    original_img_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
    clustered_rgb_image, clustered_bgr_image = ClusteringImgColor.kmean_clustering(original_img_rgb, n_cluster)

    cv2.imwrite(labeled_texture_map, clustered_bgr_image)
    return labeled_texture_map, clustered_bgr_image

def del_existing_objs():
    # Clear any existing objects
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
        
def add_subdivision_and_recalculate_normals(obj):
    bpy.context.view_layer.objects.active = obj

    # Enter Edit Mode to recalculate normals
    bpy.ops.object.mode_set(mode='EDIT')

    # Subdivide the selected faces
    bpy.ops.mesh.subdivide(number_cuts=2)
    
    # Smooth shading (faces)
    bpy.ops.mesh.faces_shade_smooth()
    
    # Recalculate normals outside
    bpy.ops.mesh.normals_make_consistent(inside=False)
    
    # Switch back to Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')
def cur_filepath(img_name):
    if bpy.data.filepath:
        # Extract the directory from the file path
        folder_path = os.path.dirname(bpy.data.filepath)
        
        # Set the file path for saving the image
        return os.path.join(folder_path, img_name)
    else:
        return img_name
        
def texture_conv(uv_texture, mode = 1, brightness = 1.3):
    # Path to the modified texture map
    modified_texture_path = 'brightened_texture_map.png'
    labeled_texture_path =  'labeled_texture_map.png'
    # Applying Gaussian Blur
    gaussian_texture_path = 'gaussian_texture_map.png'
    # Using Bilateral Filter
    filtered_texture_path = 'filtered_texture_map.png'
    # Applying Non-Local Means Denoising
    denoised_texture_path = 'denoised_texture_map.png'
    
    # Convert image to float to prevent overflow issues
    texture_image_float = uv_texture.astype(np.float32)

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
    cv2.imwrite(cur_filepath(modified_texture_path), denoised_image)

    _, labeled_image = kMean_Img(cur_filepath(modified_texture_path), cur_filepath(labeled_texture_path))
    
    print(f'Modified texture saved to {modified_texture_path}')
    print(f'Labeled texture saved to {labeled_texture_path}')
    if (mode == 1):
        return labeled_texture_path, labeled_image
    else:
        return modified_texture_path, denoised_image

def import_obj_change_uv_texture(filepath, mode = 1, brightness = 1.3):
    # Specify the path where you want to save the texture map
    export_texture_path = "texture_map.png"
    modified_texture_path = r""

    if os.path.exists(filepath):
        bpy.ops.import_scene.gltf(filepath=filepath)
    else:
        print("File does not exist:", filepath)

    # Apply smooth shading
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            
            add_subdivision_and_recalculate_normals(obj)
            
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
                        texture_node.image.save_render(filepath=cur_filepath(export_texture_path))
                        print(f'Texture saved to {export_texture_path}')

                        # Load the texture map
                        texture_image = cv2.imread(cur_filepath(export_texture_path))
                        
                        modified_texture_path, _ = texture_conv(texture_image, mode, brightness)
                    else:
                        print('No image texture found on the material.')
                else:
                    print('Material does not use nodes.')
            else:
                print('Object has no materials.')

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
                            bsdf.inputs['Metallic'].default_value = 0.4
                            bsdf.inputs['Roughness'].default_value = 0.8
                            print('Metallic value set to 0.4, Roughness value set to 0.8')
                            
                            # Check if there's an existing texture node connected to Base Color
                            texture_node = None
                            for link in links:
                                if link.to_node == bsdf and link.to_socket.name == 'Base Color':
                                    texture_node = link.from_node
                                    break
                            
                            if texture_node and texture_node.type == 'TEX_IMAGE':
                                # Load the new image
                                new_image = bpy.data.images.load(cur_filepath(modified_texture_path))
                                
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

if __name__ == "__main__":
    basepath = r"D:\Projects\GLB-preprocess\characters\4"

    # Check if file exists
    filepath = os.path.join(basepath, r'final.glb')

    #brightness
    mode = 2 # 1: KMean, 2: Denoise
    brightness = 1.3
    
    del_existing_objs()
    import_obj_change_uv_texture(filepath, mode, brightness)
        
    # Export the processed GLB file
    bpy.ops.export_scene.gltf(filepath=os.path.join(basepath, f'output_smoothed_{mode}.glb'), export_format='GLB')
