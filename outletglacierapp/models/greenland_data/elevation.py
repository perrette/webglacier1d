""" Elevation datasets
"""
import numpy as np
 
import dimarray.geo as da
from dimarray.geo.crs import get_crs
from dimarray.geo.projection import _inverse_transform_coords

from . import cresis
from . import bamber2013
from . import standard_dataset 
from . import morlighem2014

from . import outlet_glacier_region as region 

DATASET = 'bamber2013'
#DATASET = 'bamber2001'

def _transform_bbox(bbox, crs1, crs2):
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


def _check_subsampling(ni, nj, maxshape):
    # sub-sampling the data?
    maxi, maxj = maxshape
    si = np.floor_divide(ni, maxi)
    sj = np.floor_divide(nj, maxj)
    si = max([1, si])
    sj = max([1, sj])
    if si!=1 or sj!=1:
        print 'subsampling before coord transform (elevation): ',si,sj
    return si, sj

def load(bbox=None, dataset=None, crs=None, variable=None, maxshape=None):
    """ Load elevation data

    Parameters
    ----------
    bbox : bounding box: llx, lly, urx, ury
        if not provided, return whole domain
        for CRESIS dataset, bbox should be a glacier name
    dataset : dataset name, optional
        if not provided, use global DATASET variable
    crs : cartopy's coordinate system
    variable : {'bedrock', 'surface', 'thickness'}, optional
        load all variable if not provided
    
    Returns
    -------
    ds : dimarray.Dataset instance with 3 elevation variables
    """
    if dataset is None: 
        dataset = DATASET

    print "Load", dataset ,"elevation data"

    if dataset == 'cresis':
        glacier = bbox # for CRESIS dataset provide glacier name instead of bbox
        if glacier is None : 
            glacier = region.GLACIER
        ds = cresis.load(glacier) 
        mapping = cresis.MAPPING

    else:

        dimension_mapping = {} # variable in file that correspond to a particular dimension
        if dataset == 'bamber2001':
            ncfile = standard_dataset.NCFILE
            nms = ['topg','usrf','thk']
            xn, yn = 'x1', 'y1'
            mapping = standard_dataset.MAPPING

        elif dataset == 'bamber2013':
            ncfile = bamber2013.NCFILE
            nms = ['BedrockElevation','SurfaceElevation','IceThickness']
            xn, yn = 'projection_x_coordinate', 'projection_y_coordinate'
            dimension_mapping = {'x':xn, 'y':yn}
            mapping = bamber2013.MAPPING

        elif dataset == 'bamber2013u':
            ncfile = bamber2013.NCFILE
            nms = ['BedrockElevation_unprocessed','SurfaceElevation','IceThickness_unprocessed']
            xn, yn = 'projection_x_coordinate', 'projection_y_coordinate'
            dimension_mapping = {'x':xn, 'y':yn}
            mapping = bamber2013.MAPPING

        elif dataset == 'morlighem2014':
            ncfile = morlighem2014.NCFILE
            nms = ['bed','surface','thickness']
            xn, yn = 'x', 'y'
            mapping = morlighem2014.MAPPING

        else:
            raise Exception('Unknown dataset '+dataset)

        ds = da.open_nc(ncfile)

        # get actual dimension names (e.g. Bamber, variable name and 
        # dimension differ)
        xdim = ds.nc.variables[xn].dimensions[0] 
        ydim = ds.nc.variables[yn].dimensions[0] 

        # check size

        # Determine a region to load
        if bbox is not None:
            if dataset == 'morlighem2014':
                bamber_crs = get_crs(bamber2013.MAPPING) # original mapping
                data_crs = get_crs(mapping) # original mapping
                bbox = _transform_bbox(bbox, bamber_crs, data_crs)
            # default CRS is OK
            # data_crs = get_crs(mapping) # original mapping
            llx, lly, urx, ury = bbox
            # load axes
            x = ds.nc.variables[xn][:]
            y = ds.nc.variables[yn][:]
            ind_i = np.where((y >= lly) & (y <= ury))[0]
            ind_j = np.where((x >= llx) & (x <= urx))[0]
            if maxshape is not None:
                si, sj = _check_subsampling(ind_i.size, ind_j.size, maxshape)
                ind_i = ind_i[::si]
                ind_j = ind_j[::sj]
            ix = {ydim:ind_i,xdim:ind_j}

        else:
            if maxshape is not None:
                ni, nj = ds.nc.variables[yn].size, ds.nc.variables[xn].size
                si, sj = _check_subsampling(ni, nj, maxshape)
                ix = {ydim:slice(None,None,si),xdim:slice(None,None,sj)}
            else:
                ix = {ydim:slice(None),xdim:slice(None)}


        if dataset == 'bamber2001':
            ix['time'] = 0
            # ix = (0,) + ix # size-1 time slice in standard dataset
        else:
            pass

        nms_out = ['bedrock', 'surface', 'thickness']

        # restrict the variables to load
        if variable is not None:
             i = nms_out.index(variable) 
             nms = [nms[i]]
             nms_out = [variable]
            
        # load all
        ds = da.read_nc(ncfile, nms+dimension_mapping.values(), indices=ix, indexing='position')

        # assign appropriate axis values
        for k in dimension_mapping:
            ds.axes[k][:] = ds[dimension_mapping[k]]
            del ds[dimension_mapping[k]] # remove from dataset

        # rename variables
        ds = da.Dataset([(nm_out, ds[nm_in]) for nm_in, nm_out in zip(nms, nms_out)])

        # rename dimensions into something more handy
        assert ds.dims == (yn, xn) or ds.dims == ('y', 'x')
        # assert ds.dims == (yn, xn), repr((ds.dims, yn, xn))
        ds.dims = ('y','x')

        # just indicate the provenance
        ds.dataset = dataset
        ds.ncfile = ncfile


    # Transform to the appropriate coordinate system
    orig_crs = get_crs(mapping) # original projection system
    if crs is not None and crs.proj4_init != orig_crs.proj4_init:
        ds2 = da.Dataset()
        _, _, xt, yt = _inverse_transform_coords(orig_crs, crs, x0=ds.x, y0=ds.y) # speed-up only
        for nm in ds:
            if nm == 'mapping': continue
            ds2[nm] = da.transform(ds[nm], from_crs=orig_crs, to_crs=crs, xt=xt, yt=yt)
        ds = ds2

    return ds
