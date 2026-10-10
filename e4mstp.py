"""
e4MSTP vizualizacija iz DEM-a (RVT_py)

Verzija RVT: 2.2.1 (pip show rvt-py)
Vir priporočil za vizualizacijo: Kokalj (2025), Standardizing Visualization in
Ancient Maya Lidar Research: Techniques, Challenges and Recommendations.
Avtor: Jaka Dacar 2026
"""

import rvt.default
import rvt.vis
import rvt.blend
import rasterio
import numpy as np
import os

# --- Vhodni in izhodni podatki ---------------------------------------------
# Vhodni DEM
data_path = r".tiff"
# Izhodna vizualizacija (8-bitna; float različica dobi pripono _float)
output_path=r".tiff"

# --- Preverjanje vhodne datoteke -------------------------------------------
# Izpis koordinatnega sistema in nodata vrednosti; profil se uporabi pri shranjevanju.
with rasterio.open(data_path) as src:
    print("CRS:", src.crs)
    print("No data value:", src.nodata)
    profile=src.profile.copy()

# --- Branje DEM-a z RVT ----------------------------------------------------
data_dict = rvt.default.get_raster_arr(data_path)
data_arr = data_dict['array']
data_resolution = data_dict['resolution']
data_x_resolution = data_resolution[0]
data_y_resolution = data_resolution[1]
data_no_data = data_dict['no_data']

# Radija SVF: 5 m ("general") in 10 m ("flat"), preračunana v piksle.
r_small = round(5 / data_x_resolution)
r_large = round(10 / data_x_resolution)

# --- Izračun osnovnih vizualizacij -----------------------------------------
# Opomba: v rvt.vis so radiji in merila podani v pikslih, ne v metrih.

# MSTP: lokalno, mezo in široko merilo, parameter lightness.
dict_mstp = rvt.vis.mstp(
    dem=data_arr, 
    local_scale=(1, 5, 1),
    meso_scale=(5, 50, 5),
    broad_scale=(50, 200, 50), #<--- 50,500,50 iz članka in githuba
    lightness=1.2,
    ve_factor=1,
    no_data=data_no_data
)

# SVF in pozitivna odprtost, majhen radij (5 m).
dict_svf_1 = rvt.vis.sky_view_factor(
    dem=data_arr,
    resolution=data_x_resolution,
    svf_n_dir=16,
    svf_r_max=r_small,
    svf_noise=0,
    no_data=data_no_data,
    compute_svf=True,
    compute_opns=True
    )

# SVF, velik radij (10 m); odprtost ni potrebna.
dict_svf_2 = rvt.vis.sky_view_factor(
    dem=data_arr,
    resolution=data_x_resolution,
    svf_n_dir=16,
    svf_r_max=r_large,
    svf_noise=0,
    no_data=data_no_data,
    compute_svf=True,
    compute_opns=False
    )

# Obrnjen DEM za negativno odprtost; nodata piksle ohranimo.
neg_arr = -data_arr
if data_no_data is not None and not np.isnan(data_no_data):
    neg_arr[data_arr == data_no_data] = data_no_data

# Negativna odprtost: pozitivna odprtost na obrnjenem DEM-u
# (compute_svf=False, da se izračuna samo odprtost).
dict_neg_opns = rvt.vis.sky_view_factor(
    dem=neg_arr, 
    resolution=data_x_resolution,
    svf_n_dir=16,
    svf_r_max=r_small,
    svf_noise=0,
    ve_factor=1,
    no_data=data_no_data,
    compute_opns=True,
    compute_svf=False
    )

# Lokalna dominanca (radija 10 do 20 pikslov, višina opazovalca 1,7 m).
local_dom_arr = rvt.vis.local_dominance(
    dem=data_arr,
    min_rad=10,
    max_rad=20,
    rad_inc=1,
    angular_res=15,
    observer_height=1.7,
    ve_factor=1,
    no_data=data_no_data
)

# Naklon v stopinjah. Pri radianih je treba prilagoditi normalizacijo v sloju naklona.
dict_slope_aspect = rvt.vis.slope_aspect(
    dem=data_arr,
    resolution_x=data_x_resolution,
    resolution_y=data_y_resolution,
    output_units="degree",
    ve_factor=1,
    no_data=data_no_data
)


# Izvlečeni nizi (v nadaljevanju se ne uporabljajo, ostajajo za pregled).
svf_arr = dict_svf_1['svf']
opns_arr = dict_svf_1['opns']
neg_opns_arr = dict_neg_opns['opns']
slope_arr = dict_slope_aspect['slope']

# Zbirni slovar vhodov za mešanje.
dict_arrays = {
    'mstp_1': dict_mstp,
    'svf_1': dict_svf_1['svf'],     
    'svf_2': dict_svf_2['svf'],
    'local_dom_1': local_dom_arr, # lokalna dominanca
    'opns_1': dict_svf_1['opns'], # pozitivna odprtost
    'neg_opns_1': dict_neg_opns['opns'], # negativna odprtost
    'slope_1': dict_slope_aspect['slope'],          
    'profile': profile 
}

# --- Pomožne funkcije za shranjevanje --------------------------------------
# Pot za float različico: doda pripono _float imenu datoteke.
def save_path_float(save_path):
    base, ext = os.path.splitext(str(save_path))
    return f'{base}_float{ext}'

# Shrani 2D ali večkanalni niz kot GeoTIFF z danim profilom.
def rasterio_save(arr, profile, save_path, nodata=None):
    profile=profile.copy()
    count = 1 if arr.ndim == 2 else arr.shape[0]
    profile.update(count=count, dtype=arr.dtype, nodata=nodata)
    with rasterio.open(save_path, 'w', **profile) as dst:
        if arr.ndim == 2:
            dst.write(arr, 1)
        else:
            dst.write(arr) 

# --- Vmesni mešanici -------------------------------------------------------
# Kombiniran SVF: svf_1 (norm. 0,7 do 1, 50 %) pod svf_2 (norm. 0,9 do 1, 100 %).
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

# Kombinacija razlike odprtosti (pozitivna minus negativna) in lokalne dominance.
def blend_opns_ld(dict_arrays, save_path=None):
    comb_opns_ld=rvt.blend.BlenderCombination()
    comb_opns_ld.create_layer(
        vis_method='Openness positive',
        normalization='Value',
        minimum=-15,
        maximum=15,
        blend_mode='Normal',
        opacity=50, 
        image=dict_arrays['opns_1'].squeeze() - dict_arrays['neg_opns_1'].squeeze()
    )

    comb_opns_ld.create_layer(
        vis_method='Local Dominance',
        normalization='Value',
        minimum=0.5,
        maximum=1.8,
        blend_mode='Normal',
        opacity=100, 
        image=dict_arrays['local_dom_1'].squeeze()
    )

    out_opns_ld = comb_opns_ld.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )

    return out_opns_ld 

# --- Končna mešanica e4MSTP ------------------------------------------------
def e4mstp(dict_arrays, save_path=None, save_float=False):
    """
    Zloži e4MSTP iz štirih slojev (od spodaj navzgor):
      1. MSTP                      overlay,  90 %
      2. kombiniran SVF            multiply, 25 %
      3. odprtost + lok. dominanca multiply, 100 %
      4. naklon (0 do 55 stopinj, barvna lestvica 'cool')  normal, 100 %
    Rezultat omeji na največ 1, nodata piksle ohrani kot NaN in ga shrani
    kot 8-bitni GeoTIFF (ter kot float, če je save_float=True).
    """

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
        image=dict_arrays['mstp_1'].squeeze()
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
        # Barvna lestvica 'cool' (matplotlib) preide med dvema izrazitima barvama in tako
        # loči naklone. Odstopa od originalne e4MSTP, ki uporablja 'Reds_r'.
        # Lestvice: https://matplotlib.org/3.3.2/tutorials/colors/colormaps.html
        colormap='cool',
        min_colormap_cut=0,
        max_colormap_cut=1,
        image=dict_arrays['slope_1'].squeeze()
    )

    out_e4mstp = e4mstp_combination_general.render_all_images(
        save_visualizations=False,
        save_render_path=None,
        no_data=np.nan
    )

    # Maska nodata območij in omejitev vrednosti na največ 1.
    out_e4mstp = out_e4mstp.astype('float32')
    out_e4mstp[np.isnan(dict_arrays['mstp_1'])] = np.nan
    out_e4mstp[out_e4mstp > 1] = 1

    
    out_profile = dict_arrays['profile'].copy()

    # Shranjevanje: najprej float različica (po želji), nato 8-bitna.
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
