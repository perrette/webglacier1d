webglacier1d
============

This is a python-javascript project to visualize 2-D ice sheet data, draw a glacier outline, and extract relevant, averaged data along the 1-D profile.

[See snapshots here](https://www.pik-potsdam.de/members/perrette/egu2015-webglacier1d/poster-perrette-webtool-egu2015.png)

Datasets
--------
Not provided here ! You need to get it yourself...

- [Present-day Greenland](http://websrv.cs.umt.edu/isis/index.php/Present_Day_Greenland): [Greenland_5km_v1.1.nc](http://websrv.cs.umt.edu/isis/images/a/a5/Greenland_5km_v1.1.nc)
- [Bamber et al (2013) dataset](http://www.the-cryosphere.net/7/499/2013/tc-7-499-2013.html) : Available upon request to the authors
- [Rignot and Mouginot (2012) dataset for Greenland](http://onlinelibrary.wiley.com/doi/10.1029/2012GL051634) : Available upon request to the authors
- [Morlighem et al (2013)](http://dx.doi.org/10.5067/5XKQD5Y5V3VN) : [more info here](http://sites.uci.edu/morlighem/dataproducts/mass-conservation-dataset/)
    - Note: for ease of use, the Morlighem et al dataset is currently read-in with inverted y-coordinate. You need to transform it first before reading in the program.

Dependencies
------------
Can be installed via `pip install <package>` unless otherwise stated. The version number under bracket indicate 
the version with which the app was tested. Earlier or later versions might work as well.

- numpy [1.9.2]
- [netCDF4](https://github.com/Unidata/netcdf4-python) [1.1.7]: see install help on dimarray github
- [dimarray (dev)](https://github.com/perrette/dimarray) [0.1.9.dev-852f76e]: please install the latest version from github. The pip version will not work 
- [cartopy](https://github.com/SciTools/cartopy) [0.11.0]: [install instructions](http://scitools.org.uk/cartopy/docs/latest/installing.html#installing) for projections - it has many dependencies and is a bit cumbersome to install. It is used by `dimarray` under the hood.
    - Install proj.4 : `sudo apt-get install libproj-dev libgdal-dev python-gdal libgeos-dev`
    - Install PIL module : `pip install Pillow`
- pandas [0.15.2] : used for loading pre-formatted [Box and Decker (2011)](http://bprc.osu.edu/~jbox/pubs/Box_and_Decker_2011_Annals.pdf) data where coordinates for major glaciers are provided.

Web framework:
- flask 
- wtforms
- flask-wtf

...anything left out?

Install
-------
No install, but need to fetch the data. 
See `required_files.txt` 
These files are assumed to be located in $HOME/data (unix system...)
You can change this default location there: `outletglacierapp/models/greenland_data/config.py`

Then, just run the server:

    python runserver.py

And open the indicated link in your browser (it is often: http://127.0.0.1:5000/ or localhost:5000). 
Best is Google Chrome, which was used for development.
Note this will run locally on your machine, so you should not need internet.

Feedback
--------
...is welcome! Note the point is not really to make an app accessible 
on any possible device, but rather to make a useful tool for research. 
Any technical suggestions to improve the methods are welcome. 
Please see the current [list of issues](https://github.com/perrette/webglacier1d/issues), 
which is a good platform for discussion.

I also welcome any suggestion for scientific collaboration related to this topic.
