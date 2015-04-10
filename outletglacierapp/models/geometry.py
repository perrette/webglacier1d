from __future__ import division
import numpy as np
import bisect # find element in sorted list
from copy import deepcopy as cp

""" Contain classes to represent geometric objects (Point, Vector, StraightLine,
Line, Segment) and perform some simple geometric operation (translation, draw 
orthogonal line, distance, intersection)
"""
def is_sorted(l):
    """ test whether a list is sorted
    """
    return l == sorted(l)

def prolonge_line(line, dist, how='end'):
    """ Prolonge a line
    line: line
    dist: distance by which it should be prolonged
    """
    assert line.is_valid()
    if how == 'start':
	return prolonge_line(line.revert(), dist, how='end').revert()
    elif how == 'both':
	l1 = prolonge_line(line, dist, how='start')
	return prolonge_line(l1, dist, how='end')

    assert line.is_valid()
    end_vect = Vector.fromPoints(*line.pts[-2:])
    assert end_vect.length() > 0
    newpoint = line.pts[-1] + end_vect * (dist/end_vect.length())
    newline = line
    newline.pts = newline.pts + [newpoint]
    assert newline.is_valid()
    return newline

class ExtractLinearGridData(object):
    """ class to which allow data to be extracted from a grid along a line
    """
    def __init__(self, pts, xdata, ydata, method='nearest neighbor', auto=True):
	"""
	"""
	self.method = method 

	# save the fields for the record
	self.pts = pts
	self.xdata = xdata
	self.ydata = ydata

	if auto:
	    self._extract_indices()

    def subset(self, i1, i2):
	""" return info for a subset of the line
	"""
	if self.method == 'nearest neighbor':
	    # do not need to proceeed to index matching again 
	    obj = ExtractLinearGridData(pts=self.pts[i1:(i2+1)], xdata=self.xdata, ydata=self.ydata, method=self.method, auto=False)
	    obj.indices = self.indices[i1:(i2+1)]
	    obj.errors = self.errors[i1:(i2+1)]

	else:
	    obj = ExtractLinearGridData(pts=self.pts[i1:(i2+1)], xdata=self.xdata, ydata=self.ydata, method=self.method)

	return obj
	    
    def _extract_indices(self):
	""" Prepare method-dependent extraction, e.g. indice-matching for nearest neighbor 
	"""
	if self.method == 'nearest neighbor':
	    res = self._extract_indices_nn(self.pts, self.xdata, self.ydata, error=True)
	    self.indices = res[0]
	    self.errors = res[1]

    @staticmethod
    def _extract_indices_nn(pts, xdata, ydata, error=True):
	""" Extract a coordinates indices along a list of points using nearest neighbours
	"""
	indices = []
	errors = [] # indicate the error as distance from the correct grid point
	for pt in pts:
	    if pt is None:
		print 'invalid point, cannot extract data'
		indices.append(np.nan)
		errors.append(np.nan)

	    i = np.argmin(np.abs(ydata[:,0] - pt.y))
	    j = np.argmin(np.abs(xdata[0,:] - pt.x))
	    indices.append((i,j))

	    # compute error as distance from the correct grid point
	    if error:
		pt_true = Point(xdata[0,j],ydata[i,0]) # true point on the grid
		errors.append(pt.distance(pt_true)) # distance from point on the line

	if error:
	    return indices, errors
	else:
	    return indices

    def extract(self, zdata):
        """ extract actual data based on pre-computed grid indices
        """
        if self.method == 'nearest neighbor':
            i,j = zip(*self.indices[:])
            extracted_data = zdata[i,j]
            return extracted_data
#
# Define a few geometric objects
#
class Point(object):
    """ Point
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, pt):
        return self.x == pt.x and self.y == pt.y

    def __add__(self, v):
        return self.translate(v)

    def __repr__(self):
        return 'P'+repr((self.x, self.y))

    def distance(self, pt):
        return  np.sqrt((self.x-pt.x)**2+(self.y-pt.y)**2)

    def translate(self, v):
        return Point(self.x+v.x, self.y+v.y)

class Vector(object):
    """ Vector 
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __mul__(self, x):
        return self.mult(x)

    def __repr__(self):
        return 'V'+repr((self.x, self.y))

    @staticmethod
    def fromPoints(pt1, pt2):
        """ Initialize from two Points
        """
        return Vector(pt2.x - pt1.x, pt2.y - pt1.y)

    def xproduct(self, v):
        """ vector product: gives area of parallelogram and is positive if anti-clockwise
        """
        return self.x*v.y - self.y*v.x

    def sproduct(self, v):
        """ vector product: gives area of parallelogram and is positive if anti-clockwise
        """
        return self.x*v.x + self.y*v.y

    def mult(self, alpha):
        return Vector(self.x*alpha, self.y*alpha)

    def length(self):
        """ vector length
        """
        return Segment(Point(0.,0.),Point(self.x, self.y)).length()

class Segment(object):
    """ Segment (defined by two points)
    """
    def __init__(self, pt1, pt2):
        self.pt1 = pt1
        self.pt2 = pt2

    def __eq__(self, seg):
        return (self.pt1 == seg.pt1 and self.pt2 == seg.pt2) or (self.pt1 == seg.pt2 and self.pt2 == seg.pt1)

    def __repr__(self):
        return '|'+repr(self.pt1)+'--'+repr(self.pt2)+'|'

    def length(self):
        """ return segment length
        """
        return  np.sqrt((self.pt2.x-self.pt1.x)**2+(self.pt2.y-self.pt1.y)**2)

    def intersects(self, s, loose = False):
        """ Point of intersection between two segments, 
        or None if no intersection

        loose = 0, False 
              = 0.5 
              = 1, True

        Just reason on vectors: find alpha such as:
        p + alpha*v1 = q + beta*v2
        alpha*v1 = p-->q + beta*v2
        alpha = (p-->q) x v2 / (v1 x v2) where x is cross-product (v2 x v2 = 0)

        (or beta = (p-->q) x v1 / (v1 x v2)
        """
        v1 = Vector.fromPoints(self.pt1, self.pt2)
        v2 = Vector.fromPoints(s.pt1,s.pt2)
        v3 = Vector.fromPoints(self.pt1,s.pt1)

        # parametric coordinate on self given as a vector product 
        # (just to the math equating two parametric equations)
        alpha = v3.xproduct(v2) / v1.xproduct(v2)

        if not loose or loose == 0.5:

            # loose == False or 1: look at self
            if alpha < 0 or alpha > 1:
                return None

            # also look at the coef from the second vector
            if loose is False:
                beta = v3.xproduct(v1) / v1.xproduct(v2)
                if beta < 0 or beta > 1:
                    return None

        #pt = self.pt1.translate( v1.mult(alpha) )
        pt = self.pt1 + v1*alpha

        return pt

    def draw_orthogonal(self, pt):
        """ Return a straight line going throught a point pt
        and orthogonal to the segment.
        """

        v = self.to_vector()

        # find another point to draw an orthogonal line: X1, Y1 => X2=1, Y2 so that X1*1+ Y1*Y2 = 0 => Y2 = -X1/Y1
        vorth = Vector(1, -v.x/v.y) * self.length() # length scaling is not needed, here only for plotting
        pt2 = pt + vorth

        # Now define a Straighline
        return StraightLine(pt, pt2)


    def is_valid(self):
        return self.pt1 is not None and self.pt2 is not None

    def to_vector(self):
        """ returns a vector colinear to and of same length as the segment
        """
        return Vector.fromPoints(self.pt1, self.pt2)

class StraightLine(object):
    """ Straight Line
    """
    def __init__(self, pt1, pt2):
        self.pt1 = pt1
        self.pt2 = pt2

    def __repr__(self):
        return '<--'+repr(self.pt1)+'--'+repr(self.pt2)+'-->'

    def parallel(self, l):
        """ is the straight line parallel to another ?
        """
        v1 = Vector.fromPoints(self.pt1, self.pt2)
        v2 = Vector.fromPoints(l.pt1,l.pt2)
        return v1.xproduct(v2) == 0.

    def intersect_line(self, l, raise_error = True, closeto=None):
        """ return intersection point between straight line and an other line
        """
        seg0 = Segment(self.pt1, self.pt2)
        intersections = []
        for seg in l.loop_over_segments():
            #pt = seg0.intersects(seg, loose = 0.5) 
            pt = seg.intersects(seg0, loose = 0.5) 
            if pt is not None:
                intersections.append(pt)

        if len(intersections) == 0 and raise_error:
            # import warnings
            print "warnings",'{} does not interesect line !'.format(closeto)
            #warnings.warn('{} does not interesect line !'.format(closeto))
            return closeto
            #raise Exception('does not interesect line !')

        # get the closest intersection
        if len(intersections) == 1:
            pt = intersections[0]
        else:
            #print "\nseveral intersections", intersections
            #print "closeto", closeto
            if closeto is None: 
                closeto= self.pt1
            distances = [(pt.x-closeto.x)**2+(pt.y-closeto.y)**2 for pt in intersections]
            i = np.argmin(distances)
            pt = intersections[i]
            #print "chosen", pt

        return pt

class Line(object):
    """ A line is defined by a list of points
    """
    def __init__(self, list_of_points = None):
        if list_of_points is None:
            self.pts = []
        else:
            self.pts = list_of_points

        # compute the curvilinear coordinate of the curve based on distance
        self.s = self.distance()

    def is_valid(self):
        """ Are all the points of the line valid ?
        """
        val = True
        for pt in self.pts:
            if pt is None or np.isnan(pt.x+pt.y):
                val = False
                break
        return val

    def append(self, pt):

        # compute the curvilinear coordinate of the curve based on distance
        #self.s = self.distance()

        if len(self.pts) > 0:
            newdist = self.s[-1] + self.pts[-1].distance(pt) # update total distance
            self.s.append(newdist)
        else:
            self.s = [0.]

        self.pts.append(pt)
        #self.s = self.distance()

    def loop_over_segments(self):
        """ loop over segments making the line
        """
        for i in range(1, len(self.pts)):
            yield Segment(self.pts[i-1], self.pts[i])

    def length(self):
        """ total length of the line
        """
        #return sum(seg.length() for seg in self.loop_over_segments())
        return self.s[-1]  # s is always kept up to date 

    def remove(self, i):
        pt = self.pts.pop(i)
        self.s = self.distance() # update distance

    def distance(self):
        """ distance along the line
        """
        if len(self.pts) == 0:
            return []
        elif len(self.pts) == 1:
            return [0]
        else:
            totlength = 0.
            dist = [0.]
            for i,pt in enumerate(self.pts[1:]):
                totlength += pt.distance(self.pts[i])
                dist.append(totlength)
            
        if len(dist) > 0 and dist[0] != 0:
            raise Exception('distance is doing sthg wrong')

        if not is_sorted(dist):
            raise Exception('distance is doing sthg wrong')

        return dist
    
    def locate(self, x):
        """ locate a point on the line based on along-flow coordinate
        
        returns point and the segment it belongs to (oriented in the flow direction)
        """
        if x > self.s[-1]:
            raise Exception('longer than original line !')

        # find the index for insertion...
        #i = bisect.bisect_left(self.s, x) - 1
        i = 0
        while (self.s[i+1] < x):
            i += 1

        if x < self.s[i] or x > self.s[i+1]:
            print 'x=',x,' not in ',self.s[i],'-',self.s[i+1] 
            raise Exception('hey, problem when locating x')

        seg = Segment(self.pts[i], self.pts[i+1])

        # find the adequate point on the segment
        alpha = (x - self.s[i])/(self.s[i+1]-self.s[i])
        pt = self.pts[i] + seg.to_vector() * alpha

        return pt, seg, i

    def draw_orthogonal(self, x):
        """ Return an orthogonal straight line going throught the point indexed by the curvilinear coordinate

        x: curvilinear coordinate = along-flow distance
        """

        pt, seg, i = self.locate(x)

        return seg.draw_orthogonal(pt)

    def resample(self, dx = None, n = None, nmax=None, verbose=False):
        """ resample a line with a particular grid step
        """
        pts = []

        # subdivide to maintain a given grid step
        if dx is not None:
            xx = np.arange(0,self.length(), dx)

            # if too many grid points, use a criterion based on max point number instead
            if nmax is not None and len(xx) > nmax:
                n = nmax

        # subdivide in a number of equally-spaced segments
        if n is not None:
            xx = np.linspace(0, self.length(), n) 

        for x in xx:
            pt, seg, i = self.locate(x)
            if verbose: print '\rresample:',x,' on ', i,
            pts.append(pt)
        if verbose: print '\rresample:',x,' on ', i,'...done'

        return Line(pts)

    def array(self):
        """ Export to numpy arrays
        return: x, y
        """
        x, y = zip(*[(pt.x, pt.y) for pt in self.pts])
        return np.array(x), np.array(y)

    @classmethod
    def from_array(cls, x, y):
        """ define a line from x, y coordinate arrays
        """
        n = len(x)
        return cls([Point(x[i],y[i]) for i in range(n)])

    def copy(self):
        return cp(self)

    def revert(self):
        l = self.copy()
        l.pts.reverse()
        return l
