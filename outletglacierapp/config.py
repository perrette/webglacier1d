""" configuration: options and default
"""
import netCDF4 as nc
import os
from models.greenland_data import standard_dataset, boxdecker2011 as bd

curdir = os.path.abspath(os.path.dirname(__name__)) # this directory
# datadir=os.path.join(curdir, os.path.pardir, 'appdata') # data directory above that one
datadir=os.path.join(curdir, 'appdata') # data directory above that one, for some reason no need for pardir...
datadir=os.path.join(curdir, 'outletglacierapp', 'appdata') # data directory above that one, for some reason no need for pardir...

# get variables present in the standard_greenland dataset
ds = nc.Dataset(standard_dataset.NCFILE)
stdvariables = [v for v in ds.variables.keys() \
                if ds.variables[v].dimensions==('time','y1','x1')] # 2D (plus singleton time) variable
ds.close()

bx2013 = bd.load()  

# Construct the list of available dataset
# appears as variable - source

# Available datasets and variables
sources = dict(
    bamber2001 = ('bedrock', 'surface', 'thickness'),
    bamber2013 = ('bedrock', 'surface', 'thickness'),
    morlighem2014 = ('bedrock',), #'surface', 'thickness'),
    joughin2010 = ('velocity_mag', 'velocity_x', 'velocity_y','velocity_angle'),
    rignot_mouginot2012 = ('velocity_mag','velocity_angle'),
    standard_dataset = stdvariables,
    )

# Data sources for variables to extract to glacier
variables = ['bedrock', 'velocity_mag', 'smb']
sources_choices = {v:[ds for ds in sources.keys() if v in sources[ds]] for v in variables}
# sources_choices['bedrock'].append('morlighem2014') # add morlighem to the options
sources_default = dict(
    bedrock = 'bamber2013',
    # surface = 'bamber2013',
    # thickness = 'bamber2013',
    velocity_mag = 'rignot_mouginot2012',
    smb = 'standard_dataset',
)

# Map vizualization
# Combine source and datasets to offer a choice
dataset_choices = []
for ds in sources.keys():
    for nm in sources[ds]:
        dataset_choices.append("{} - {}".format(nm, ds))

dataset_choices = sorted(dataset_choices)
# put standard_dataset at the end (many variables)
dataset_choices = [ds for ds in dataset_choices \
                   if not ds.endswith('standard_dataset')] \
    + [ds for ds in dataset_choices if ds.endswith('standard_dataset')]

dataset_default = 'bedrock - bamber2013'

#
# To select between various regions to display
#
glacier_choices = bx2013.index.tolist()
glacier_choices = sorted(glacier_choices)
glacier_choices.insert(0, "Custom")
glacier_choices.insert(1, "Greenland")

# parameters which define glacier region
glacier_default = 'Greenland'

# zoom around a glacier
zoom = 300e3 

# size of the image that can be transfered - per side - (total pixels = maxpixels**2)
maxpixels = 250

#Flow line options
dx = 1 # space between flowline elements
maxdist = 200 # max distance (km)
# resample = 50

# mesh glacier
mesh_dx = 10*1e3 # m
mesh_ny = 10 # number of points along a cross-section
