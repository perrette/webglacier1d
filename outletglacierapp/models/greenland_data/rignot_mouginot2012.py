""" Load velocity dataset from Rignot and Mouginot (2012)
"""

import os
from collections import OrderedDict as odict
import numpy as np
import netCDF4 as nc
import dimarray.geo as da

try:
    from .config import datadir
except ImportError:
    datadir = ''

NCFILE = os.path.join(datadir, "Rignot_Mouginot_2012_IceFlowGreenlandPolarYear20082009","velocity_greenland_15Feb2013.nc")

MAPPING = {'ellipsoid': u'WGS84',
         'false_easting': 0.0,
         'false_northing': 0.0,
         'grid_mapping_name': u'polar_stereographic',
         'latitude_of_projection_origin': 90.0,
         'standard_parallel': 70.0,
         'straight_vertical_longitude_from_pole': -45.0}

def load(bbox=None, maxshape=None):
    """ load data for a region
    
    parameters:
    -----------
    bbox: llx, lly, urx, ury: projection coordinates of lower left and upper right corners
    maxshape: tuple, optional
        maximum shape of the data to be loaded


    return: 
    -------
    x, y, vx, vy

    NOTE: projection coordinates: lon0=-45, lat0=90, sec_lat=70
    """
    f = nc.Dataset(NCFILE)

    # reconstruct coordinates
    xmin, ymax = -638000.0, -657600.0
    spacing = 150.0
    nx, ny = 10018, 17946
    x = np.linspace (xmin, xmin + spacing*(nx-1), nx)  # ~ 10000 * 170000 points, 
    y = np.linspace (ymax, ymax - spacing*(ny-1), ny)  # reversed data

    if bbox is not None: 
        llx, lly, urx, ury = bbox
        #llx, urx, lly, ury = bbox
        j = np.where((x >= llx) & (x <= urx))[0]
        i = np.where((y >= lly) & (y <= ury))[0][::-1] # needs to be inverted
        nx, ny = len(j), len(i)
    else:
        j = np.arange(nx)
        i = np.arange(ny)[::-1]

    # sub-sampling?
    if maxshape is not None:
        if len(maxshape) == 1: 
            maxshape = (maxshape, maxshape)  
        maxi, maxj = maxshape
        si = np.floor_divide(ny, maxi)
        sj = np.floor_divide(nx, maxj)
        si = max([1, si])
        sj = max([1, sj])
        if si != 1 or sj != 1:
            print 'a priori subsampling (velocity): ',si,sj
            j = j[::sj]
            i = i[::si]
    
    i = sorted(i.tolist())
    j = sorted(j.tolist())

    vx = f.variables['vx'][i, j][::-1,:]
    vy = f.variables['vy'][i, j][::-1,:]
    x = x[j]
    y = y[i][::-1]

    # convert all to a dataset
    ds = da.Dataset()
    ds['vx'] = da.GeoArray(vx, axes=[y,x], dims=['y','x'], grid_mapping='mapping')
    ds['vy'] = da.GeoArray(vy, axes=[y,x], dims=['y','x'], grid_mapping='mapping')
    mapping = da.GeoArray('')
    mapping._metadata(MAPPING) # add mapping info
    ds['mapping'] = mapping

    # also set metadata
    for att in f.variables['vx'].ncattrs():
        setattr(ds['vx'], att.lower(), f.variables['vx'].getncattr(att))
    for att in f.variables['vy'].ncattrs():
        setattr(ds['vy'], att.lower(), f.variables['vy'].getncattr(att))
    for att in f.ncattrs():
        setattr(ds, att.lower(), f.getncattr(att))

    f.close()

    return ds
