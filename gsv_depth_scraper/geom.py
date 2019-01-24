import json, geojson, os, math
import geog
import numpy as np
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
    
# given a dict of dicts as "key": {"lat":val, "lng":val}, constructs a geojson featurecollection
# given a list of tuple locations as [lng,lat],[lng,lat], constructs a geojson featurecollection
def locs_to_geojson(locs):
    feacoll = False
    try:
        feas = []
        for key, item in locs.items():
            fea = geojson.Feature(geometry=geojson.Point((float(item['lng']),float(item['lat']))), properties={"panoid": key})
            feas.append(fea)
        feacoll = geojson.FeatureCollection(feas)
    except:
        try:
            feas = []
            for tup in locs:
                fea = geojson.Feature(geometry=geojson.Point((tup[0],tup[1])))
                feas.append(fea)
            feacoll = geojson.FeatureCollection(feas)
        except:
            return False
    feacoll = geojson.FeatureCollection(feas)
    return feacoll   
    
def plot_map(geojson_feas, pth_save, mapbox_key, popup_image=False):    
    html_template = False
    fname = 'map_noimg.html'
    if popup_image: fname = 'map_img.html'
    with open(os.path.join(os.path.dirname(__file__),'..','templates',fname), 'r') as f:
        html_template = f.read()
    if not html_template:
        print("FAILED TO LOAD HTML TEMPLATE:\t{}".format(os.path.join(os.path.dirname(__file__),'..','templates','map.html')))
        return False

    ctr = sum([fea.geometry.coordinates[0] for fea in geojson_feas['features']])/len(geojson_feas['features']), sum([fea.geometry.coordinates[1] for fea in geojson_feas['features']])/len(geojson_feas['features'])
        
    html_template = html_template.replace("{{geojson}}",str(geojson_feas))
    html_template = html_template.replace("{{cntr_lng}}",str(ctr[0]))
    html_template = html_template.replace("{{cntr_lat}}",str(ctr[1]))
    html_template = html_template.replace("{{zoom}}",str(15))
    html_template = html_template.replace("{{key}}",mapbox_key)
    
    with open(pth_save, "w") as f: print(html_template, file=f)
    
    return True
    
    
def rectangular_grid(cntr_latlng, dim_lat=0.01, dim_lng=0.01, cnt_lat=4, cnt_lng=4):
    ctr_lat, ctr_lng = cntr_latlng[0],cntr_latlng[1]
    feas = []
    for x in range(cnt_lng):
        lng = np.interp(x,(0.0,cnt_lng),(ctr_lng-dim_lng/2.0,ctr_lng+dim_lng/2.0))
        for y in range(cnt_lat):
            lat = np.interp(y,(0.0,cnt_lat),(ctr_lat-dim_lat/2.0,ctr_lat+dim_lat/2.0))
            fea = geojson.Feature(geometry=geojson.Point((lng,lat)))
            feas.append(fea)
    feacoll = geojson.FeatureCollection(feas)
    return feacoll
    
def circular_grid(cntr_latlng, dim=50, min_cnt=50):
    lnglats = [(cntr_latlng[1], cntr_latlng[0])]
    d = dim
    n = 0
    while len(lnglats) < min_cnt:
        c = d*2*math.pi
        n_points = int(math.floor(c/dim))
        angles = np.linspace(0, 360, n_points)
        if n%2==0: angles += 360.0/n_points/2.0
        lnglats.extend( geog.propagate(lnglats[0], angles, d) )
        #print("{} \t {}".format(d,n_points))
        d+=dim
        n+=1
    
    print("{} locations plotted to geojson.".format(len(lnglats)))
    feacoll = locs_to_geojson(lnglats)
    return feacoll
    

    
    
    
    
    
    
    