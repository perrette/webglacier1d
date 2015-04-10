""" An app to draw glacier geometry on top of a background image (local plotly)
"""
from outletglacierapp import app
import os
import warnings
import itertools
import json
import numpy as np

from flask import Flask, redirect, url_for, render_template, request, jsonify, flash, session, abort, make_response, send_from_directory
from forms import MapForm, FlowLineForm, ExtractForm, MeshForm
from config import glacier_choices, datadir, maxpixels as MAXPIXELS

import dimarray as da
from models.greenmap import get_dict_data, get_json_data, _load_data, get_coords
from models.flowline import compute_one_flowline
from models.mesh import make_2d_grid_from_contours, Point, Line, extractglacier1d
from models.glacier1d import massbalance_diag

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field: %s" % (
                getattr(form, field).label.text,
                error
            ))

def getmeshpath(session):
    if 'mesh2d' not in session:
        session['mesh2d'] = 'mesh2d.nc'
    return os.path.join(datadir, session['mesh2d'])

def getglacierpath(session):
    if 'glacier1d' not in session:
        session['glacier1d'] = 'glacier1d.nc'
    return os.path.join(datadir, session['glacier1d'])

def getlinepath(session):
    if 'lines' not in session:
        session['lines'] = 'lines.json'
    if type(session['lines']) is list:
        warnings.warn('lines is a list for some reason')
        session['lines'] = 'lines.json'
    return os.path.join(datadir, session['lines'])

def get_map_form(session):
    """ instantiate and define MapForm based on session parameters
    """ 
    form = MapForm()
    # update form based on session parameters
    if 'variable' in session and 'dataset' in session:
        form.dataset.data = session['variable']+' - '+ session['dataset']
    if 'coords' in session:
        print 'document coords',session['coords']
        form.left.data = session['coords'][0]
        form.right.data = session['coords'][1]
        form.bottom.data = session['coords'][2]
        form.top.data = session['coords'][3]
    if 'glacier' in session:
        form.glacier.data = session['glacier']
    if 'maxpixels' in session:
        form.maxpixels.data = session['maxpixels']
    return form

def get_form(form, session):
    """ initialize Form with session parameters (be careful, risk of conflict)
    """
    for k in form.data.keys():
        nm = form.__class__.__name__+'_'+k
        if nm in session:
            # form.data[k] = session[nm] # flask bug??? does not work
            getattr(form, k).data = session[nm]
    return form

def set_form(form, session):
    for k in form.data.keys():
        nm = form.__class__.__name__+'_'+k
        # print "set param",nm,"with",session[nm],"to session"
        session[nm] = form.data[k]

@app.route('/')
def index():
    return redirect(url_for('drawing'))

@app.route('/drawing')
def drawing():
    #return redirect(url_for('map'))
    form = get_map_form(session)
    meshform = get_form(MeshForm(), session)
    # if 'variable' in session
    return render_template('drawing.html', form=form, flowline=FlowLineForm(), meshform=meshform, hidemeshform=True)

@app.route('/googlemap')
def googlemap():
    #return redirect(url_for('map'))
    # form = get_map_form(session)
    # if 'variable' in session
    meshform = get_form(MeshForm(), session)
    return render_template('googlemap.html', flowline=FlowLineForm(), meshform=meshform, hidemeshform=True)

@app.route('/reset', methods=["POST"])
def reset():
    # if 'mesh' in session: del session['mesh']
    # if 'lines' in session: del session['lines']
    if 'variable' in session: del session['variable']
    if 'dataset' in session: del session['dataset']
    if 'coords' in session: del session['coords']
    if 'glacier' in session: 
        del session['glacier']
    return redirect(url_for('drawing'))

@app.route('/mapdata', methods=["GET"])
def mapdata():
    """ return json data to plot map on Greenland domain
    """
    form = MapForm(request.args)
    if not form.validate():
        flash_errors(form)

    # define session parameters
    variable, source = form.dataset.data.split('-')

    # save these parameters in session just in case, but is not used
    # but leave GET to make testing easier
    session['variable'] = variable.strip()
    session['dataset'] = source.strip()
    session['glacier'] = form.glacier.data

    # update coordinates to get a fixed aspect ratio
    r = 1
    currentwidth = form.right.data - form.left.data
    width = r*(form.top.data - form.bottom.data)
    form.right.data += (width-currentwidth)/2 
    form.left.data -= (width-currentwidth)/2 
    session['coords'] = [form.left.data, form.right.data, form.bottom.data, form.top.data]
    

    coords = session['coords'] # coordinates (can be custom)
    variable = session['variable'] # coordinates (can be custom)
    dataset = session['dataset'] # coordinates (can be custom)

    if 'maxpixels' in session:
        maxshape = (session['maxpixels'],)*2
    else:
        maxshape = (MAXPIXELS,)*2
    data = get_json_data(variable, dataset, coords, maxshape=maxshape)
    return make_response(data) #, type='application/json')

    # data = get_dict_data(session)
    # return jsonify(**data)

@app.route('/glacierinfo')
def glacierinfo():
    """ provide glacier coordinate information from box and decker
    """
    # indicate the same list of glaciers as in settings
    data = [{'name':nm, 'coords':get_coords(nm)} for nm in glacier_choices if nm.lower() != 'custom']
    return jsonify(glacierinfo=data)

@app.route('/flowline', methods=['GET'])
def flowline():
    """ compute flowline given a starting point
    """
    # starting point in km
    # x = float(request.get('x'))
    # y = float(request.get('y'))
    # dx = float(request.get('dx'))
    # maxdist = float(request.get('maxdist'))
    # dataset = request.form.get('dataset')
    form = FlowLineForm(request.args)

    line = compute_one_flowline(form.x.data, form.y.data, dx=form.dx.data, maxdist=form.maxdist.data,
                                dataset=form.dataset.data)
    return jsonify(line=line)

@app.route('/lines', methods=['GET','POST']) 
def lines():
    if request.method == 'GET':
        lines = _getlines(session)
        return jsonify(lines=lines)
    else:
        lines = request.json
        _setlines(session, lines)
        return jsonify(lines=lines)

def _getlines(session):
    linepath = getlinepath(session)
    if os.path.exists(linepath):
        with open(linepath,'r') as f:
            lines = json.load(f)
    else:
        lines = []
    return lines

def _setlines(session, lines):
    linepath = getlinepath(session)
    with open(linepath,'w') as f:
        lines = json.dump(lines, f)

@app.route('/lineslonglat', methods=['GET','POST']) 
def lineslonglat():
    import cartopy.crs as ccrs
    from models.greenmap import CRS
    longlat = ccrs.PlateCarree()

    def transform_line(line, crs0, crs1):
        " transform a line between two coordinate systems "
        x, y = zip(*[(pt['x'], pt['y']) for pt in line['values']])
        x, y = np.array(x), np.array(y)

        if crs0 != longlat:
            x *= 1e3
            y *= 1e3

        pts_xyz = crs1.transform_points(crs0, x, y)

        if crs1 != longlat:
            pts_xyz /= 1e3

        lon, lat = pts_xyz[...,0], pts_xyz[...,1]
        newvalues = [{'x':lo, 'y':la} for lo, la in zip(lon, lat)]
        if np.any(~np.isfinite(pts_xyz)):
            raise RuntimeError("nan or inf in points !")
        return {'id':line['id'], 'values':newvalues}

    if request.method == 'GET':
        lines = _getlines(session)

        longlatlines = [transform_line(line, CRS, longlat) for line in lines]
        # lines = [transform_line(line, longlat, CRS) for line in longlatlines]

        return jsonify(longlatlines=longlatlines)
    else:

        print "received longlat", request.json
        #lines = [transform_line(line, longlat, CRS) for line in request.json]
        lines = [transform_line(line, longlat, CRS) for line in request.json]
        print "transformed xy", lines
        _setlines(session, lines)
        # return jsonify(msg='all good')
        return jsonify(lines=lines)
        # return jsonify(lines=lines)

@app.route('/mesh', methods=['GET', 'POST'])
def mesh():

    meshpath = getmeshpath(session)

    if request.method == 'GET':

        try:
            ds = da.read_nc(meshpath)
        except:
            raise
            raise ValueError("mesh file not found, create mesh via POST first (Save and Mesh button)")
            flash("mesh file not found, create mesh via POST first (Save and Mesh button)")
            return jsonify(url=url_for('drawing'))

        mesh = [[{'x':x*1e-3, 'y':y*1e-3, 's':s*1e-3} for x, y in zip(xs_section, ys_section)] for xs_section, ys_section, s in zip(ds['x_coord'], ds['y_coord'], ds.x)]

        # return redirect(url_for('/viewmesh'))
        return jsonify(mesh=mesh)

    else:
        # compute mesh and return the data extraction page
        lines = _getlines(session)

        meshform = MeshForm(request.form)
        set_form(meshform, session) # make request persistent

        dx = meshform.data['dx']
        ny = meshform.data['ny']

        if len(lines) == 0:
            flash('no lines found !')
            return jsonify(url=url_for('drawing'))
        elif len(lines) != 3:
            flash('3 lines expected !')
            return jsonify(url=url_for('drawing'))

        linedict = {line['id'].lower(): line['values'] for line in lines}

        if set(linedict.keys()) != {'left','right','middle'}:
            flash('Unxpected line ids. Expected: {}, got: {}'.format(['left','right','middle'],linedict.keys()))
            return jsonify(url=url_for('drawing'))

        # make Lines objects
        for nm in ['middle','left','right']:
            linedict[nm] = Line([Point(pt['x']*1e3, pt['y']*1e3) for pt in linedict[nm]]) # make a Line object

        # # build fake mesh for testing
        # ny = 5 
        # nx = len(session['lines'][0])
        # mesh = [[{'x':pt['x']+20*j,'y':pt['y']+20*j} for j in range(ny)] for pt in session['lines'][0]['values']]

        dima_mesh = make_2d_grid_from_contours(dx=dx, ny=ny, **linedict)
        dima_mesh.write_nc(meshpath, 'w') # write mesh to disk

        # return jsonify(url=url_for('viewmesh'))
        return redirect(url_for('mesh'))

@app.route('/viewmesh')
def viewmesh():
    """ mesh / glacier view
    """
    mapform = get_map_form(session)
    extractform = get_form(ExtractForm(), session)
    meshform = get_form(MeshForm(), session)
    return render_template('mesh.html', form=mapform, extractform=extractform, meshform=meshform)

@app.route('/meshoutline', methods=['GET', 'POST'])
def meshoutline():
    """ extract glacier1d outlines (lines) from existing mesh
    """
    meshpath = getmeshpath(session)
    if not os.path.exists(meshpath):
        raise ValueError("mesh file unavailable: "+meshpath)
    x_coord = da.read_nc(meshpath,'x_coord').values*1e-3
    y_coord = da.read_nc(meshpath,'y_coord').values*1e-3

    ni, nj = x_coord.shape
    left = []
    middle = []
    right = []
    lines = [{'id':'middle', 'values':[]}, 
             {'id':'left', 'values':[]}, 
             {'id':'right', 'values':[]}]

    for i in range(ni): # loop over sections
        lines[0]['values'].append({'x':x_coord[i][int(nj/2)], 'y':y_coord[i][int(nj/2)]})
        lines[1]['values'].append({'x':x_coord[i][0], 'y':y_coord[i][0]})
        lines[2]['values'].append({'x':x_coord[i][-1], 'y':y_coord[i][-1]})

    # if POST, make it the default line
    if request.method == 'POST':
        _setlines(session, lines)

    return jsonify(lines=lines)


# @app.route('/data1d/<name:variable>/<name:dataset>', methods=['GET'])
# def extract_one_variable(variable, dataset):
#     """ extract one variable from the netCDF file
#     """

@app.route('/glacier1d', methods=['GET', 'POST'])
def make_glacier1d():
    """ extract data 
    """
    meshpath = getmeshpath(session)
    glacierpath = getglacierpath(session)

    if request.method == 'POST':
    # if request.method == 'GET':
        extractform = ExtractForm(request.form)
        # extractform = ExtractForm()
        mesh = da.read_nc(meshpath)
        glacier1d = extractglacier1d(mesh, extractform.data)
        # quick fix SMB shifted upward
        # glacier1d['smb'].values += (0.2/(3600*24*365.25))
        # glacier1d['smb'].note = "increased by 0.2 m/year, uniformly"
        glacier1d.write_nc(glacierpath, 'w')

        return redirect(url_for('vizualize_glacier1d'))  # get method

    elif request.method == 'GET':
        raise ValueError("no GET route for /glacier1d, try /figure/glacier1d")

@app.route("/figure/glacier1d")
def vizualize_glacier1d():
    """ return data to make a figure
    """
    # read glacier data
    glacierpath = getglacierpath(session)
    glacier1d = da.read_nc(glacierpath)

    # for the diagnostic, also add velocity divergence near surface mass balance
    glacier1d = massbalance_diag(glacier1d)

    # rename variables and change units for the plotting
    fmt = dict(
        U='surf_velocity',
        hs='surface',
        hb='bottom',
        zb='bedrock',
        W='width',
    )
    glacier1d = da.Dataset({fmt.pop(nm, nm): glacier1d[nm] for nm in glacier1d.keys()})

    # meters into km
    glacier1d.axes['x'].values *= 1e-3
    glacier1d.axes['x'].units = 'km'
    for nm in ['x_coord','y_coord','width']:
        glacier1d[nm].values *= 1e-3
        glacier1d[nm].units = 'km'

    # meters/seconds into meters/year
    for nm in ['surf_velocity','balance_velocity_obs','balance_velocity_mod3D','smb','runoff']:
        glacier1d[nm].values *= 24*3600*365.25
        glacier1d[nm].units = 'meters/year'

    # group data into various views
    views = [
        { 
            'id': 'elevation',
            'names' : ['bedrock','bottom','surface'],
            'xlabel' : '',
            'ylabel' : 'elevation (m)',
        },
        { 
            'id': 'width',
            'names' : ['width'],
            'xlabel' : '',
            'ylabel' : 'width (km)',
        },
        { 
            'id': 'velocity',
            'names' : ['surf_velocity'],
            # 'names' : ['surf_velocity','balance_velocity_obs','balance_velocity_mod3D'],
            # 'xlabel' : '',
            'xlabel' : 'distance from ice divide(km)',
            'ylabel' : 'velocity (meters/year)',
        },
        # { 
        #     'id': 'mass_balance',
        #     'names' : ['cumulative_smb','ice_flux_surf_obs','ice_flux_bal_mod3D'],
        #     'xlabel' : '',
        #     'ylabel' : 'mass balance (meters^3/second)',
        # },
        # { 
        #     'id': 'smb',
        #     'names' : ['smb','runoff'],
        #     'xlabel' : 'distance from ice divide(km)',
        #     'ylabel' : 'SMB (meters/year)',
        # },
    ]

    # variables to plot
    names = np.unique(list(itertools.chain(*[view['names'] for view in views]))).tolist()
    names +=  ['x_coord','y_coord'] # also pass along coordinates
    print names

    # replace all nan values
    missing_values = -99.99
    for k in glacier1d:
        glacier1d[k][np.isnan(glacier1d[k])] = missing_values

    # for simplicity, organize each line a list of poitns with x, y property
    sources = {}
    for nm in names:
        sources[nm] = {
            'values':[{'x':glacier1d.x[i], 'y':val} for i, val in enumerate(glacier1d[nm].values)],
            'missing_values': missing_values,
        }

    # not used for now
    units = {k:glacier1d[k].units.strip()  if hasattr(glacier1d[k], 'units') else '' for k in names}

    return jsonify(views=views, sources=sources, width=350, height=120)

@app.route('/download/glacier1d.nc')
def download():
    direc, filename = os.path.split(getglacierpath(session))
    return send_from_directory(directory=direc, filename=filename)
