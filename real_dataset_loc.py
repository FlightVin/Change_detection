from object_memory import *
import ast, pickle, shutil, time
import psutil, os
import pdb, pickle
import csv

@dataclass
class LocalArgs:
    """
    Class to hold local configuration arguments.
    """
    lora_path: str='models/vit_finegrained_5x40_procthor.pt'
    test_folder_path: str='/scratch/vineeth.bhat/sequence2'
    rearranged_test_folder_path: str='/scratch/vineeth.bhat/sequence2' # basically the dataset of the stuff ebing localised
    pose_file: str='/scratch/vineeth.bhat/sequence2/poses.csv'
    device: str='cuda'
    sam_checkpoint_path: str = '/scratch/vineeth.bhat/sam_vit_h_4b8939.pth'
    ram_pretrained_path: str = '/scratch/vineeth.bhat/ram_swin_large_14m.pth'
    downsampling_rate: int = 1000 # downsample points every these many frames


    save_dir: str = "/scratch/vineeth.bhat/results/real-lora"
    sampling_period: int = 1
    start_file_index: int = 3
    last_file_index: int = 20
    rot_correction: float = 0.0 # keep as 30 for 8-room-new 
    look_around_range: int = 0 # number of sucessive frames to consider at every frame
    save_individual_objects: bool = True
    save_localised_objects: bool = True

    add_pose_noise: bool = False # already noisy

    down_sample_voxel_size: float = 0.01 # best results
    create_ext_mesh: bool = False
    save_point_clouds: bool = False
    fpfh_global_dist_factor: float = 1.5
    fpfh_local_dist_factor: float = 0.4
    fpfh_voxel_size: float = 0.05   
    localise_times: int = 1

    loc_results_start_file_index: int = 4
    loc_results_last_file_index: int = -1
    loc_results_sampling_period: int = 10

    useLora: bool=True

    reid_config_file: str = "./FourDNet-wrapper/config.yml"
    reid_model: str = "/scratch/vineeth.bhat/FourDNet/procthor_final.pth"
    reid_num_classes: int = 69
    reid_model_pretrain_path: str = "/scratch/vineeth.bhat/FourDNet/checkpoints/jx_vit_base_p16_224-80ecf9dd.pth"

    min_points: int = 500

if __name__=="__main__":
    start_time = time.time()

    largs = tyro.cli(LocalArgs, description=__doc__)
    print(largs)

    # creating save dir
    os.makedirs(largs.save_dir, exist_ok=True)
    print(f"Created save directory {largs.save_dir}")

    files = os.listdir(os.path.join(largs.test_folder_path, "color_corrected"))
    num_files = len(files)
    print(f"We have {num_files} files")

    poses = {}
    csv_file_path = largs.pose_file  # Change this to the path of your CSV file
    with open(csv_file_path, newline='') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        next(csv_reader)  # Skip the header row
        for row in csv_reader:
            ID = int(row[0])
            Tx,	Ty,	Tz,	Qw,	Qx,	Qy,	Qz = [float(val) for val in row[1:]]
            values = np.array([Tx,Ty,Tz,Qw,Qx,Qy,Qz])
            poses[ID] = values


    print("\nBegin Memory Initialization")
    if largs.useLora:
        mem = ObjectMemory(device = largs.device, 
                        ram_pretrained_path=largs.ram_pretrained_path,
                        sam_checkpoint_path = largs.sam_checkpoint_path,
                        lora_path=largs.lora_path)
    else:
        mem = ObjectMemory(device = largs.device, 
                        ram_pretrained_path=largs.ram_pretrained_path,
                        sam_checkpoint_path = largs.sam_checkpoint_path,
                        lora_path=largs.lora_path, reid_largs = largs)
    print("Memory Init'ed\n")

    if largs.last_file_index == -1:
        largs.last_file_index = num_files
    if largs.loc_results_last_file_index == -1:
        largs.loc_results_last_file_index = num_files

    frame_counter = 0

    for cur_frame in tqdm(range(largs.start_file_index, largs.last_file_index + 1, largs.sampling_period), total=(largs.last_file_index-largs.start_file_index)//largs.sampling_period):
        for i in range(cur_frame, min(largs.last_file_index + 1, cur_frame + largs.look_around_range + 1)):
            print(f"\n\tSeeing image {i} currently")

            file_num = "{:03d}".format(i)
            image_file_path = os.path.join(largs.test_folder_path, 
                                        f"color_corrected/{file_num}.jpg")
            depth_file_path = os.path.join(largs.test_folder_path, 
                                        f"depth_corrected_npy/{file_num}.npy")
            # pose_file_path = os.path.join(largs.test_folder_path, 
            #                             f"pose/{i}.txt")

            
            # with open(pose_file_path, 'r') as file:
            #     pose_dict = file.read()
            # pose_dict = ast.literal_eval(pose_dict)
            # pose_dict = {
            #     "position": {
            #         "x": pose_dict[0]['x'],
            #         "y": pose_dict[0]['y'],
            #         "z": pose_dict[0]['z']
            #     },
            #     "rotation": {
            #         "x": pose_dict[1]['x'] + largs.rot_correction,
            #         "y": pose_dict[1]['y'],
            #         "z": pose_dict[1]['z']
            #     }
            # }

            # q = Rotation.from_euler('xyz', [r for _, r in pose_dict["rotation"].items()], degrees=True).as_quat()
            # t = np.array([x for _, x in pose_dict["position"].items()])
            # pose = np.concatenate([t, q])

            pose = poses[i]

            mem.process_image(testname=f"view%d" % i, 
                                image_path = image_file_path, 
                                depth_image_path = depth_file_path, 
                                pose=pose,
                                verbose=False, add_noise=largs.add_pose_noise, 
                                useLora = largs.useLora, min_points = largs.min_points,
                                outlier_removal_config = "")
            
            pid = psutil.Process()
            memory_info = pid.memory_info()
            memory_info_GBs = memory_info.rss / (1e3 ** 3)
            print(f"Memory usage: {memory_info_GBs:.3f} GB")

            cuda_memory_stats = torch.cuda.memory_stats()
            max_cuda_memory_GBs = int(cuda_memory_stats["allocated_bytes.all.peak"]) / (1e3 ** 3)
            print(f"Max GPU memory usage: {max_cuda_memory_GBs:.3f} GB")

            print("\t ----------------")

            if frame_counter % largs.downsampling_rate == 0:
                
                #     # begin debug
                # if i > 60:
                #     pcd_list = []
                    
                #     for info in mem.memory:
                #         object_pcd = info.pcd
                #         pcd_list.append(object_pcd)

                #     combined_pcd = o3d.geometry.PointCloud()

                #     for bhencho in range(len(pcd_list)):
                #         pcd_np = pcd_list[bhencho]
                #         pcd_vec = o3d.utility.Vector3dVector(pcd_np.T)
                #         pcd = o3d.geometry.PointCloud()
                #         pcd.points = pcd_vec
                #         pcd.paint_uniform_color(np.random.rand(3))
                #         combined_pcd += pcd

                #     save_path = os.path.join(largs.save_dir, 
                #         f"/home2/vineeth.bhat/Change_detection/temp/{i}_before_cons.pcd")
                #     o3d.io.write_point_cloud(save_path, combined_pcd)
                #     print("Memory's pointcloud saved to", save_path)

                #     # end debug

                if largs.down_sample_voxel_size > 0:
                    print(f"Downsampling at {frame_counter} frame voxel size as {largs.down_sample_voxel_size}")
                    mem.downsample_all_objects(voxel_size=largs.down_sample_voxel_size)
                    mem.consolidate_memory()
                mem.remove_object_floors()


                # # begin debug
                # if i > 60:
                #     pcd_list = []
                    
                #     for info in mem.memory:
                #         object_pcd = info.pcd
                #         pcd_list.append(object_pcd)

                #     combined_pcd = o3d.geometry.PointCloud()

                #     for bhencho in range(len(pcd_list)):
                #         pcd_np = pcd_list[bhencho]
                #         pcd_vec = o3d.utility.Vector3dVector(pcd_np.T)
                #         pcd = o3d.geometry.PointCloud()
                #         pcd.points = pcd_vec
                #         pcd.paint_uniform_color(np.random.rand(3))
                #         combined_pcd += pcd

                #     save_path = os.path.join(largs.save_dir, 
                #         f"/home2/vineeth.bhat/Change_detection/temp/{i}_after_cons.pcd")
                #     o3d.io.write_point_cloud(save_path, combined_pcd)
                #     print("Memory's pointcloud saved to", save_path)

                    # pdb.set_trace()
                # end debug

            frame_counter += 1


    if largs.down_sample_voxel_size > 0:
        print(f"Downsampling using voxel size as {largs.down_sample_voxel_size}")
        mem.downsample_all_objects(voxel_size=largs.down_sample_voxel_size)

    end_time = time.time()
    print(f"Traversal completed in {end_time - start_time} seconds")

    pcd_list = []
    
    for info in mem.memory:
        object_pcd = info.pcd
        pcd_list.append(object_pcd)

    combined_pcd = o3d.geometry.PointCloud()

    if largs.save_localised_objects:
        localised_mem_save_dir = os.path.join(largs.save_dir,
            f"localised_mems")
        os.makedirs(localised_mem_save_dir, exist_ok=True)

    if largs.save_individual_objects:
        individual_mem_save_dir = os.path.join(largs.save_dir,
            f"ind_mems")
        os.makedirs(individual_mem_save_dir, exist_ok=True)

    for i in range(len(pcd_list)):
        pcd_np = pcd_list[i]
        pcd_vec = o3d.utility.Vector3dVector(pcd_np.T)
        pcd = o3d.geometry.PointCloud()
        pcd.points = pcd_vec

        if largs.save_individual_objects:
            cur_save_path = os.path.join(individual_mem_save_dir, 
                f"memory_{i}.pcd") 

            o3d.io.write_point_cloud(cur_save_path, pcd)
            print(f"{i} pointcloud saved to", cur_save_path)

        combined_pcd += pcd

    save_path = os.path.join(largs.save_dir, 
        f"mem.pcd")
    o3d.io.write_point_cloud(save_path, combined_pcd)
    print("Memory's pointcloud saved to", save_path)

    print("\n\n\t---------------------")
    mem.view_memory()

    start_time = time.time()

    tgt = []
    pred = []
    trans_errors = []
    rot_errors = []
    chosen_assignments = []

    for n, i in tqdm(enumerate(range(largs.loc_results_start_file_index, 
                   largs.loc_results_last_file_index + 1, 
                   largs.loc_results_sampling_period)), total=(largs.loc_results_start_file_index-largs.loc_results_start_file_index)//largs.loc_results_sampling_period):
        print(f"\n\tLocalizing image {i} currently")
        image_file_path = os.path.join(largs.rearranged_test_folder_path, 
                                    f"rgb/{i}.png")
        depth_file_path = os.path.join(largs.rearranged_test_folder_path, 
                                    f"depth_npy/{i}.npy")
        pose_file_path = os.path.join(largs.rearranged_test_folder_path, 
                                    f"pose/{i}.txt")

        
        with open(pose_file_path, 'r') as file:
            pose_dict = file.read()
        pose_dict = ast.literal_eval(pose_dict)
        pose_dict = {
            "position": {
                "x": pose_dict[0]['x'],
                "y": pose_dict[0]['y'],
                "z": pose_dict[0]['z']
            },
            "rotation": {
                "x": pose_dict[1]['x'] + largs.rot_correction,
                "y": pose_dict[1]['y'],
                "z": pose_dict[1]['z']
            }
        }

        q = Rotation.from_euler('xyz', [r for _, r in pose_dict["rotation"].items()], degrees=True).as_quat()
        t = np.array([x for _, x in pose_dict["position"].items()])
        target_pose = np.concatenate([t, q])
        tgt.append(target_pose)
            
        if largs.save_localised_objects:
            estimated_pose, chosen_assignment = mem.localise(image_path=image_file_path, 
                                            depth_image_path=depth_file_path,
                                            save_point_clouds=largs.save_point_clouds,
                                            fpfh_global_dist_factor = largs.fpfh_global_dist_factor, 
                                            fpfh_local_dist_factor = largs.fpfh_global_dist_factor, 
                                            fpfh_voxel_size = largs.fpfh_voxel_size,
                                            save_localised_pcd_path = localised_mem_save_dir, useLora = largs.useLora)
        else:
            estimated_pose, chosen_assignment = mem.localise(image_path=image_file_path, 
                                            depth_image_path=depth_file_path,
                                            save_point_clouds=largs.save_point_clouds,
                                            fpfh_global_dist_factor = largs.fpfh_global_dist_factor, 
                                            fpfh_local_dist_factor = largs.fpfh_global_dist_factor, 
                                            fpfh_voxel_size = largs.fpfh_voxel_size, useLora = largs.useLora)

        # save detected objs
        _, _, detected_pcds = mem._get_object_info(image_path=image_file_path, depth_image_path=depth_file_path, useLora=largs.useLora)
        if largs.save_individual_objects and detected_pcds is not None:
            p = o3d.geometry.PointCloud()
            for j, det_pcd in enumerate(detected_pcds):
                save_path = os.path.join(individual_mem_save_dir,
                    f"detected_img_{n}_{j}.pcd")
                p.points = o3d.utility.Vector3dVector(det_pcd.T)
                o3d.io.write_point_cloud(save_path, p)
                print(f"Img {i} obj {j} pointcloud saved to", save_path)


        print("Target pose: ", target_pose)
        print("Estimated pose: ", estimated_pose)

        translation_error = np.linalg.norm(target_pose[:3] - estimated_pose[:3]) 
        rotation_error = QuaternionOps.quaternion_error(target_pose[3:], estimated_pose[3:])

        print("Translation error: ", translation_error)
        print("Rotation_error: ", rotation_error)

        # ## DEBUG
        # if detected_pcds is not None:
        #     print("DEBUG BEGINS")
        #     print(f"Detectec len {len(detected_pcds)}")

        #     outlier_removal_config = {
        #             "radius_nb_points": 8,
        #             "radius": 0.05,
        #         }

        #     assn = chosen_assignment[0]
        #     all_detected_points = []
        #     all_memory_points = []

        #     for pcd in detected_pcds:
        #         all_detected_points.append(pcd)
        #     for info in mem.memory:
        #         all_memory_points.append(info.pcd)

        #     all_detected_points = np.concatenate(all_detected_points, axis=-1).T
        #     all_memory_points = np.concatenate(all_memory_points, axis=-1).T

        #     all_detected_pcd = o3d.geometry.PointCloud()
        #     all_memory_pcd = o3d.geometry.PointCloud()

        #     all_detected_pcd.points = o3d.utility.Vector3dVector(all_detected_points)
        #     all_memory_pcd.points = o3d.utility.Vector3dVector(all_memory_points)

        #     # all_detected_pcd_filtered, _ = all_detected_pcd.remove_radius_outlier(nb_points=outlier_removal_config["radius_nb_points"],
        #     #                                         radius=outlier_removal_config["radius"])

        #     all_memory_pcd = all_memory_pcd.voxel_down_sample(0.05)
        #     all_memory_pcd.paint_uniform_color([0,1,1])
        #     all_detected_pcd.paint_uniform_color([1,0,0])
            
        #     print("points: ", all_detected_points)

        #     o3d.io.write_point_cloud(f"./temp/{str(assn)}-{i}-ISTHISIT.ply", all_detected_pcd)

        #     transform = np.eye(4)
        #     transform[:3,:3] = Rotation.from_quat(estimated_pose[3:]).as_matrix()
        #     transform[:3, 3] = estimated_pose[:3]

        #     print(transform)

        #     o3d.io.write_point_cloud(f"./temp/{str(assn)}-{i}-full_aligned.ply", all_memory_pcd + 
        #                             all_detected_pcd.transform(transform))
        #     o3d.io.write_point_cloud(f"./temp/{str(assn)}-{i}-full_aligned_test.ply", all_detected_pcd.transform(transform))
            
        #     # import pdb;
        #     # if len(detected_pcds) > 0:
        #     #     pdb.set_trace()
        #     ## END DEBUG

        pred.append(estimated_pose.tolist())
        trans_errors.append(translation_error)
        rot_errors.append(rotation_error)
        chosen_assignments.append(chosen_assignment)

        # if n % 10 == 0:
        #     for ii in range(len(trans_errors)):
        #         print(f"Pose {i + 1}")
        #         print("Translation error", trans_errors[ii])
        #         print("Rotation errors", rot_errors[ii])
        #         print("Assignment: ", chosen_assignments[ii][0])
        #         print("Moved objects: ", chosen_assignments[ii][1])

    for i in range(len(trans_errors)):
        print(f"Pose {i + 1}")
        print("Translation error", trans_errors[i])
        print("Rotation errors", rot_errors[i])
        print("Assignment: ", chosen_assignments[i][0])
        print("Moved objects: ", chosen_assignments[i][1])

    results = {
        "translation_errors": trans_errors,
        "rotation_errors": rot_errors,
        "assignments": chosen_assignments,
    }

    save_path = os.path.join(largs.save_dir, 
        f"results.pkl")
    with open(save_path, "wb") as f:
        pickle.dump(results, f)
    print("Resuts saved to", save_path)

    end_time = time.time()
    print(f"Localization completed in {end_time - start_time} seconds")
