""" Module to read compiled data "Present Day Greenland's standard dataset"
"""
import os
import numpy as np

from dimarray.geo import read_nc

from .config import datadir

VERSION = 'v1.1'
#VERSION = 'dev1.2'

_NCFILE = os.path.join(datadir, "Present_Day_Greenland", 'Greenland_5km_{VERSION}.nc')
NCFILE = _NCFILE.format(VERSION=VERSION)

MAPPING = {'ellipsoid': u'WGS84',
         'false_easting': 0.0,
         'false_northing': 0.0,
         'grid_mapping_name': u'polar_stereographic',
         'latitude_of_projection_origin': 90.0,
         'standard_parallel': 71.0,
         'straight_vertical_longitude_from_pole': -39.0}

#def get_mapping(): return da.read_nc(NCFILE,'mapping')._metadata()

def load(*args, **kwargs):
    return read_nc(NCFILE, *args, **kwargs)


#def load(args=None, coord='geocentric', idx=None, region=None, datapath=datapath, metadata=False):
#    """ Load Greenland Standard (Developmental) Dataset
#
#    keyword argument: 
#    coord = None, "geocentric" [default], "geographic"
#    => if not None, coordinates are provided as the two first output variables,
#    either as x,y (geocentric) or as lon,lat (geographic)
#
#    Example:
#    >>> import presentdaygreenland as grl
#    >>> x, y, vx, vy = grl.load(['surfvelx','surfvely'])
#    >>> x, y, vx, vy = grl.load(['surfvelx','surfvely'])
#    >>> lon, lat, v  = grl.load('surfvelmag',coord='geographic')
#    >>> v  = grl.load('surfvelmag',coord=None)
#    >>> lon, lat, v  = grl.load('surfvelmag',region=[-40,75,-30,82], coord='geographic')
#    >>> x, y, v, metadata  = grl.load('surfvelmag', metadata=True)  # also return metadata
#    """
#    # Input arguments check
#    if args is None:
#       args = []
#    elif np.isscalar(args):
#       args = [args]
#    allowed_variables = variables()
#    for v in args:
#        if v not in allowed_variables:
#           raise Exception('error: variable {} not present, please provide one of {}'.format(v, variables()))
#
#    # Box to extract
#    if idx is not None: ind_i, ind_j = idx
#    else: ind_i = ind_j = None
#
#    if ind_i is None: ind_i = slice(None)
#    if ind_j is None: ind_j = slice(None)
#
#    nc = netCDF4.Dataset(datapath)
#
#    # Read coordinates
#    if coord == 'geocentric':
#       x = nc.variables['x1'][ind_j]
#       y = nc.variables['y1'][ind_i]
#       #x, y = np.meshgrid(x,y)
#       res = [x, y]
#       #res = [x[reg_ind],y[reg_ind]]
#
#    elif coord == 'geographic':
#       lon = nc.variables['lon'][:,ind_i, ind_j]
#       lat = nc.variables['lat'][:, ind_i, ind_j]
#       res = [lon,lat]
#    elif coord is None:
#       res = []
#    else:
#       raise Exception('bad value for coord:'+coord)
#
#    # Append explicitly required variables
#    for v in args:
#       res.append(nc.variables[v][:, ind_i, ind_j])
#
#    # make sure data are squeezed
#    for i,v in enumerate(res):
#       vv = res[i]
#       if np.ndim(vv) == 3:
#           res[i] = np.squeeze(vv)
#
#    # add metadata if required
#    if metadata:
#       for v in args:
#           ncvar = nc.variables[v]
#           meta = {att:ncvar.getncattr(att) for att in ncvar.ncattrs}
#           res.append(meta)
#
#    nc.close()
#
#    return res
#
#def region_index(region, coord='geocentric', loadf=load):
#    """ extract index for a particular region
#
#    region: [llx, lly, urx, ury] 
#    coord : geocentric (x, y) or geographic (lon, lat)
#
#    """
#    # load coordinates (x,y or lon,lat)
#    x,y = loadf(coord=coord)
#
#    # make a mask
#    if np.ndim(x) == 1:
#       x, y = np.meshgrid(x, y) # make sure x,y is 2D
#    llx, lly, urx, ury = region
#    mask = (x >= llx) & (x <= urx) & (y>= lly) & (y <= ury) # mask
#
#    #import cresis
#    #import matplotlib.pyplot as plt
#    #xx, yy = cresis.cresis_to_standard(x[mask], y[mask], reverse=True)
#    #plt.scatter(xx, yy,marker='.',color='r')
#    #plt.show()
#
#    # find index ranges 
#    if coord == 'geographic': x,y = loadf(coord='geocentric')
#    ymin,ymax = np.min(y[mask]), np.max(y[mask])
#    xmin,xmax= np.min(x[mask]), np.max(x[mask])
#    j1 = int(np.where(x[0,:]==xmin)[0])
#    j2 = int(np.where(x[0,:]==xmax)[0])
#    i1 = int(np.where(y[:,0]==ymin)[0])
#    i2 = int(np.where(y[:,0]==ymax)[0])
#
#    # return as array slices
#    ind_i_s = slice(i1, i2+1) 
#    ind_j_s = slice(j1, j2+1)
#
#    #import cresis
#    #import matplotlib.pyplot as plt
#    #xx, yy = cresis.cresis_to_standard(x[ind_i_s,ind_j_s], y[ind_i_s,ind_j_s], reverse=True)
#    #plt.scatter(xx, yy,marker='.',color='r')
#    #plt.show()
#    #plt.draw()
#    #1/0
#
#    return ind_i_s, ind_j_s 
