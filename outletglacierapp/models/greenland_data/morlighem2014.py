""" Bedrock elevation
"""
import os

from dimarray.geo import read_nc

from .config import datadir

# NCFILE = os.path.join(datadir, "MCdataset-2014-10-16.nc")
NCFILE = os.path.join(datadir, "MCdataset-2014-10-16-y-inverted.nc")

MAPPING = {'ellipsoid': u'WGS84',
         'false_easting': 0.0,
         'false_northing': 0.0,
         'grid_mapping_name': u'polar_stereographic',
         'latitude_of_projection_origin': 90.0,
         'standard_parallel': 70.0,
         'straight_vertical_longitude_from_pole': -45.0}

def load(*args, **kwargs):
    return read_nc(NCFILE, *args, **kwargs)
