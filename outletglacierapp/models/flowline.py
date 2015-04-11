""" compute flow line 
"""
import pickle
import numpy as np
from scipy.interpolate import interp2d, RectBivariateSpline
import matplotlib.pyplot as plt
import dimarray.geo as da
from dimarray.geo.crs import get_crs

from greenland_data.velocity import load as load_velocity
from greenland_data.rignot_mouginot2012 import MAPPING as MAPPING_RM2012
from greenland_data.standard_dataset import MAPPING as MAPPING_SD
from helper import keepincache

# get equivalent cartopy transformations
CRS_RM2012 = get_crs(MAPPING_RM2012)
CRS_SD = get_crs(MAPPING_SD)

from geometry import Line, Point, Vector

PARAMS = dict(
    dx = 0.3,        		# along-flow grid step
    dy = 0.5,         		# discretization at the mouth (cross-section)

    # start/termination conditions
    vmin = 0.5, # do not start flowline if velocity under vmin
    maxdist = 800., # maximum distance for a flowline (any longer line will be discarded)

    straightness = 0.7, # max ratio between start-to-end straight and total distance of a flowline (default 0.7=1/sqrt(2))

    dataset = 'rignot_mouginot2012',
)

# def get_velocity_functions(dataset=None):
#     """ Do the interpolation thingy once for all
#     """
#     if dataset is None: 
#         dataset = PARAMS['dataset']
#     if dataset in DATA:
#         return DATA[dataset]

@keepincache
def get_velocity_functions(dataset, maxshape=None):
    vel = load_velocity(dataset=dataset, maxshape=maxshape) # RM2012 CRS
    fx = naninterpReg(vel.x, vel.y, vel['vx'].values.T, kx=1, ky=1)
    fy = naninterpReg(vel.x, vel.y, vel['vy'].values.T, kx=1, ky=1)
    return vel.x, vel.y, fx, fy

# load velocity data
def compute_one_flowline(x0, y0, dataset, maxshape=None, **kwargs):
    """ Load velocity data and compute flowline
    """
    # parameters
    dx = kwargs.pop('dx', PARAMS['dx'])*1e3 # convert to meters
    dy = kwargs.pop('dy', PARAMS['dy'])*1e3
    vmin = kwargs.pop('vmin', PARAMS['vmin'])
    maxdist = kwargs.pop('maxdist', PARAMS['maxdist'])*1e3
    straightness = kwargs.pop('straightness', PARAMS['straightness'])

    # Load velocity data around the starting point
    w = maxdist # half width of data to be loaded & interpolated
    coords = [x0-w, x0+w, y0-w, y0+w]

    x1, y1, fx, fy = get_velocity_functions(dataset=dataset, maxshape=maxshape)

    # transform starting point from standard coordinate system to velocity's
    x0 *= 1e3; y0*=1e3 # km to m
    x0, y0 = CRS_RM2012.transform_point(x0, y0, CRS_SD)
    pt0 = Point(x0, y0)
    xx, yy, v, s, t = drift_from_point(pt0, x1, y1, fx, fy, dx, vmin, maxdist=maxdist, straightness=straightness)

    # transform back to DATA's coordinate system
    prj_xyz = CRS_SD.transform_points(CRS_RM2012, xx, yy)
    xx, yy = prj_xyz[...,0], prj_xyz[...,1]
    return [{'x':xi*1e-3, 'y':yi*1e-3} for xi, yi in zip(xx, yy)]

def nans(n):
    x = np.empty(n)
    x.fill(np.nan)
    return x

class nanSplineBase(object): # works for regular grid
    """ subclass interp2d to account for NaNs in interpolated data
    """
    def __init__(self, *args, **kwargs):
            
        data = args[2]
        if 'rep_na' in kwargs:
            rep_na = kwargs.pop('rep_na')
        else:
            rep_na = 1e20
        any_nan = np.any(np.isnan(data))
        if any_nan:
            data[np.isnan(data)] = rep_na

        self._init(*args, **kwargs)
        self.any_nan = any_nan
        self.rep_na = rep_na

    def __call__(self, x, y, **kwargs):
        z = self._call(x, y, **kwargs)
        if np.ndim(z) > 0 and self.any_nan:
            z[z>self.rep_na*1e-2] = np.nan
        elif np.ndim(z) == 0 and self.any_nan:
            z = z if z > self.rep_na*1e-2 else np.nan

        if np.ndim(x) == 0 and np.ndim(z) > 0:
            z = float(z) # make sure z stays a float if input is float
            
        return z

class naninterp2d(nanSplineBase, interp2d):
    """ for interp2d
    """
    _init = interp2d.__init__
    _call = interp2d.__call__

class naninterpReg(nanSplineBase, RectBivariateSpline):
    """ for regular x / y
    """
    _init = RectBivariateSpline.__init__
    _call = RectBivariateSpline.__call__

def _drift(x0, y0, fx, fy, dx, sign = 1, maxstep = 10000, stopcond=None, straightness=0):
    """ let a point drift in a vector field with a given step

    Inputs:
    - x0, y0  : coordinates of the start Point
    - fx, fy  : spline to obtain vector coordinates at (x, y)
    - dx            : linear step 
    - sign    : [default 1] : multiply the vector field (e.g. upstream or downstream)
    - maxstep    : maximum number of steps
    - straightness : 1> > 0 , stop the drift if eddies (when > 0). if <<0, loose, if close to 1 straight

    Returns:
    - x, y     = coordinates of the trajectory
    - s        = corresponding distance, if fx, fy are velocity vectors
    - t        = corresponding "travel times", if fx, fy are velocity vectors

    NOTE: need to access Point, Line and Vector from the (own) geometry package

    Example:
    >>> from scipy.interpolate import interp2d # spline interpolation: scipy 0.12.0 needed
    >>> L = 1000. # real domain size (m)
    >>> nx, ny = 41, 41 # number of points
    >>> x1 = np.linspace(0., L, nx)
    >>> y1 = np.linspace(0., L, ny)
    >>> xx, yy = np.meshgrid(x1, y1) 
    >>> vx = np.ones((ny, nx))
    >>> vy = cos(xx/L*5)
    >>> fx = interp2d(x1, y1, vx, kind='linear', fill_value = np.nan)
    >>> fy = interp2d(x1, y1, vy, kind='linear', fill_value = np.nan)
    >>> x, y, t, s = _drift(0., 500., fx, fy, dx=1)
    >>> plt.plot(x, y)
    >>> plt.quiver(xx, yy, vx, vy)
    """
    # follow line upstream
    l = Line() # test that Line is present in workspace
    pt = Point(x0, y0)
    flowline = [pt]
    velmag = []
    totaltime = 0.
    totaldist = 0.
    time = [0.] # record total "time" (or whatever unit is fx,fy has)
    dist = [0.] # record total "time" (or whatever unit is fx,fy has)
    i = 0
    while True:

        i+=1

        # compute velocity at the desired grid point
        v = Vector(fx(pt.x, pt.y), fy(pt.x, pt.y))
        vlen = v.length()
        velmag.append(vlen) # append velocity magnitude

        if i > maxstep:
            print 'maximum number of steps reached: ', maxstep
            break

        if stopcond is not None and stopcond(x=pt.x, y=pt.y, vx=v.x, vy=v.y, v=vlen, dist=totaldist, time=totaltime):
            print 'stop condition after {:.1f} km'.format(totaldist*1e-3)
            break

        # stop if velocity vector is NaN (it would mean an invalid point)
        if np.isnan(vlen):
            flowline.pop() # remove current (invalid) point from flow line
            time.pop()
            dist.pop()
            velmag.pop()
            break

        # Stop if kick in the flowlines
        #n = int(3e3/dx) # about 10 points are used
        n = 3
        if len(flowline) >= n:
            last_two_straight = flowline[-1].distance(flowline[-n])
            if (n-1) * dx * straightness > last_two_straight:
        	print 'kick in the flowline  {}x{:.0f}m > {:.0f}m at {}'.format(straightness, (n-1)*dx, last_two_straight, totaldist)
        	flowline.pop() # remove current (invalid) point from flow line
        	time.pop()
        	dist.pop()
        	velmag.pop()
        	break
        #    else:
        #	print 'CHECK:  {}x{:.0f}m < {:.0f}m at {}'.format(straightness, (n-1)*dx, last_two_straight, totaldist)

        # give the vector its appropriate length and direction
        dt = dx / vlen # time spent to make the dx distance
        path = v * (dt * sign) # spatial displacement
        pt = pt + path # translate the point
        totaltime += dt
        totaldist += dx 

        flowline.append(pt)
        time.append(totaltime)
        dist.append(totaldist)

    if len(flowline) > 0:
        xx, yy = Line(flowline).array() # convert coordinates to numpy arrays
    else:
        xx, yy = np.array([]), np.array([])

    return xx, yy, np.array(dist), np.array(time), np.array(velmag)


def drift_from_point(pt0, x1d, y1d, fx, fy, ds, vmin = 10, maxdist=500000, straightness=0):
    """ Drift from a point, both upstream and downstream
    
    fx, fy: linear splines from vx and vx

    returns:
    x, y, v, s, t 

    x, y: coordinates 
    v : speed along flowline
    s : distance along flowline
    t : propagation time along flowline
    """
    # define a stop condition when drawing the lines
    def stopcond(**dico):
        """ stop if the velocity is less than a threshold velocity
        """
        stop = False
        if dico['v'] <= vmin:
            print 'velocity < {:.1f} m/yr:'.format(vmin),
            stop = True
        return stop

    # Do not stop if velocity too low
    v = np.sqrt(fx(pt0.x, pt0.y)**2 + fy(pt0.x, pt0.y)**2)
    if stopcond(v=v):
        print 'Stop'
        return 

    # follow line upstream
    maxstep = maxdist/ds # stop after more than 500 km...

    x1,y1,s1,t1,v1 = _drift(pt0.x, pt0.y, fx, fy, ds, sign=-1, maxstep=maxstep, stopcond=stopcond,straightness=straightness)

    # break if start point invalid (empty flowline)
    if len(x1) == 0:
        raise ValueError('invalid point')

    # follow line downstream
    x2,y2,s2,t2,v2 = _drift(pt0.x, pt0.y, fx, fy, ds, sign=1, maxstep=maxstep,straightness=straightness)

    # join with upstream line (after reversing upstream trajectory and removing pt0 from downstream traj)
    x = np.concatenate((x1[::-1], x2[1:]))
    y = np.concatenate((y1[::-1], y2[1:]))
    v = np.concatenate((v1[::-1], v2[1:]))
    s = np.concatenate((-s1[::-1], s2[1:])) # first part was upstream: negative distance
    t = np.concatenate((-t1[::-1], t2[1:])) # first part was upstream: negative time

    return x, y, v, s, t

def drift_from_section(line, x1d, y1d, vx, vy, ds, dxs, vmin = 10, maxdist=500000, straightness=0, plot=False, axes=None):
    """ Return a 2D grid made of geometric flowlines

    line: cross-section through which the glacier will be discretized
    x1d, y1d, vx, vy: velocity data and coordinates
    ds  : grid step in the direction of the flow
    dxs  : grid step transversal to the flow
    maxdist : maximum distance for a flowline
    vmin : min allowed velocity (otherwise the flowline does not start or stops)

    plot  : make plot?
    axes  : plot the lines on every axis present in axes (if plot is True)

    """
    # Regularly-spaced sampling of the line
    line = line.resample(dx=dxs)

    # Compute linear splines to interpolate velocity data
    if np.ndim(x1d) == 2:
        raise Exception('need regular grid (or check in grids.make_regular_data to add the feature)')

    #fx = naninterp2d(x1d, y1d, vx, kind='linear', fill_value=np.nan)
    #fy = naninterp2d(x1d, y1d, vy, kind='linear', fill_value=np.nan)
    fx = naninterp2d(x1d, y1d, vx, kind='linear', fill_value=np.nan)
    fy = naninterp2d(x1d, y1d, vy, kind='linear', fill_value=np.nan)

    # loop over flow lines
    flowlines = dict(
        x = [],
        y = [],
        s = [], # distance from section
        t = [], # time from section
        v = [], # velocity
    )

    for i, pt0 in enumerate(line.pts):

        try:
            xx,yy,ss,tt,vv = drift_from_point(pt0, x1d, y1d, fx, fy, ds, vmin=vmin, maxdist=maxdist, straightness=straightness)
        except ValueError:
            print "invalid point:", pt0.x, pt0.y
        continue

        # append to flowlines
        flowlines['x'].append(xx)
        flowlines['y'].append(yy)
        flowlines['s'].append(ss)
        flowlines['t'].append(tt)
        flowlines['v'].append(vv)

    if len(x) == 0:
        raise Exception('no valid line was drawn !')

    return flowlines
