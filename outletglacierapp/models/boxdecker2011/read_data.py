import pandas as pd
import numpy as np
from os.path import dirname, abspath, exists

#datadir = ''
#datadir = '../box_decker_2011/'
#datadir = '/media/Data/Documents/Talks and posters/2013/EGU2013/GreenlandIceSheet/box_decker_2011/'

datadir = dirname(abspath(__file__))+'/'

def table1():
    """ read table 1 from Box and Decker: Greenland marine-terminating glacier area changes
    """
    data =  pd.DataFrame.from_csv(datadir+'table1.txt',sep=' ')

    # format indices
    inds = []
    for ind in data.index:
        ind = str(ind).replace('_',' ')
        if ind[0] == '(':
            ind = ind[1:-1] # remove parentheses
        ind = ind.replace('Nunatakassaap Sermia','Nunatakassaap Sermia (Alison)')
        inds.append(ind)
    data.index = inds
    return data.sort()

def table2():
    """ read table 1 from Box and Decker: Greenland marine-terminating glacier area changes
    """
    data =  pd.DataFrame.from_csv(datadir+'table2.txt',sep=' ')

    # format indices
    inds = []
    for ind in data.index:
        ind = str(ind).replace('_',' ')
        ind = ind.replace('Sermeq Kujatdleq (Jakobshavn)','Sermeq Kujatdleq (Jakobshavn Isbrae)')
        ind = ind.replace('Sermeq Avannarleq','Sermeq Avannarleq Ilulissat')
        ind = ind.replace('Zachariae','Zachariae Isstrom')
        inds.append(ind)
    #inds = [str(ind).replace('_',' ') for ind in data.index]
    data.index = inds
    return data.sort()

def join(tab1, tab2):
    data = tab1.join(tab2, rsuffix='_tab2', how='outer')
    del data['Region_tab2']

    # Now take care of Upernavik glacier which was taken at different years (indicated with A-E in tab2)
    ix = 'Upernavik'
    ixs = [ix+' '+l for l in ['A','B','C','D','E']]

    for k in data.columns:
        # fill in the region info
        for ix2 in ixs:
            if type(data.ix[ix2][k]) is not str and np.isnan(data.ix[ix2][k]):
                #print "Replace",ix2,k,"with",data.ix[ix,k]
                data.ix[ix2,k] = data.ix[ix,k]

        # provide average data for Upernavik
        if type(data.ix[ix][k]) is not str and np.isnan(data.ix[ix][k]):
            if type(data.ix[ixs[0],k]) is str:
                pass
            else:
                data.ix[ix,k] = data.ix[ixs,k].mean()

    # Give some standard names
    inds = []
    for ind in data.index:
        ind = ind.replace('Sermeq Kujatdleq (Jakobshavn Isbrae)','Jakobshavn Isbrae')
        inds.append(ind)
    data.index = inds

    # Just drop the A, ..., E for now
    data = data.reindex([ind for ind in data.index if ind not in ixs])
        
    return data

def load():
    """ Load data...
    """
    hdfname = datadir+'boxdecker2011.hdf5'
    if exists(hdfname):
        #data = pd.DataFrame.load(hdfname) # does not work in 0.13.0 due to some new bug
        data = pd.DataFrame().load(hdfname)
        return data

    tab1 = table1()
    tab2 = table2()
    data = join(tab1, tab2)
    data.save(hdfname)
    #print tab1
    #print tab2.ix[:,:5]
    #print data.ix[-9:-1,5:-1]
    return data

def polar_stere(lon_w, lon_e, lat_s, lat_n, **kwargs):
    '''Returns a Basemap object (NPS/SPS) focused in a region.

    lon_w, lon_e, lat_s, lat_n -- Graphic limits in geographical coordinates.
                                  W and S directions are negative.
    **kwargs -- Aditional arguments for Basemap object.

    http://code.activestate.com/recipes/578379-plotting-maps-with-polar-stereographic-projection-/
    '''
    from mpl_toolkits.basemap import Basemap
    lon_0 = lon_w + (lon_e - lon_w) / 2.
    ref = lat_s if abs(lat_s) > abs(lat_n) else lat_n
    lat_0 = math.copysign(90., ref)
    proj = 'npstere' if lat_0 > 0 else 'spstere'
    prj = Basemap(projection=proj, lon_0=lon_0, lat_0=lat_0,
                          boundinglat=0, resolution='c')
    #prj = pyproj.Proj(proj='stere', lon_0=lon_0, lat_0=lat_0)
    lons = [lon_w, lon_e, lon_w, lon_e, lon_0, lon_0]
    lats = [lat_s, lat_s, lat_n, lat_n, lat_s, lat_n]
    x, y = prj(lons, lats)
    ll_lon, ll_lat = prj(min(x), min(y), inverse=True)
    ur_lon, ur_lat = prj(max(x), max(y), inverse=True)
    return Basemap(projection='stere', lat_0=lat_0, lon_0=lon_0,
                           llcrnrlon=ll_lon, llcrnrlat=ll_lat,
                           urcrnrlon=ur_lon, urcrnrlat=ur_lat, **kwargs)

def main():

    bd2011 = load()

    lon_0 = -43.
    #lon_0 = 0.
    lat_0 = 74.
    #projection = 'cyl'
    projection = 'geos'
    projection = 'ortho'
    #lon_w, lon_e, lat_s, lat_n = -71, -10, 58, 85
    lon_w, lon_e, lat_s, lat_n = -60, -20, 58, 85
    #corners = dict(llcrnrlon = lon_w, urcrnrlon = lon_e, llcrnrlat = lat_s, urcrnrlat = lat_n) # domain
    #m = Basemap(lon_0=lon_0, lat_0=lat_0, **corners) # set-up map
    #m = Basemap(projection=projection,lon_0=lon_0, lat_0=lat_0, height=50000, width=50000) # set-up map
    #m = Basemap(projection=projection,lon_0=lon_0, lat_0=lat_0) # set-up map


    if 'm' not in locals():
        m = polar_stere(lon_w, lon_e, lat_s, lat_n)
    plt.clf()
    m.etopo()
    #cm.jet.N = 255

    #variable = 'Width_km'
    vcolor = 'Area_change_rate(km2/a)'
    vsize = 'Width_km'
    maxc = bd2011[vcolor].max()
    minc = bd2011[vcolor].min()

    # min-max values of size variable
    maxw = bd2011[vsize].max()
    minw = bd2011[vsize].min()
    def get_col(w):
        x = (w - minw)/(maxw - minw)
        return cm.jet(x)

    for nm in bd2011.index: # loop over glaciers
        gl = bd2011.ix[nm]
        lon = -gl['Longitude_W']
        lat = gl['Latitude_N']
        x, y = m(lon, lat)

        c = gl[vcolor] # variable which  determines the color
        w = gl[vsize]# variable which  determines the size
        if 0: # linear between min and max
            smin = 20 # min size
            smax = 100 # max size
            s = smin + (w - minw)/(maxw - minw)*smax 
        else:
            smin = 20 # min size
            factor = smin/minw # factor to convert width into size
            s = w*factor
        m.scatter(x, y, c=c, s=s, cmap=cm.jet_r, vmin=minc, vmax=maxc)
        #m.scatter(x, y, color=get_col(w))

    h = m.colorbar()
    h.set_label('Area change rate (km$^2$a$^{-1}$)')

    m.drawcoastlines()
    m.drawparallels(np.arange(-90.,120.,10.),labels=[1,0,0,0]) # draw parallels
    m.drawmeridians(np.arange(-420.,420.,10.),labels=[0,0,0,1]) # draw meridians


    # ADD NAMES ON THE GLACIERS
    #names = ['Helheim']
    names = []
    names = bd2011.sort('Width_km', ascending=0).index[:15] # just the first 15 largest glaciers
    #names = bd2011.index
    #names = ['Humboldt', 'Jakobshavn Isbrae','Petermann', 'Helheim', 'Kangerdlugssuaq','Nioghalvfjerdsbrae/79','Storstrommen']
    for nm in names:
        gl = bd2011.ix[nm]
        lon = -gl['Longitude_W']
        lat = gl['Latitude_N']
        xy = m(lon, lat)
        #xytext = m(lon+2, lat)
        #annotate(nm,xy,xytext=xytext)
        annotate(nm,xy)

    plt.show()
    globals().update(locals()) # pass all variables to the main environment dirty, useful for interactive programming

if __name__ == '__main__':
    main()
