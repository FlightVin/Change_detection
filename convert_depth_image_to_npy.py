# import os
# import cv2
# import numpy as np

# def png_to_npy(png_dir, npy_dir):
#     # Create the output directory if it doesn't exist
#     os.makedirs(npy_dir, exist_ok=True)
    
#     # List all PNG files in the input directory
#     png_files = [f for f in os.listdir(png_dir) if f.endswith('.png')]
    
#     for png_file in png_files:
#         # Read PNG image
#         img = cv2.imread(os.path.join(png_dir, png_file), cv2.IMREAD_UNCHANGED)
        
#         # Save as NumPy array with the same file name
#         npy_file = os.path.splitext(png_file)[0] + '.npy'
#         np.save(os.path.join(npy_dir, npy_file), img)

# # Specify input and output directories
# png_dir = '/scratch/vineeth.bhat/mainlab_scan_2/depth'
# npy_dir = '/scratch/vineeth.bhat/mainlab_scan_2/depth_npy'

# # Convert PNG to NumPy
# png_to_npy(png_dir, npy_dir)


# import os
# import cv2

# # Define input and output directories
# input_dir = "/scratch/vineeth.bhat/mainlab_scan_2/rgb"
# output_dir = "/scratch/vineeth.bhat/mainlab_scan_2/rgb_shape_corrected"

# # Create output directory if it doesn't exist
# if not os.path.exists(output_dir):
#     os.makedirs(output_dir)

# # Define target shape
# target_width = 192
# target_height = 256

# # Iterate through images in the input directory
# for filename in os.listdir(input_dir):
#     if filename.endswith(".jpg"):
#         # Read image
#         img_path = os.path.join(input_dir, filename)
#         img = cv2.imread(img_path)
        
#         # Resize image
#         resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)
        
#         # Save resized image to output directory
#         output_path = os.path.join(output_dir, filename)
#         cv2.imwrite(output_path, resized_img)

#         print(f"Resized {filename} to ({target_width}, {target_height}) and saved to {output_path}")

import os
import shutil
import numpy as np

# Define input and output directories
input_dir = "/scratch/vineeth.bhat/mainlab_scan_2/depth_npy"
output_dir = "/scratch/vineeth.bhat/mainlab_scan_2/depth_npy_corrected"

# If output directory exists, delete it and everything in it
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)

# Create output directory
os.makedirs(output_dir)

# Iterate through files in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".npy"):
        # Load numpy array
        file_path = os.path.join(input_dir, filename)
        np_array = np.load(file_path)
        
        # Multiply each element by 5/70000
        corrected_array = np_array * (1/10)
        
        # Save corrected array to output directory
        output_path = os.path.join(output_dir, filename)
        np.save(output_path, corrected_array)

        print(f"Corrected {filename} and saved to {output_path}")

