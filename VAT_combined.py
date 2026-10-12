'''
VAT COMBINED
'''


import rasterio as rio 
import rvt.blend
import rvt.vis
import rvt.default
import os 
import numpy as np 
from pathlib import Path 

input_data = Path(r"C:\Users\jakad\OneDrive\Desktop\3d_data\output\Pivola_klasificirano_in_rastirano_mediana.tiff")
output_data = Path(r"C:\Users\jakad\OneDrive\Desktop\3d_data\output\Pivola_VATcombined.tiff")

with rio.open(input_data) as src:
    print("CRS", src.crs)
    profile=src.profile.copy()

data_dict = rvt.default.get_raster_arr(input_data)
data_arr = data_dict['array']
data_resolution=data_dict['resolution']
data_x_resolution=data_resolution[0]
data_y_resolution=data_resolution[1]
data_no_data=data_dict['no_data']


dict_svf = rvt.vis.sky_view_factor(
    dem=data_arr,
    resolution=data_x_resolution,
    svf_n_dir=16,
    svf_r_max=10,
    svf_noise=0,
    no_data=data_no_data,
    compute_svf=True,
    compute_opns=True
)

svf_arr = dict_svf['svf']
opns_arr = dict_svf['opns']

dict_slope = rvt.vis.slope_aspect(
    dem=data_arr, 
    resolution_x = data_x_resolution,
    resolution_y= data_y_resolution,
    output_units='degree',
    ve_factor=1,
    no_data=data_no_data
)

slope_arr = dict_slope['slope']

hillshade_arr = rvt.vis.hillshade(
    dem=data_arr,
    resolution_x=data_x_resolution,
    resolution_y=data_y_resolution,
    sun_azimuth=315,
    sun_elevation=35,
    slope=None, 
    aspect=None,
    ve_factor=2.0,
    no_data=data_no_data
)

dict_arrays = {
    'svf_1': dict_svf['svf'],
    'slp_1': dict_slope['slope'],   
    'opns_1': dict_svf['opns'],
    'hs_1': hillshade_arr,
    'svf_2': dict_svf['svf'],
    'slp_2': dict_slope['slope'],   
    'opns_2': dict_svf['opns'],
    'hs_2': hillshade_arr,
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

#BlendBlender

#vat_flat
def vat_flat(dict_arrays, save_path=None, save_float=False):
    vat_combination_flat=rvt.blend.BlenderCombination()

    vat_combination_flat.create_layer(
        vis_method='Sky View Factor',
        normalization='Value',
        minimum=0.7,
        maximum=1.0,
        blend_mode='Multiply',
        opacity=25,
        image=dict_arrays['svf_2'].squeeze()
    )
    vat_combination_flat.create_layer(
        vis_method='Positive Openness',
        normalization='Value',
        minimum=68,
        maximum=93,
        blend_mode='Overlay',
        opacity=50,
        image=dict_arrays['opns_2'].squeeze()
    )
    vat_combination_flat.create_layer(
        vis_method='Slope gradient',
        normalization='Value',
        minimum=0,
        maximum=15,
        blend_mode='Luminosity',
        opacity=50,
        image=dict_arrays['slp_2'].squeeze()
    )
    vat_combination_flat.create_layer(
        vis_method='Hillshade',
        normalization='Value',
        minimum=0,
        maximum=1,
        blend_mode='Normal',
        opacity=100,
        image=dict_arrays['hs_2'].squeeze()        
    )

    out_vat_flat = vat_combination_flat.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )
    return out_vat_flat

#vat_general
def vat_general(dict_arrays, save_path=None, save_float=False):
    vat_combination_general=rvt.blend.BlenderCombination()
    vat_combination_general.create_layer(
        vis_method='Sky View Factor',
        normalization='Value',
        minimum=0.7,
        maximum=1.0,
        blend_mode='Multiply',
        opacity=25,
        image=dict_arrays['svf_1'].squeeze()
    )
    vat_combination_general.create_layer(
        vis_method='Positive Openness',
        normalization='Value',
        minimum=68,
        maximum=93,
        blend_mode='Overlay',
        opacity=50,
        image=dict_arrays['opns_1'].squeeze()
    )
    vat_combination_general.create_layer(
        vis_method='Slope gradient',
        normalization='Value',
        minimum=0,
        maximum=50,
        blend_mode='Luminosity',
        opacity=50,
        image=dict_arrays['slp_1'].squeeze()
    )
    vat_combination_general.create_layer(
        vis_method='Hillshade',
        normalization='Value',
        minimum=0,
        maximum=1,
        blend_mode='Normal',
        opacity=100,
        image=dict_arrays['hs_1'].squeeze()
    )

    out_vat_general = vat_combination_general.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )
    return out_vat_general

def combined_vat(dict_arrays, save_path=None, save_float=False):

    dict_arrays['vat_general'] = vat_general(dict_arrays)
    dict_arrays['vat_flat'] = vat_flat(dict_arrays)

    vat_combined_combination = rvt.blend.BlenderCombination()
    vat_combined_combination.create_layer(
    vis_method='VAT general',
    normalization='Value',
    minimum=0,
    maximum=1,
    blend_mode='Normal',
    opacity=50,
    image=dict_arrays['vat_general'].squeeze()
)
    vat_combined_combination.create_layer(
    vis_method='VAT flat',
    normalization='Value',
    minimum=0,
    maximum=1,
    blend_mode='Normal',
    opacity=100,
    image=dict_arrays['vat_flat'].squeeze()
)

    out_combined_vat = vat_combined_combination.render_all_images(
        save_visualizations=False, 
        save_render_path=None,
        no_data=np.nan
    )

    out_profile = dict_arrays['profile'].copy()

    if save_float:
        rasterio_save(
            out_combined_vat,
            out_profile,
            save_path=save_path_float(save_path),
            nodata=np.nan            
            )
    
    out_vat_combined_8bit = rvt.vis.byte_scale(
        out_combined_vat,
        c_min=0,
        c_max=1
        )
    
    out_profile.update(dtype='uint8')
    rasterio_save(
        out_vat_combined_8bit,
        out_profile,
        save_path=save_path,
        nodata=None
        )
        
    return combined_vat

    
vat_combined_big = combined_vat(dict_arrays, save_path=output_path, save_float=True)
