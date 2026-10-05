import rvt.default
import rvt.vis
import rvt.blend
import rasterio as rio
import numpy as np

data_path = r"C:\Users\jakad\OneDrive\Desktop\3d_data\output\Pivola_klasificirano_in_rastirano_mediana.tiff"
output_path=r"C:\Users\jakad\OneDrive\Desktop\3d_data\output\Pivola_klasificirano_in_rastirano_mediana201.tiff"

with rio.open(data_path) as src:
    print("CRS:", src.crs)
    print("No data value:", src.nodata)

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

combination_manual = rvt.blend.BlenderCombination()

combination_manual.create_layer(
    vis_method='Sky View Factor', 
    normalization='value',
    minimum=0.65,
    maximum=1.00,
    blend_mode='multiply',
    opacity=25,
    image=svf_arr
)

combination_manual.create_layer(
    vis_method='Positive Openness',
    normalization='value',
    minimum=80,
    maximum=91,
    blend_mode='overlay',
    opacity=50,
    image=opns_arr
)

combination_manual.create_layer(
    vis_method='Slope',
    normalization='value',
    minimum=0,
    maximum=1.57,
    blend_mode='luminosity',
    opacity=50,
    image=slope_arr
)
combination_manual.create_layer(
    vis_method='Hillshade',
    normalization='value',
    minimum=0,
    maximum=1,
    blend_mode='normal',
    opacity=100,
    image=hillshade_arr
)

combination_manual.add_dem_path(dem_path=data_path)
render_arr = combination_manual.render_all_images(save_render_path=output_path)


