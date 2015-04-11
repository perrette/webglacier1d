#!/usr/bin/python
""" Main routine to derive glacier geometry from velocity and elevation data
"""
from __future__ import division

import os, sys, copy, warnings
import datetime

import numpy as np
import matplotlib.pyplot as plt

import dimarray.geo as da
from dimarray.compat.basemap import interp
from dimarray.geo.crs import get_crs, LatitudeLongitude

# local module to create the mesh
from geometry import Line, Segment, prolonge_line, Point
from greenmap import _load_data

# # load greenland data
from greenland_data.standard_dataset import MAPPING
# from greenland_data.elevation import load as load_elevation
# from greenland_data.velocity import load as load_velocity
# from greenland_data import standard_dataset

TODAY = datetime.date.today().strftime("%Y%m%d")
AUTHOR = "mahe.perrette@pik-potsdam.de"
WORK = 'work' # work directory

def make_2d_grid_from_contours(middle, left, right, dx, ny):
    """ Transform glacier contours (middle line and side walls) into a 2-D grid
    
    The middle line is used as guide to draw regularly-spaced orthogonal 
    cross-sections, whose intersections with the walls delimit the end points.
    The segment defined by the two end points is then resampled with a
    regular interval.

    Parameters
    ----------
    middle, left, right : Line instances
        This delimits the glacier domain.
    xdata : 2-D array of x-coordinates (lon.)
    ydata : 2-D array of y-coordinates (lat.)
    dx : along-flow step on the middle-line
    ny : number of cross-flow points

    Returns
    -------
    glacier_grid : dimarray.Dataset instance
        containing x_coord and y_coord variables which represent the irregular
        grid onto which greenland data should be interpolated prior to averaging
        The first dimension reprensent the along flow, and the second cross flow 
    """
    # prolonge sides of the domain to make sure the lines intersect
    # with middle-originating cross sections
    extra = left.length() 
    left_save = copy.deepcopy(left)
    assert left.is_valid()
    assert right.is_valid()
    assert middle.is_valid()
    left = prolonge_line(left, extra, how='both')
    right = prolonge_line(right, extra, how='both')
    assert left.is_valid()
    assert right.is_valid()

    # Resample middle line with appropriate spacing
    midline = middle.resample(dx=dx, verbose=True) # resample middle line
    s = midline.s
    pts = midline.pts

    # At each grid step, draw an orthogonal line which crosses the left and right borders
    #glacierslices = GlacierSlices()
    nx = len(pts)

    x2d = np.empty((nx, ny))
    x2d.fill(np.nan)
    y2d = np.empty((nx, ny))
    y2d.fill(np.nan)

    #for i, pt in enumerate(pts):
    for i, pt in enumerate(pts):
        print '\rDiscretize: slice {} / {}'.format(i, len(pts)),

        # determine a local segment to draw an orthogonal line from
        if i == 0:
            tangent = Segment(pts[i], pts[i+1])
        else:
            tangent = Segment(pts[i-1], pts[i])

        # draw a straight line orthogonal to the local tangent (segment)
        ortho = tangent.draw_orthogonal(pt)

        # find the intersection points of the orthogonal straight line and the borders
        pt_left = ortho.intersect_line(left, closeto=pt)
        pt_right = ortho.intersect_line(right, closeto=pt)

        # Check that all points are valid (intersections were found)
        if pt_left is None or pt_right is None or np.isnan(pt_left.x + pt_left.y + pt_right.x + pt_right.y):
            #raise ValueError('invalid section !')
            raise ValueError("Invalid cross section at {} ({:.0f} km), side lines too short".format(i, s[i]*1e-3))

        # define a section line passing through the 3 points
        section = Line([pt_left, pt, pt_right])

        # resample at regular intervals ?
        section = section.resample(n=ny)

        # Fill in the grid
        xy = [(p.x, p.y) for p in section.pts]
        x2d[i], y2d[i] = zip(*xy)

    print('...done')
    if np.isnan(x2d).any() or np.isnan(y2d).any():
        raise RuntimeError('nan values in the grid !')

    # Package the grid as a dataset
    nx, ny = x2d.shape
    x0 = da.Axis(s, 'x', long_name="along-flow distance", units="meters")
    y0 = da.Axis(np.arange(ny)/(ny-1.), 'y', long_name="cross-flow fraction (0-1) from left to right", units="")
    axes = da.Axes([x0, y0])
    glacier_grid = da.Dataset()
    glacier_grid['x_coord'] = da.DimArray(x2d, axes)
    glacier_grid['y_coord'] = da.DimArray(y2d, axes)
    glacier_grid.creation_date = TODAY
    glacier_grid.author = AUTHOR
    glacier_grid.description = "2-dimensional glacier domain"

    assert len(glacier_grid.dims) == 2

    return glacier_grid


def interpolate_data_on_glacier_grid(dataset, glacier2d):
    """ Interpolate all useful data 

    Parameters
    ----------
    dataset : dimarray.Dataset instance containing data
        to interpolate onto the 2-D grid
        first dimension is the y-coordinate, second the x-coordinate
    glacier2d : dimarray.Dataset
        contains at least x_coord and y_coord variables on which to interpolate
        first dimension is along-flow, second is cross-flow

    Returns
    -------
    glacier2d : Dataset instance
        glacier2d augmented with interpolated data contained in dataset
    """
    assert len(glacier2d.dims) == 2
    assert len(dataset.dims) == 2

    xout = glacier2d['x_coord'].values
    yout = glacier2d['y_coord'].values

    xin = dataset.axes[1].values
    yin = dataset.axes[0].values

    for nm in dataset.keys():
        tmp = interp(dataset[nm].values, xin, yin, xout, yout)
        glacier2d[nm] = da.DimArray(tmp, glacier2d.axes)
        glacier2d[nm]._metadata(dataset[nm]._metadata()) # copy metadata

    glacier2d.description = "Greenland data interpolated onto the glacier domain"
    glacier2d.author = AUTHOR
    glacier2d.creation_date = TODAY

    return glacier2d

def glacier_crossflow_average(glacier2d):
    """ Average 2-D glacier data into a flowline glacier

    Glacier data is averaged along each cross section.
    Glacier width is also computed.

    Parameters
    ----------
    glacier2d : Dataset instance containing glacier data

    Returns
    -------
    glacier1d : flowline glacier
        contains at least width, coordinates, and along-flow distance
    """
    x2d = glacier2d['x_coord'].values
    y2d = glacier2d['y_coord'].values

    # compute width along the glacier
    width = ((x2d[:, 0] - x2d[:,-1])**2 + (y2d[:, 0] - y2d[:,-1])**2)**0.5

    glacier1d = da.Dataset()
    glacier1d['W'] = da.DimArray(width, [glacier2d.axes[0]])
    glacier1d['W'].long_name = 'glacier width'
    glacier1d['W'].units = 'meters'

    for nm in glacier2d.keys():
        glacier1d[nm] = glacier2d[nm].mean(axis=1, skipna=False)
        glacier1d[nm]._metadata(glacier2d[nm]._metadata())

        # check nans
        if np.any(np.isnan(glacier1d[nm])):
            # Fill up the NaNs
            print glacier1d[nm].values
            warnings.warn("NaNs remain after averaging glacier for variable "+nm)

    # add lon/lat info based on back-transformed x_coord, y_coord
    # from cartopy.crs import PlateCarree
    CRS = get_crs(MAPPING)
    pts_xyz = LatitudeLongitude().transform_points(CRS, glacier1d['x_coord'].values, glacier1d['y_coord'].values)
    glacier1d['lon'] = da.DimArray(pts_xyz[...,0], glacier1d.axes)
    glacier1d['lat'] = da.DimArray(pts_xyz[...,1], glacier1d.axes)

    glacier1d.author = "mahe.perrette@pik-potsdam.de"
    glacier1d.creation_date = TODAY
    glacier1d.description = "1-D representation of a Greenland outlet glacier"

    return glacier1d

def _get_glacier_bbox(glacier_grid):
    m = 0*1e3 # margin
    return [glacier_grid['x_coord'].min()*1e-3 - m,
            glacier_grid['x_coord'].max()*1e-3 + m,
            glacier_grid['y_coord'].min()*1e-3 - m,
            glacier_grid['y_coord'].max()*1e-3 + m]

#
# Another version of extractglacier1d, should be faster...
#
def extractglacier1d(glacier_grid, datasets):
    """
    """
    # Interpolate various datasets onto the grid
    glacier2d = copy.copy(glacier_grid) # just to keep glacier_grid clean

    # determine bounding box that encloses the glacier data
    coords = _get_glacier_bbox(glacier_grid)

    # Elevation
    if datasets['bedrock'] == "morlighem2014":
        # ...special treatment for Morlighem, which is on a different grid
        # ==> instead of loading a large grid and making the projections, 
        # just project the coords onto Morlighem grid.
        # also load Bamber et al 2013 as fill values

        from greenland_data import morlighem2014
        crs_disk = get_crs(morlighem2014.MAPPING)
        crs_target = get_crs(MAPPING)
        glacier2d_prj, coords_prj = _prepare_load_prj(glacier_grid, crs_disk, crs_target)

        # load data
        l,r,b,t = [v*1e3 for v in coords_prj] # km => m
        indexer = {'x':slice(l,r), 'y':slice(b,t)}
        ds_prj = morlighem2014.load(['bed', 'surface', 'thickness'], indexer, tol=1e3) # 1000 m tolerance, since 150 res
        ds_prj.rename_keys({'bed':'zb', 'surface':'hs','thickness':'H'}, inplace=True)
        ds_prj['H'][np.isnan(ds_prj['H'])] = 0.
        ds_prj.write_nc("test_morlighem_raw.nc")
        glacier2d_prj = interpolate_data_on_glacier_grid(ds_prj, glacier2d_prj)
        glacier2d_prj.write_nc("test_morlighem_interp.nc")

        # complement NaN values with bamber2013 dataset?
        # load Bamber et al 2013
        zb = _load_data(coords, 'bedrock', 'bamber2013') 
        hs = _load_data(coords, 'surface', 'bamber2013') 
        H = _load_data(coords, 'thickness', 'bamber2013') 
        H[np.isnan(H)] = 0.
        dataset = da.Dataset({'zb':zb, 'hs':hs, 'H':H}) 
        dataset.write_nc("test_bamber_raw.nc")
        glacier2d = interpolate_data_on_glacier_grid(dataset, glacier2d)
        glacier2d.write_nc("test_bamber_interp.nc")

        # fill nan values
        # ...determine grid boxes to be filled with Bamber
        null = np.zeros_like(glacier2d['H'], dtype=bool)
        for k in glacier2d_prj.keys():
            if k in ('x_coord','y_coord'): continue
            null = null | np.isnan(glacier2d_prj[k].values)

        # ...fill values
        for k in glacier2d_prj.keys():
            if k in ('x_coord','y_coord'): continue
            # take Morlighem, fill NaNs with Bamber et al 2013
            values = glacier2d_prj[k].values
            fill_values = glacier2d[k].values
            values[null] = fill_values[null]
            glacier2d[k] = da.DimArray(values, axes=glacier2d.axes)

    else:
        # just load the data normally
        zb = _load_data(coords, 'bedrock', datasets['bedrock'])
        hs = _load_data(coords, 'surface', datasets['bedrock'])
        H = _load_data(coords, 'thickness', datasets['bedrock'])
        # replace NaN in thickness with zero
        H[np.isnan(H)] = 0.
        dataset = da.Dataset({'zb':zb, 'hs':hs, 'H':H}) 
        glacier2d = interpolate_data_on_glacier_grid(dataset, glacier2d)

    glacier2d['hb'] = glacier2d['hs'] - glacier2d['H']

    # check that hb >= zb
    water_under_glacier = glacier2d['hb'].values - glacier2d['zb'].values
    prec = 1e-2 # data precision (in meters)
    if np.any(water_under_glacier < -prec):
        # make stats
        count = np.sum((water_under_glacier) < -prec)
        d = water_under_glacier[water_under_glacier<-prec]
        assert d.ndim == 1
        stats = "#:{} - mean(min,max):{}({},{}), 50(5,95):{}({},{})".format(
            count, d.mean(), d.min(), d.max(), *np.percentile(d, [50,5,95])
        )
        warnings.warn("{} glacier bottom values are lower than bedrock within {} m precision!\n{}\nLower bedrock.".format(count, prec, stats))
        glacier2d.bedrock_dataset = datasets['bedrock']
        # glacier2d.write_nc("glacier2d.nc")
        bad = water_under_glacier<0
        glacier2d['zb'][bad] = glacier2d['hb'][bad]

    # Velocity
    velocity = _load_data(coords, 'velocity_mag', datasets['velocity_mag'], maxshape=(300,300))  # load data at lower resolution : TODO: see Morlighem et al 2012
    assert velocity.units.strip() in ('meter/year','meters/year'), "check out velocity units: "+repr(velocity.units)
    velocity.values /= 3600*24*365.25
    velocity.units = "meters / second"
    dataset = da.Dataset({'U':velocity})
    glacier2d = interpolate_data_on_glacier_grid(dataset, glacier2d)

    # also add surf / basal velocity /and runoff from the standard dataset.
    ds = da.Dataset()
    for nm in ['surfvelmag','balvelmag','runoff']:
        a = _load_data(coords, nm, 'standard_dataset')
        a.values /= 3600*24*365.25
        a.units = "meters / second"
        ds[nm] = a
    glacier2d = interpolate_data_on_glacier_grid(ds, glacier2d)

    # Surface mass balance
    smb = _load_data(coords, 'smb', datasets['smb'])
    assert smb.units.strip() == 'meters/year', "check out smb units"
    smb.values /= 3600*24*365.25
    smb.units = "meters / second"
    dataset = da.Dataset({'smb':smb})
    glacier2d = interpolate_data_on_glacier_grid(dataset, glacier2d)

    glacier2d.write_nc("outletglacierapp/appdata/glacier2d.nc")

    # Export to 1-D glacier
    glacier1d = glacier_crossflow_average(glacier2d)

    return glacier1d


def _prepare_load_prj(glacier_grid, crs_disk, crs_target):
    pts = crs_disk.transform_points(crs_target, glacier_grid['x_coord'].values, glacier_grid['y_coord'].values)
    x, y = pts[...,0], pts[...,1] # grid 
    glacier2d_prj = glacier_grid.copy()
    glacier2d_prj['x_coord'][:] = x
    glacier2d_prj['y_coord'][:] = y
    coords_prj = _get_glacier_bbox(glacier2d_prj) # bbox for morlighem2014
    return glacier2d_prj, coords_prj
