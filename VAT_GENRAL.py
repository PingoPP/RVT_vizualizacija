import rvt.default
import rvt.vis
import rvt.blend
import rasterio 
import numpy as np

data_path = r".tiff"
output_path=r".tiff"

with rasterio.open(data_path) as src:
    print("CRS:", src.crs)
    print("No data value:", src.nodata)
    profile=src.profile.copy()

data_dict = rvt.default.get_raster_arr(data_path)
data_arr = data_dict['array']
data_resolution = data_dict['resolution']
data_x_resolution = data_resolution[0]
data_y_resolution = data_resolution[1]
data_no_data = data_dict['no_data']


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


dict_slope_aspect = rvt.vis.slope_aspect(
    dem=data_arr,
    resolution_x=data_x_resolution,
    resolution_y=data_y_resolution,
    output_units="radian",
    ve_factor=2,
    no_data=data_no_data
)

slope_arr = dict_slope_aspect['slope']

hillshade_arr = rvt.vis.hillshade(
    dem=data_arr,
    resolution_x=data_x_resolution,
    resolution_y=data_y_resolution,
    sun_azimuth=315,
    sun_elevation=35,
    slope=None,
    aspect=None,
    ve_factor=6.0,
    no_data=data_no_data
)

dict_arrays = {
    'svf_1': dict_svf['svf'],
    'opns_1': dict_svf['opns'],
    'slp_1': dict_slope_aspect['slope'],
    'hs_1': hillshade_arr,
    'profile': profile
}

def save_path_float(save_path):
    return str(save_path).replace('.tiff', '_float.tiff').replace('.tif', 'float.fit')

def rasterio_save(arr, profile, save_path, nodata=None):
    profile=profile.copy()
    count = 1 if arr.ndim == 2 else arr.shape[0]
    profile.update(count=count, dtype=arr.dtype, nodata=nodata)
    with rasterio.open(save_path, 'w', **profile) as dst:
        if arr.ndim == 2:
            dst.write(arr, 1)
        else:
            dst.writer(arr) 

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
    vat_1 = vat_combination_general.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )
    out_vat_general = vat_1.astype('float32')

    out_profile = dict_arrays['profile'].copy()
    if save_float:
        rasterio_save(
            out_vat_general,
            out_profile,
            save_path=save_path_float(save_path),
            nodata=np.nan
        )
    if save_path:
        out_vat_general_8bit=rvt.vis.byte_scale(
            out_vat_general,
            c_min=0,
            c_max=1
        )
        out_profile.update(dtype='unit8')
        rasterio_save(
            out_vat_general_8bit,
            out_profile,
            save_path=save_path,
            nodata=None
        )

    return out_vat_general

vat = vat_general(dict_arrays, save_path=output_path, save_float=True)
