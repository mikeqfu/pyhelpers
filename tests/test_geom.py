# geom.py

import numpy as np

from pyhelpers.geom import osgb36_to_wgs84

xy = np.array((530034, 180381))  # London
easting, northing = xy
lonlat = osgb36_to_wgs84(easting, northing)  # osgb36_to_wgs84(xy[0], xy[1])
print(lonlat)

# To convert an array of OSGB36 coordinates
xy_array = np.array([(530034, 180381),   # London
                     (406689, 286822),   # Birmingham
                     (383819, 398052),   # Manchester
                     (582044, 152953)])  # Leeds

eastings, northings = xy_array.T
lonlat_array = np.array(osgb36_to_wgs84(eastings, northings))
print(lonlat_array.T)
