""" Module to load outlet glacier regions
"""
from __future__ import absolute_import, division
import numpy as np

# for the projections
import cartopy.crs as ccrs
from dimarray.geo.crs import get_crs

from . import cresis
from . import boxdecker2011

MAPPING_CRESIS = cresis.MAPPING
from .standard_dataset import MAPPING as MAPPING_SD

GLACIER = None
ZOOM = 150e3

def get_region(glacier=None, zoom=None, crs=None, **kwargs):
    """ Return region coordinates for a particular glacier based on CRESIS or Box and Decker 2011

    Parameters
    ----------
    name : glacier name
    zoom : glacier width
    crs : cartopy's CRS instance (coordinate systems) 
        default same as Bamber et al 2013
    ** kwargs : passed to get_region_box (e.g. df)

    Returns
    -------
    llx, lly, urx, ury : lower and upper corners
    """
    if glacier is None: glacier = GLACIER

    # small hack: allow glacier to be already provided as llx, lly, urx, ury
    # and in that case do nothing, just adapt the zoom
    if not (isinstance(glacier, str) or isinstance(glacier, unicode)) and np.iterable(glacier) and len(glacier) == 4:
        if zoom is not None:
            llx, lly, urx, ury = glacier
            cx = (llx + urx) / 2.
            cy = (lly + ury) / 2.
            w = zoom / 2.
            glacier = cx-w, cy-w, cx+w, cy+w
        return glacier

    # full Greenland?
    if glacier.lower() == "greenland":
        # in BAMBER_SD
        llx, lly, urx, ury = -900e3, -3500e3, 800e3, -500e3
        # in case another CRS is required
        if crs is not None:
            crs0 = get_crs(MAPPING_SD)
            llx, lly = crs.transform_point(llx, lly, crs0)
            urx, ury = crs.transform_point(urx, ury, crs0)
        return llx, lly, urx, ury

    if crs is None:
        crs = get_crs(MAPPING_SD)

    if zoom is None: zoom = ZOOM

    # Return the box based on CRESIS grids
    if glacier in cresis.glaciers():
        return get_region_cresis(glacier, zoom, crs=crs)

    # Otherwise use Box and Decker 2011
    else:
        return get_region_box(glacier, zoom=zoom, crs=crs, **kwargs)

def _cresis_to_standard(xc, yc):
    """ convert cresis projection coordinate to standard projection coordinates
    """
    prj_sd = get_crs(MAPPING_SD)
    prj_cres = get_crs(MAPPING_CRESIS)
    x, y, z = prj_sd.transform_points(prj_cres, xc, yc).T
    return x, y

def get_region_cresis(name, zoom=None, crs=None): 
    """ Return region coordinates for a particular glacier based on CRESIS 

    name : glacier name
    zoom : glacier width
    crs : cartopy's CRS instance (coordinate systems) 
        default same as Bamber et al 2013
    """
    xc, yc = cresis.load_grid(name)

    # both data sets do not have the save geocentric projection: need to convert
    prj_cres = get_crs(MAPPING_CRESIS) # original coordinate system
    if crs is None:
        crs = get_crs(MAPPING_SD) # use standard grid mapping
    XC, YC = np.meshgrid(xc, yc)
    x, y,_ = crs.transform_points(prj_cres, XC, YC).T

    # select a region corresponding to the dataset
    if name == 'kogebugt':
        dx = dy = 50e3
    else:
        dx = dy = 0.

    if zoom is None:
        box = [np.min(x)-dx, np.min(y)-dy, np.max(x)+dx, np.max(y)+dy]
    else:
        box = [np.mean(x)-zoom, np.mean(y)-zoom, np.mean(x)+zoom, np.mean(y)+zoom]
    return box

def get_region_box(name, zoom=None, crs=None, df=None):
    """ Return region coordinates for a particular glacier based on Box and Decker 2011

    Parameters
    ----------
    name : glacier name
    zoom : width of the squared box (zoom)
    crs : cartopy's CRS instance (coordinate systems) 
        default same as Bamber et al 2011
    df : dataframe, optional
        Box and Decker 2011 dataset
    """
    if zoom is None: zoom = ZOOM
    w = zoom
    if df is None:
        df = get_boxdecker2011(name)

    # get coords and project onto the x, y plane
    lon, lat = -df['Longitude_W'], df['Latitude_N']
    #xx, yy = proj(lon,lat,**projpar_bamber)
    xx, yy = crs.transform_point(lon, lat, ccrs.Geodetic())

    xw = yw = w # width
    box = np.array([xx-xw, yy-yw, xx+xw, yy+yw])

    return box

def _strip_bd(nm): 
    nm = nm.replace('Jakobshavn Isbrae','jakobshavn')
    nm = nm.replace('Nioghalvfjerdsbrae/79','Nioghalvfjerdsbrae')
    if '(' in nm: # remove parenthesis
        nm = nm[:nm.find('(')-1]
    return nm.lower().replace(' ','_')

def get_boxdecker2011(name):
    """ return glacier from box and decker 2011
    """
    box2011 = boxdecker2011.load() # load Box and Decker 2011 data
    name_table = {_strip_bd(k):k for k in box2011.T.keys()}
    bname = name_table[_strip_bd(name)]
    gl = box2011.ix[bname] # extract particular glacier
    return gl

def draw_boxdecker2011(name, ax=None, crs=None):
    """ plot on a figure the location of the glacier and info about its size
    """
    import matplotlib.pyplot as plt

    if ax is None: ax = plt.gca()
    gl = get_boxdecker2011(name)

    # get coords and project onto the x, y plane
    lon, lat = -gl['Longitude_W'], gl['Latitude_N']

    if crs is not None:
        xx, yy = crs.transform(lon,lat, ccrs.Geodetic())
        ax.scatter(xx, yy,marker='x',color='k')
        circle=plt.Circle((xx,yy),gl['Width_km']*1e3,color='k', lw=1, fill=False)
        ax.add_artist(circle)

    else:
        print 'provide mapping !!'
        #matplotlib.patches.Ellipse
        ax.scatter(lon, lat)

    return gl

def print_boxdecker2011(name):
    """ plot on a figure the location of the glacier and info about its size
    """
    gl = get_boxdecker2011(name)
    print gl

def is_in_boxdecker2011(name):
    """ Is the data found in boxdecker2011 ?
    """
    try:
        get_boxdecker2011(name)
        return True
    except:
        print name,'not found in Box and Decker 2011'
        return False
