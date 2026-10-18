'''
Simple Red Relief
'''

import rasterio as rio 
import rvt.blend
import rvt.vis
import rvt.default
import os 
import numpy as np 
from pathlib import Path 
import matplotlib.colors as matcolor


input_data = Path(r".tif")
output_data = Path(r".tif")

with rio.open(input_data) as src:
    print("CRS", src.crs)
    profile=src.profile.copy()

data_dict = rvt.default.get_raster_arr(input_data)
data_arr = data_dict['array']
data_resolution=data_dict['resolution']
data_x_resolution=data_resolution[0]
data_y_resolution=data_resolution[1]
data_no_data=data_dict['no_data']

slope_dict = rvt.vis.slope_aspect(
    dem=data_arr,
    resolution_x=data_x_resolution,
    resolution_y=data_y_resolution,
    output_units='degree',
    ve_factor=1,
    no_data=data_no_data
)

slope_arr = slope_dict['slope']

slrm_arr = rvt.vis.slrm(
    dem=data_arr,
    radius_cell=20,
    ve_factor=1,
    no_data=data_no_data
)

dict_arrays = {
    'slrm_1': slrm_arr,
    'slope_1': slope_arr,
    'profile': profile
}

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

def cumulative_count_cut(band, min_percentile=2.0, max_percentile=98.0):
    min_val=np.nanpercentile(band, min_percentile)
    max_val=np.nanpercentile(band, max_percentile)
    return min_val, max_val

def srr(dict_arrays, save_path=None, save_float=False):
    srr_combination = rvt.blend.BlenderCombination()

    colors_slrm = [
        (0.0, (0.0, 0.0, 0.0, 0.0)),   # Low Stop: -7.79 #009EA2  --> svetla modra
        (0.50, "#8A8A8A"),  # Middle Stop: -1 
        (1.0, "#FEFFAC")    # High Stop: 8.42 
    ]
    cmap_slrm = matcolor.LinearSegmentedColormap.from_list('slrm_custom', [(val, col) for val, col in colors_slrm])

    colors_slope = [
        (0.0, "#FFFFFF"),   # Low Stop
        (1.0, '#B62700')    # High Stop
    ]
    cmap_slope = matcolor.LinearSegmentedColormap.from_list('white_to_red', [(val, col) for val, col in colors_slope])

    srr_combination.create_layer(
        vis_method='Slope',
        normalization='Value',
        minimum=0,
        maximum=55,
        blend_mode='Multiply',
        opacity=50,  
        colormap=cmap_slope,
        image=dict_arrays['slope_1'].squeeze()
    )


    srr_combination.create_layer(
        vis_method='Simple Local Relief Model',
        normalization='Value',
        minimum=-8,
        maximum=7,
        blend_mode='Normal',
        opacity=100,
        colormap=cmap_slrm,
        image=dict_arrays['slrm_1'].squeeze()
    )


    out_srr_combination = srr_combination.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )

    out_profile = dict_arrays['profile'].copy()

    if save_float:
        rasterio_save(
            out_srr_combination,
            out_profile,
            save_path=save_path_float(save_path),
            nodata=np.nan
        )

    lo, hi = cumulative_count_cut(out_srr_combination, 2.0, 98.0)
    out_srr_combination_8bit = rvt.vis.byte_scale(
            out_srr_combination,
            c_min=lo,
            c_max=hi
        )

    out_profile.update(dtype='uint8')
    rasterio_save(
        out_srr_combination_8bit,
        out_profile,
        save_path=save_path,
        nodata=None
    )

    return srr_combination


srr_ou = srr(dict_arrays, save_path=output_data, save_float=True)
