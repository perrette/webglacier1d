import os
import numpy as np
import netCDF4 
from dimarray.geo import read_nc

from .config import datadir

#ncfile = datadir+'bamber_2013_1km/Greenland_bedrock_topography_V2.nc'
NCFILE = os.path.join(datadir, 'bamber_2013_1km','Greenland_bedrock_topography_V3.nc')

MAPPING = {'ellipsoid': u'WGS84',
         'false_easting': 0.0,
         'false_northing': 0.0,
         'grid_mapping_name': u'polar_stereographic',
         'latitude_of_projection_origin': 90.0,
         'standard_parallel': 71.0,
         'straight_vertical_longitude_from_pole': -39.0}

# da.read_nc(NCFILE,'Polar-Stereographic')._metadata()

def load(*args, **kwargs):
    res = read_nc(NCFILE, *args, **kwargs)
    # x = read_nc(NCFILE, 'projection_x_coordinate')
    # y = read_nc(NCFILE, 'projection_y_coordinate')
    # res.axes['x'][:] = x
    # res.axes['y'][:] = y
    return res
