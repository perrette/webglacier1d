webglacier1d
============

This is a python-javascript project to visualize 2-D ice sheet data, draw a glacier outline, and extract relevant, averaged data along the 1-D profile.

[See snapshots here](https://www.pik-potsdam.de/members/perrette/egu2015-webglacier1d/poster-perrette-webtool-egu2015.png)

Dependencies
------------
Can be installed via `pip install <package>` unless otherwise stated. The version number under bracket indicate 
the version with which the app was tested. Earlier or later versions might work as well. For installations requiring more than just pip, [see instructions here](https://github.com/perrette/python-install).

- [icedata (dev)](https://github.com/perrette/icedata) : install last version from github (see dependencies there)
- [cartopy](https://github.com/SciTools/cartopy) [0.11.0]: used for grid projections, [see instructions here](https://github.com/perrette/python-install/blob/master/README.md#cartopy)
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
