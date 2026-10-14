'''
OPENNESS PRISMATIC

PLEASE SEND ME TO HELL!
'''


import rasterio as rio 
import rvt.blend
import rvt.vis
import rvt.default
import os 
import numpy as np 
from pathlib import Path 

input_data = Path(r"C:\Users\jakad\OneDrive\Desktop\3d_data\output\Pivola_klasificirano_in_rastirano_mediana.tiff")
output_data = Path(r"C:\Users\jakad\OneDrive\Desktop\3d_data\output\Pivola_Prismatic_Openness_v31.tiff")

with rio.open(input_data) as src:
    print("CRS", src.crs)
    profile=src.profile.copy()

data_dict = rvt.default.get_raster_arr(input_data)
data_arr = data_dict['array']
data_resolution=data_dict['resolution']
data_x_resolution=data_resolution[0]
data_y_resolution=data_resolution[1]
data_no_data=data_dict['no_data']

dict_mhs = rvt.vis.multi_hillshade(
    dem=data_arr,
    resolution_x=data_x_resolution,
    resolution_y=data_y_resolution,
    nr_directions=6,
    sun_elevation=10, 
    ve_factor=1,
    no_data=data_no_data
)

dict_opns = rvt.vis.sky_view_factor(
    dem=data_arr,
    resolution=data_x_resolution,
    svf_n_dir=16,
    svf_r_max=10,
    svf_noise=0,
    ve_factor=0,
    no_data=data_no_data,
    compute_asvf=False,
    compute_opns=True,
    compute_svf=False
)

neg_arr = -data_arr
if data_no_data is not None is not np.isnan(data_no_data):
    neg_arr[data_arr == data_no_data] = data_no_data


dict_neg_opns = rvt.vis.sky_view_factor(
    dem=neg_arr,
    resolution=data_x_resolution,
    svf_n_dir=16,
    svf_r_max=10,
    svf_noise=0,
    ve_factor=1,
    no_data=data_no_data,
    compute_asvf=False,
    compute_opns=True,
    compute_svf=False
)

def pad_to_dem(array, dem):
    pad_r = dem.shape[0] - array.shape[-2]
    pad_c = dem.shape[1] - array.shape[-1]
    if pad_r == 0 and pad_c == 0:
        return array
    pad_width = [(0, 0)] * (array.ndim - 2) + [
        (pad_r // 2, pad_r - pad_r // 2),  
        (pad_c // 2, pad_c - pad_c // 2)    
    ]
    return np.pad(array, pad_width, mode="edge")

mhs_array = pad_to_dem(dict_mhs, data_arr)
opns_array = pad_to_dem(dict_opns['opns'], data_arr)
neg_opns_array = pad_to_dem(dict_neg_opns['opns'], data_arr)

dict_arrays = {
    'mhs_1': mhs_array,
    'opns_1': opns_array,
    'neg_opns_1': neg_opns_array,
    'profile': profile
}

for k, v in dict_arrays.items():
    print(k, type(v), getattr(v, 'shape', None))


def save_path_float(save_path):
    base, ext = os.path.splitext(str(save_path))
    return f'{base}_float{ext}'

def rasterio_save(arr, profile, save_path, nodata=None):
    profile=profile.copy()
    count = 1 if arr.ndim == 2 else arr.shape[0]
    profile.update(count=count, dtype=arr.dtype, nodata=nodata)
    with rio.open(save_path, 'w', **profile) as dst:
        if arr.ndim == 2:
            dst.write(arr, 1)
        else:
            dst.write(arr) 


def op(dict_arrays, save_path=None, save_float=False):
    opns = dict_arrays['opns_1'].squeeze()
    neg_opns = dict_arrays['neg_opns_1'].squeeze()

    comb_op = rvt.blend.BlenderCombination()

    comb_op.create_layer(
        vis_method='Positive Openness',
        normalization='Value',
        minimum=55,
        maximum=92,
        blend_mode='Overlay',
        opacity=90,
        image=opns
    )
    comb_op.create_layer(
        vis_method='Negative Openness',
        normalization='Value',
        minimum=55,
        maximum=60,
        blend_mode='Overlay',
        opacity=50,
        image=neg_opns
    )
    comb_op.create_layer(
        vis_method='Multidirectional Hillshade',
        normalization='Value',
        minimum=0,
        maximum=1,
        blend_mode='Normal',
        opacity=100,
        image=dict_arrays['mhs_1'].squeeze()
    )

    out_op = comb_op.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )

    out_profile = dict_arrays['profile'].copy()

    if save_float:
        rasterio_save(
            out_op,
            out_profile,
            save_path=save_path_float(save_path),
            nodata=np.nan
        )

    out_op_combined_8bit = rvt.vis.byte_scale(
        out_op,
        c_min=0,
        c_max=1
    ).astype('uint8')

    out_profile.update(dtype='uint8')
    rasterio_save(
        out_op_combined_8bit,
        out_profile,
        save_path=save_path,
        nodata=None
    )

    return out_op

op_big = op(dict_arrays, save_path=output_data, save_float=True)
