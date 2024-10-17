# https://github.com/krrish94/nerf-pytorch

import os
import time
import pdb

import imageio
import numpy as np
import torch
import torchvision
import yaml

from nerf import (
    CfgNode,
    get_ray_bundle,
    models,
    get_embedding_function,
    run_one_iter_of_nerf,
)

def cast_to_image(tensor, dataset_type):
    tensor = tensor.permute(2, 0, 1)
    img = np.array(torchvision.transforms.ToPILImage()(tensor.detach().cpu()))
    return img

def cast_to_disparity_image(tensor):
    img = (tensor - tensor.min()) / (tensor.max() - tensor.min())
    img = img.clamp(0, 1) * 255
    return img.detach().cpu().numpy().astype(np.uint8)

def get_render_image(vector_magnitude, rotation_matrix, focal_length, data, file_name):
    config_file_path = f'{data.data_path}/config.yml'
    checkpoint_file_path = f'{data.data_path}/checkpoint{data.iterations-1}.ckpt'

    cfg = None
    with open(config_file_path, "r") as f:
        cfg_dict = yaml.load(f, Loader=yaml.FullLoader)
        cfg = CfgNode(cfg_dict)
    checkpoint = torch.load(checkpoint_file_path)

    # Device on which to run.
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"

    encode_position_fn = get_embedding_function(
        num_encoding_functions=cfg.models.coarse.num_encoding_fn_xyz,
        include_input=cfg.models.coarse.include_input_xyz,
        log_sampling=cfg.models.coarse.log_sampling_xyz,
    )

    encode_direction_fn = None
    if cfg.models.coarse.use_viewdirs:
        encode_direction_fn = get_embedding_function(
            num_encoding_functions=cfg.models.coarse.num_encoding_fn_dir,
            include_input=cfg.models.coarse.include_input_dir,
            log_sampling=cfg.models.coarse.log_sampling_dir,
        )

    # Initialize a coarse resolution model.
    model_type = data.model_type
    model_coarse = getattr(models, cfg.models.coarse.type)(
        num_layers=cfg.models.coarse.num_layers,
        hidden_size=cfg.models.coarse.hidden_size,
        skip_connect_every=cfg.models.coarse.skip_connect_every,
        num_encoding_fn_xyz=cfg.models.coarse.num_encoding_fn_xyz,
        num_encoding_fn_dir=cfg.models.coarse.num_encoding_fn_dir,
        include_input_xyz=cfg.models.coarse.include_input_xyz,
        include_input_dir=cfg.models.coarse.include_input_dir,
        use_viewdirs=cfg.models.coarse.use_viewdirs,
        model_type=model_type,
    )
    model_coarse.to(device)

    # If a fine-resolution model is specified, initialize it.
    model_fine = None
    if hasattr(cfg.models, "fine"):
        model_fine = getattr(models, cfg.models.fine.type)(
            num_layers=cfg.models.fine.num_layers,
            hidden_size=cfg.models.fine.hidden_size,
            skip_connect_every=cfg.models.fine.skip_connect_every,
            num_encoding_fn_xyz=cfg.models.fine.num_encoding_fn_xyz,
            num_encoding_fn_dir=cfg.models.fine.num_encoding_fn_dir,
            include_input_xyz=cfg.models.fine.include_input_xyz,
            include_input_dir=cfg.models.fine.include_input_dir,
            use_viewdirs=cfg.models.fine.use_viewdirs,
            model_type=model_type,
        )
        model_fine.to(device)

    coarse_model_secondary_list = []
    fine_model_secondary_list = []

    model_coarse.load_state_dict(checkpoint["model_coarse_state_dict"])
    if checkpoint["model_fine_state_dict"]:
        try:
            model_fine.load_state_dict(checkpoint["model_fine_state_dict"])
        except:
            print(
                "The checkpoint has a fine-level model, but it could "
                "not be loaded (possibly due to a mismatched config file."
            )

    hwf = [800, 800, focal_length]

    model_coarse.eval()
    if model_fine:
        model_fine.eval()

    def rotate_by_phi_along_x(phi):
        tform = np.eye(4).astype(np.float32)
        tform[1, 1] = tform[2, 2] = np.cos(phi)
        tform[1, 2] = -np.sin(phi)
        tform[2, 1] = -tform[1, 2]
        return tform

    translationMatrix = np.eye(4).astype(np.float32)
    translationMatrix[2, 3] = 4.0 if vector_magnitude >= 4.0 else vector_magnitude
    rotationMatrix = np.linalg.inv(rotation_matrix)
    tranformationMatrix = rotate_by_phi_along_x(-90 / 180.0 * np.pi) @ np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]) @ rotationMatrix @ translationMatrix

    render_poses = torch.stack(
        [
            torch.from_numpy(tranformationMatrix)
        ],
        0,
    )

    render_poses = render_poses.float().to(device)

    save_dir = '.'

    # Evaluation loop
    times_per_image = []
    for i, pose in enumerate(render_poses):
        start = time.time()
        rgb = None, None
        disp = None, None
        with torch.no_grad():
            pose = pose[:3, :4]
            ray_origins, ray_directions = get_ray_bundle(hwf[0], hwf[1], hwf[2], pose)
            outputs \
                = run_one_iter_of_nerf(
                    hwf[0],
                    hwf[1],
                    hwf[2],
                    model_coarse,
                    model_fine,
                    [],
                    [],
                    ray_origins,
                    ray_directions,
                    cfg,
                    mode="validation",
                    encode_position_fn=encode_position_fn,
                    encode_direction_fn=encode_direction_fn,
                    model_type=model_type,
                )
            
            rgb_coarse = outputs[0]
            rgb_fine = outputs[3]

            rgb = rgb_fine if rgb_fine is not None else rgb_coarse
            # if configargs.save_disparity_image:
            #     disp = disp_fine if disp_fine is not None else disp_coarse
        times_per_image.append(time.time() - start)
        if save_dir:
            savefile = f"{file_name}"
            imageio.imwrite(
                savefile, cast_to_image(rgb[..., :3], cfg.dataset.type.lower())
            )