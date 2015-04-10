""" This app allows vizualizing various Greenland dataset
with a selection of : 
    - variables to vizualize
        bedrock, surface elevation, thickness, velocity, SMB...
    - regions to investigate
        Box and Decker (2011) pre-defined glaciers
"""
import sys
import hashlib
import time

import numpy as np
import dimarray.geo as da
from dimarray.geo.crs import get_crs

# load greenland data
from greenland_data.elevation import load as load_elevation
from greenland_data.velocity import load as load_velocity
from greenland_data.outlet_glacier_region import get_region
from greenland_data import standard_dataset
from greenland_data.standard_dataset import MAPPING # coordinate system
# from greenland_data.rignot_mouginot2012 import MAPPING # coordinate system


CRS = get_crs(MAPPING) # coordinate system 

# glacier regions
from greenland_data import boxdecker2011 as bd

def get_coords(nm):
    """ get coordinates of a glacier as left, right, bottom, top in km
    """
    reg = get_region(nm)
    l,b,r,t = [round(c*1e-3) for c in reg]
    return l,r,b,t

def _load_data(coords, variable, dataset=None, maxshape=None):
    """ load data to be plotted, for a particular glacier 
    and a particular region

    Parameter
    ---------
    coords : coordinate box in km (left, right, bottom, up)
        in the coordinate system from STANDARD_DATASET
    variable : variable to load
    dataset : data source, optional 
    maxshape : maximum shape of laoded data (sub-sampling when loading to save time)
    
    Returns
    -------
    DimArray instance
    """
    # convert to llx, lly, urx, ury in m
    l, r, b, u = np.array(coords)*1e3
    bbox = l,b,r,u

    # All data from standard greenland dataset
    if dataset == 'standard_dataset':
        data = standard_dataset.load(variable).squeeze()
        data.dims = ('y','x')
        data = data[(data.y >= b) & (data.y<=u)][:,(data.x >= l) & (data.x<=r)]

    # Bedrock topography
    elif variable in ('bedrock', 'surface', 'thickness'):
        ds = load_elevation(bbox, variable=variable, dataset=dataset, crs=CRS, maxshape=maxshape) #, variable=variable)
        data = ds[variable]

    # Velocity
    elif variable in ('velocity_x', 'velocity_y','velocity_mag','velocity_angle'):
        velocity = load_velocity(bbox, dataset=dataset, crs=CRS, maxshape=maxshape)   # dataset='...'
        vx = velocity['vx']
        vy = velocity['vy']
        if variable == 'velocity_x': 
            data = vx
        elif variable == 'velocity_y': 
            data = vy
        elif variable == "velocity_mag":
            data = (vx**2 + vy**2)**0.5
            data.units = vx.units
            data.long_name = "velocity magnitude"
        elif variable == 'velocity_angle':
            data = np.arctan(vy/vx)*180/np.pi
            data.units = "degrees"
            data.long_name = "angle of the velocity vector from the horizontal (arctan(vy/vx)"
        else:
            raise NotImplementedError(variable + ' is not available')

    else:
        raise NotImplementedError(variable + ' is not available')

    return data

def get_dict_data(variable, dataset, coords, zoom=300e3, maxshape=(200,200)):
    """ read data and return it as json format for the javascript plotting
    """
    # Update coordinates based on glacier and coords
    #coords = get_region(glacier, zoom)
    #session['coords'] = [float(c) for c in coords]

    # load data
    dim_a = _load_data(coords, variable, dataset, maxshape=maxshape)

    if True:
        # subsample data to ease plotting?
        ni, nj = dim_a.shape
        #maxi, maxj = 200, 200 # quite high res, but not too high
        maxi, maxj = maxshape
        si = np.floor_divide(ni, maxi)
        sj = np.floor_divide(nj, maxi)
        si = max([1, si])
        sj = max([1, sj])
        if si != 1 or sj != 1:
            print 'a posteriori subsampling: ',si,sj
            #print "subsampling:",si, sj
            dim_a = dim_a.ix[::si, ::sj]

    # extends x-axis to get appropriate aspect ratio (useful for velocity, which involves 
    # projections)

    if variable == 'velocity_mag':
        units = dim_a.units.strip()
        # dim_a = np.log(np.clip(dim_a, 1e-2, np.inf)) # remove zero numbers
        # dim_a.units = "ln("+units+")"
        dim_a = np.log10(np.clip(dim_a, 1e-2, np.inf)) # remove zero numbers
        dim_a.units = "log10("+units+")"

    # prepare dictionary to update data source
    x = dim_a.axes[1].values*1e-3  # express in m
    y = dim_a.axes[0].values*1e-3
    z = dim_a.values

    assert not np.isnan(x).any()
    assert not np.isnan(y).any()

    # make sure everything is a regular float and not some
    # numpy type not understood by json
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)

    # replace missing values with a flag
    missing = -99.99 # missing data
    if np.isnan(z).any():
        z[np.isnan(z)] = missing

    # round data to save space
    z = np.round(z, 2)
    x = np.round(x, 0)
    y = np.round(y, 0)

    data = dict(
        values = z.tolist(),
        missing = missing,
        shape = z.shape,
        data_range = [float(z.min()), float(z.max())],
        x_range = [x[0], x[-1]],
        y_range = [y[0], y[-1]],
        units = dim_a.units,
        variable = variable,
    )

    return data

def get_json_data(*args, **kwargs):
    data = get_dict_data(*args, **kwargs)
    import json
    # try:
    jsondata = json.dumps(data, separators=[',',':'])
    # except Exception as error:
    #     print error.message
    #     import ipdb
    #     ipdb.set_trace()

    return jsondata
