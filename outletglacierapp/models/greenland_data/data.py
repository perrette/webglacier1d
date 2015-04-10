""" Elevation and velocity datasets
"""
from __future__ import division, absolute_import

import os, warnings
import numpy as np
import matplotlib.pyplot as plt
import netCDF4 as nc

import cartopy.crs as ccrs
#import dimarray.geo.crs as dcrs
from dimarray.geo.crs import get_crs

# grids and plotting tools
#from grids import interp2 # interpolation

# Import Datasets
from .config import datadir
from . import cresis
from . import boxdecker2011 
from .rignot_mouginot2012 import load as load_vel_rm2012

# Dataset specific configuration (e.g. file names)

# Cresis
DATASET_VELOCITY = 'rignot_mouginot2012'
DATASET_VELOCITY = 'joughin2010'

def load_smb(name, **kwargs):
    return load_presentgreenland(name, 'smb',**kwargs)

def load_presentgreenland(name, *args, **kwargs):
    """ load surface velocity from 5km res present-day Greenland data 

    kwargs: 
        - mapping: None
        - passed to get_region, e.g.  "width": size of the data to be extracted (default: 150 km)
    """
    mapping = kwargs.pop('mapping',None)
    assert len(args) == 1, 'for testing: only one variable at a time'
    v = args[0]
    print "Load data:", v
    llx, lly, urx, ury = get_region(name, **kwargs) # get region box based on Box and Decker 2011
    x, y = grl.load()
    ind_i = (y >= lly) & (y <= ury)
    ind_j = (x >= llx) & (x <= urx)
    x, y, data = grl.load([v], idx=(ind_i, ind_j))
    grid = projgrid(x, y, **projpar_bamber) # same projection as bamber et al 2013

#    if 'smb' in args:
#       1/0

    # make a projection to another mapping, if needed
    if mapping is not none:
        grid = grid.proj(**mapping)

    return griddeddata(grid, {v:data})

def compare_evelation_datasets(name, v='z', datasets = none, ref=none, crange=none, sub=none, data=none):
    """ compare cresis and bamber elevation datasets

    >>> data, f, axes = fb.compare_evelation_datasets2('petermann','z', ref='cresis')
    """
    from plotting import plot_map
    if datasets is none:
        datasets = ['bamber2001','bamber2013','bamber2013u','cresis']

    if ref is none:
        ref = datasets[0]

    # load the data
    if data is none:
        data = {}
        for ds in datasets:
            data[ds] = load_elevation(name, dataset=ds)

    # make projection on a common grid (ref)
    for ds in datasets: 
        if ds == ref: continue
        data[ds].grid = data[ds].grid.proj_like(data[ref].grid)

    # use common color range
    if crange is none:
        cref = data[ref]
        npts = 15 # 15 contour lines
        crange = np.linspace(np.nanmin(cref.data[v]), np.nanmax(cref.data[v]), npts)

    # define subplots
    plt.clf()
    n = len(datasets)
    if sub is none:
        sub = (1,n)
    ni, nj = sub
    f, axes = plt.subplots(ni, nj, sharex='all', sharey='all', num=plt.gcf().number)

    # now make the plots
    for i, ds in enumerate(datasets):
        ax = axes.flatten()[i]
        d = data[ds]
        plot_map(d.x, d.y, d.data[v], ax=ax, crange=crange, orientation='horizontal')
        ax.set_title(ds)
    f.suptitle(v)

    return data, f, axes

    ## compute splines from original grid, to be evaluated on elevation grid 
    #fx = projspline(vel.x1, vel.y1, vel.vx, prjgrid=vel.grid.par, evalgrid=prj_std, kind='linear', fill_value=np.nan)
    #fy = projspline(vel.x1, vel.y1, vel.vy, prjgrid=vel.grid.par, evalgrid=prj_std, kind='linear', fill_value=np.nan)

    # compute splines from original grid, to be evaluated on the same grid 

