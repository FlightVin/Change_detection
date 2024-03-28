# import os
# import cv2
# import numpy as np
# import shutil

# def png_to_npy(png_dir, npy_dir):
#     # Create the output directory if it doesn't exist
#     os.makedirs(npy_dir, exist_ok=True)
    
#     # List all PNG files in the input directory
#     png_files = [f for f in os.listdir(png_dir) if f.endswith('.png')]
    
#     for png_file in png_files:
#         # Read PNG image
#         img = cv2.imread(os.path.join(png_dir, png_file), cv2.IMREAD_GRAYSCALE)
        
#         # Save as NumPy array with the same file name
#         npy_file = os.path.splitext(png_file)[0] + '.npy'
#         np.save(os.path.join(npy_dir, npy_file), img)

# # Specify input and output directories
# png_dir = '/scratch/vineeth.bhat/sequence2/depth_corrected'
# npy_dir = '/scratch/vineeth.bhat/sequence2/depth_corrected_npy'

# if os.path.exists(npy_dir):
#     shutil.rmtree(npy_dir)

# # Convert PNG to NumPy
# png_to_npy(png_dir, npy_dir)


# import os
# import cv2

# # Define input and output directories
# input_dir = "/scratch/vineeth.bhat/sequence2/depth"
# output_dir = "/scratch/vineeth.bhat/sequence2/depth_corrected"

# # Create output directory if it doesn't exist
# if not os.path.exists(output_dir):
#     os.makedirs(output_dir)

# # Define target shape
# target_width = 300
# target_height = 300

# # Iterate through images in the input directory
# for filename in os.listdir(input_dir):
#     if filename.endswith(".png"):
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
input_dir = "/scratch/vineeth.bhat/sequence2/depth_corrected_npy"
output_dir = "/scratch/vineeth.bhat/sequence2/depth_corrected_npy_new"

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

        print(np_array.shape)
        print(np.max(np_array))
        
        corrected_array = np_array * (100 / 65535) 
        
        # Save corrected array to output directory
        output_path = os.path.join(output_dir, filename)
        np.save(output_path, corrected_array)

        print(f"Corrected {filename} and saved to {output_path}")

