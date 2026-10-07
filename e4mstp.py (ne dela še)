import rvt.default
import rvt.vis
import rvt.blend
import rasterio 
import numpy as np
import os 

data_path = r"C:\Users\jakad\OneDrive\Desktop\3d_data\output\Pivola_klasificirano_in_rastirano_mediana.tiff"
output_path=r"C:\Users\jakad\OneDrive\Desktop\3d_data\output\Pivola_klasificirano_in_rastirano_mediana_e4mstp.tiff"

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

dict_mstp = rvt.vis.mstp(
    dem=data_arr, 
    local_scale=(1, 5, 1),
    meso_scale=(5, 50, 5),
    broad_scale=(50, 500, 50),
    lightness=1.2,
    ve_factor=1,
    no_data=data_no_data
)

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

#dict_on = rvt.vis.sky_view_factor(
#    dem=data_arr, 
#    resolution=data_x_resolution,
#    svf_n_dir=16,
#    svf_r_max=10,
#    svf_noise=0,
#    no_data=data_no_data
#)

dict_ld = rvt.vis.local_dominance(
    dem=data_arr,
    min_rad=10,
    max_rad=20,
    rad_inc=1,
    angular_res=15,
    observer_height=1.7,
    ve_factor=1,
    no_data=data_no_data
)

svf_arr = dict_svf['svf']
opns_arr = dict_svf['opns']
neg_opns_arr = dict_svf['neg_opns']
local_dom_arr = dict_svf['local_dom']


dict_slope_aspect = rvt.vis.slope_aspect(
    dem=data_arr,
    resolution_x=data_x_resolution,
    resolution_y=data_y_resolution,
    output_units="radian",
    ve_factor=1,
    no_data=data_no_data
)

slope_arr = dict_slope_aspect['slope']

dict_arrays = {
    'mstp': dict_mstp['mstp'],
    'svf_1': dict_svf['svf'],     
    'svf_2': dict_svf['svf'],
    'local_dom': dict_ld['local_dom'], #local dominance
    'opns': dict_svf['opns'], #positive openness
    'neg_opns': dict_svf['neg_opns'], #negative openness
    'slope': dict_slope_aspect['slope'],          
    'profile': profile 
}

def save_path_float(save_path):
    base, ext = os.path.splitext(str(save_path))
    return f'{base}_float{ext}'

def rasterio_save(arr, profile, save_path, nodata=None):
    profile=profile.copy()
    count = 1 if arr.ndim == 2 else arr.shape[0]
    profile.update(count=count, dtype=arr.dtype, nodata=nodata)
    with rasterio.open(save_path, 'w', **profile) as dst:
        if arr.ndim == 2:
            dst.write(arr, 1)
        else:
            dst.write(arr) 

def blend_svf_combined(dict_arrays, save_path=None):
    comb_svf=rvt.blend.BlenderCombination()
    comb_svf.create_layer(
        vis_method='Sky View Factor',
        normalization='Value',
        minimum=0.7,
        maximum=1.0,
        blend_mode='Normal',
        opacity=50,
        image=dict_arrays['svf_1'].squeeze()
    )

    comb_svf.create_layer(
        vis_method='Sky View Factor',
        normalization='Value',
        minimum=0.9,
        maximum=1.0,
        blend_mode='Normal',
        opacity=100,
        image=dict_arrays['svf_2'].squeeze()
    )

    out_comb_svf = comb_svf.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )

    return out_comb_svf

def blend_opns_ld(dict_arrays, save_path=None):
    comb_opns_ld=rvt.blend.BlenderCombination()
    comb_opns_ld.create_layer(
        vis_method='Openness positive',
        normalization='Value',
        minimum=15,
        maximum=15,
        blend_mode='Normal',
        opacity=50, 
        image=(dict_arrays['opns'] - dict_arrays['neg_opns'].squeeze)
    )

    comb_opns_ld.create_layer(
        vis_method='Local Dominace',
        normalization='Value',
        minimum=0.5,
        maximum=1.8,
        blend_mode='Normal',
        opacity=100, 
        image=(dict_arrays['local_dom'].squeeze)
    )

    out_opns_ld = comb_opns_ld.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )

    return out_opns_ld 


def e4mstp(dict_arrays, save_path=None, save_float=False):

    dict_arrays['svf_combined'] = blend_svf_combined(dict_arrays)
    dict_arrays['blend_opns_ld'] = blend_opns_ld(dict_arrays)

    e4mstp_combination_general=rvt.blend.BlenderCombination()
    e4mstp_combination_general.create_layer(
        vis_method='mstp',
        normalization='Value',
        minimum=0.0,
        maximum=1.0,
        blend_mode='Overlay',
        opacity=90,
        image=dict_arrays['mstp'].squeeze()
    )
    e4mstp_combination_general.create_layer(
        vis_method='Combo SVF',
        normalization='Value',
        minimum=-0.5,
        maximum=0.5,
        blend_mode='Multiply',
        opacity=25,
        image=dict_arrays['svf_combined'].squeeze()
    )
    e4mstp_combination_general.create_layer(
        vis_method='Combo opns ld',
        normalization='Value',
        minimum=0,
        maximum=1,
        blend_mode='Multiply',
        opacity=100,
        image=dict_arrays['blend_opns_ld'].squeeze()
    )
    e4mstp_combination_general.create_layer(
        vis_method='Slope',
        normalization='Value',
        minimum=0,
        maximum=55,
        blend_mode='Normal',
        opacity=100,
        colormap='Reds_r',
        min_colormap_cut=0,
        max_colormap_cut=1,
        image=dict_arrays['slope'].squeeze()
    )

    out_e4mstp = e4mstp_combination_general.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )

    out_profile = dict_arrays['profile'].copy()
    
    if save_float:
        rasterio_save(
            out_e4mstp,
            out_profile,
            save_path=save_path_float(save_path),
            nodata=np.nan            
            )
    
    out_vat_combined_8bit = rvt.vis.byte_scale(
        out_e4mstp,
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
        
    return out_e4mstp

    
e4mstp_big = e4mstp(dict_arrays, save_path=output_path, save_float=True)
