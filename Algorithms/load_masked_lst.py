# -*- coding: utf-8 -*-
"""
Created on Thu Mar 15 10:35:49 2018

@author: Chad

A script for loading clean/masked Frcational Cover

"""
import datacube
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
from datacube.storage.masking import mask_to_dict
from datacube.storage.masking import make_mask

dc = datacube.Datacube(app='fc_fun')

def load_masked_lst(sensor, query, cloud_free_threshold, bands_of_int=['red','green','blue','nir','swir1']):   
    #print('loading {}'.format(sensor)
    
    basic_pq_mask = {'cloud_acca':'no_cloud',
    'cloud_shadow_acca' :'no_cloud_shadow',
    'cloud_shadow_fmask' : 'no_cloud_shadow',
    'cloud_fmask' :'no_cloud',
    'blue_saturated' : False,
    'green_saturated' : False,
    'red_saturated' : False,
    'nir_saturated' : False,
    'swir1_saturated' : False,
    'swir2_saturated' : False,
    'contiguous':True,
    'land_sea': 'land'}

    # load surface reflectance and PQ
    data = dc.load(product=(sensor + '_nbart_albers'), measurements=bands_of_int, group_by='solar_day', **query)
    pq = dc.load(product=(sensor + '_pq_albers'), group_by='solar_day', **query, fuse_func=ga_pq_fuser)

    crs = data.crs
    crswkt = data.crs.wkt
    affine = data.affine

    # find common observations
    time = (data.time - data.time).time  # works!
    data = data.sel(time=time)
    pq = pq.sel(time=time)

    # mask
    basic_mask = make_mask(pq, **basic_pq_mask).pixelquality
    data = data.where(basic_mask)    
    cloud_free = make_mask(pq, cloud_acca='no_cloud', cloud_fmask='no_cloud').pixelquality

    #filter with cloud free threshold to remove cloudy scenes
    mostly_cloud_free = cloud_free.mean(dim=('x', 'y')) >= cloud_free_threshold

    # only those observations that were mostly cloud free
    result = data.where(mostly_cloud_free).dropna(dim='time', how='all')
    result.attrs['crs'] = crs
    result.attrs['affine'] = affine
    return result
        
    print ('complete')
