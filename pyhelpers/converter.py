""" Converter """

import subprocess

import pyproj


# Convert british national grid (OSBG36) to latitude and longitude (WGS84)
def osgb36_to_wgs84(easting, northing):
    osgb36 = pyproj.Proj(init='EPSG:27700')
    wgs84 = pyproj.Proj(init='EPSG:4326')
    longitude, latitude = pyproj.transform(osgb36, wgs84, easting, northing)
    return longitude, latitude


# Convert latitude and longitude (WGS84) to british national grid (OSBG36)
def wgs84_to_osgb36(longitude, latitude):
    wgs84 = pyproj.Proj(init='EPSG:4326')
    osgb36 = pyproj.Proj(init='EPSG:27700')
    easting, northing = pyproj.transform(wgs84, osgb36, longitude, latitude)
    return easting, northing


# Convert a .svg file to, and save locally, a .emf file
def svg_to_emf(path_to_svg, path_to_emf):
    print("Converting \".svg\" to \".emf\" ... ", end="")
    try:
        subprocess.call(["C:\\Program Files\\Inkscape\\inkscape.exe", '-z', path_to_svg, '-M', path_to_emf])
        print("Done.")
    except Exception as e:
        print("Failed. {}".format(e))
