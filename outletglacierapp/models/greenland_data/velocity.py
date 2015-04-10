""" Compilation of various velocity datasets

see ipython notebook for comparison between datasets
"""
DATASET = 'joughin2010'

import numpy as np
import netCDF4 as nc

import dimarray.geo as da
from dimarray.geo.crs import get_crs
from dimarray.geo import transform, transform_vectors

from . import standard_dataset
from . import rignot_mouginot2012

def load(bbox=None, dataset=None, crs=None, maxshape=(1000,1000)):
    """ Load velocity 

    Parameters
    ----------
    bbox : bounding box (llx, lly, urx, ury)
    dataset : dataset name
        - 'joughin2010' : present in the Present Day Greenland dataset, same grid as Bamber et al 2009
        - 'rignot_mouginot2012':  Rignot and Mouginot (2012) data 
            merged product, 150 m resolution data from the Polar Year 2008/2009
            ==> ISSUES: 
                a) CRESIS-like projection 
                b) slight mismatch against Bamber et al dataset
    crs : desired coordinate reference system (cartopy.crs object)
    maxshape: maximum shape of the object, to load reduced size from netCDF
    """

    if dataset is None: dataset = DATASET

    #print "Load velocity data: ", dataset

    # present in the Present Day Greenland dataset
    # ==> ISSUES: vector components seem wrong (correspond to another coordinate 
    # system)
    if dataset == 'joughin2010':

        ncfile = standard_dataset.NCFILE
        mapping = standard_dataset.MAPPING
        data_crs = get_crs(mapping)

        if bbox is not None:
            bbox2 = bbox
            if crs is not None and crs.proj4_init != data_crs.proj4_init:
                bbox2 = transform_bbox(bbox, data_crs, crs)

            llx, lly, urx, ury = bbox2
            with nc.Dataset(ncfile) as ds:
                x = ds.variables['x1'][:]
                y = ds.variables['y1'][:]
            ind_i = np.where((y >= lly) & (y <= ury))[0]
            ind_j = np.where((x >= llx) & (x <= urx))[0]
            # ni, nj = ind_i.size, ind_j.size
            ix = (0, ind_i,ind_j)
        else:
            ix = 0

        vx = da.read_nc(ncfile, 'surfvelx', indices=ix, indexing='position')
        vy = da.read_nc(ncfile, 'surfvely', indices=ix, indexing='position')
        vx.dims = ('y', 'x') # instead of y1, x1
        vy.dims = ('y', 'x') # instead of y1, x1

        # the vector coordinates are not properly interpolated in the netCDF
        # it seems to match rignot_mouginot2012.MAPPING however.
        # fix it
        rignot_crs = get_crs(rignot_mouginot2012.MAPPING)
        vx = transform(vx, from_crs=data_crs, to_crs=rignot_crs, masked=False)
        vy = transform(vy, from_crs=data_crs, to_crs=rignot_crs, masked=False)
        data_crs = rignot_crs

        vel = da.Dataset()
        vel['vx'] = vx
        vel['vy'] = vy

    # Rignot and Mouginot (2012) data (merged product, 150 m resolution data from the Polar Year 2008/2009)
    elif dataset == 'rignot_mouginot2012':

        ncfile = rignot_mouginot2012.NCFILE
        mapping = rignot_mouginot2012.MAPPING
        data_crs = get_crs(mapping)

        # adapt bounding box to approximate standard dataset
        bbox2 = bbox
        if bbox is not None and crs is not None \
            and crs.proj4_init != data_crs.proj4_init:
            bbox2 = transform_bbox(bbox, crs, data_crs)

        vel = rignot_mouginot2012.load(bbox=bbox2, maxshape=maxshape)
        vel.dims = ('y', 'x')

    else:
        raise ValueError("unknown dataset")

    vel.grid_mapping = mapping

    # Project onto a new mapping?
    if crs is not None and crs.proj4_init != data_crs.proj4_init:
        vx = vel['vx']
        vy = vel['vy']
        vxt, vyt = da.transform_vectors(vx, vy, from_crs=data_crs, to_crs=crs)
        vel = da.Dataset(vx=vxt, vy=vyt)

    # make sure the bounding box is still respected after transformation
    if bbox is not None:
        llx, lly, urx, ury = bbox
        ix = (vel.x >= llx) & (vel.x <= urx)
        iy = (vel.y >= lly) & (vel.y <= ury)
        if np.any(~ix) or np.any(~iy):
            vel2 = da.Dataset()
            vel2._metadata(vel._metadata()) # copy metadata
            for k in vel.keys():
                vel2[k] = vel[k][iy][:, ix]
            vel = vel2

    vel.ncfile = ncfile
    vel.dataset = dataset
    #print vel.summary()
    # print 'bbox:',bbox
    # print 'data:',vel.x[0],vel.y[0],vel.x[-1], vel.x[-1]

    if vel['vx'].units is None or vel['vy'].units is None:
        raise ValueError("hey, why units are not defined?")

    return vel

def transform_bbox(bbox, crs1, crs2):
    llx, lly, urx, ury = bbox
    llx, lly = crs2.transform_point(llx, lly, crs1)
    urx, ury = crs2.transform_point(urx, ury, crs1)
    # to also compute other corners (because of rotations)
    lrx, lry = crs2.transform_point(urx, lly, crs1)
    ulx, uly = crs2.transform_point(llx, ury, crs1)
    urx = max([urx, lrx]) 
    ury = max([uly, ury]) 
    llx = min([llx, ulx]) - 100e3 # fix to rignot_mouginot2012
    lly = min([lly, lry]) 
    bbox2 = llx, lly, urx, ury
    return bbox2

