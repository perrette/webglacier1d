webglacier1d
============

This is a python-javascript project to visualize 2-D ice sheet data, draw a glacier outline, and extract relevant, averaged data along the 1-D profile.

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
numpy
[netCDF4](https://github.com/Unidata/netcdf4-python) (see install help on dimarray github)
[dimarray (dev)](https://github.com/perrette/dimarray) : please install the latest version from github. The pip version will not work.
flask
wtforms
flask-wtf
... anything left out?

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
Any technical suggestions to improve the methods are welcome, for example
mesh generation and so on.

I also welcome any suggestion for scientific collaboration related to this topic.
