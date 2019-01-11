import json, geojson
# GeoJSON wants [longitude, latitude, elevation]

def test_gpts():
    latlngs = [(37.7611365438102, -122.3983484843661), (37.76083695786007, -122.3983250339414), (37.76073990870817, -122.3983174373624), (137.76073990870816, 122.3983174373624), (37.76073990870817, -122.3983174373624)]
    return latlngs_to_gpts(latlngs) 


def lnglats_to_gpts(lnglats): return [geojson.Point((lnglat[0],lnglat[1])) for lnglat in lnglats] 
def latlngs_to_gpts(latlngs): return [geojson.Point((latlng[1],latlng[0])) for latlng in latlngs]
    
def concat_gpts_to_goog_str(gpts):
    return ";".join(["{},{}".format(gpt["coordinates"][1],gpt["coordinates"][0]) for gpt in gpts ])  # GeoJSON stores [lng,lat], Google wants [lat,lng]
    

# create compatible geojson files with http://geojson.io/
# coordinates of all features (LineStrings, Points, etc) in the top-level feature collection will be processed
def load_gpts(pth_fil):
    feat_coll = False 
    with open(pth_fil) as f: feat_coll = geojson.load(f)
    if not feat_coll: 
        print("!!!! Failed to load geometry from file {}".format(pth_fil))
        return False
    
    gpts = []
    for feat in feat_coll.features: gpts.extend(lnglats_to_gpts(list(geojson.utils.coords(feat))))
    return gpts