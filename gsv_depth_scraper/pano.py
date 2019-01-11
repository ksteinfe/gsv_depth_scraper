import datetime, requests, os, json
from io import BytesIO
import google_streetview.api
from PIL import Image

import gsv_depth_scraper.geom

now = datetime.datetime.now()
URL_STR = 'http://maps.google.com/cbk?output=tile&panoid={panoid}&zoom={z}&x={x}&y={y}&key={key}&' + str(now.microsecond)

GSV_TILEDIM = 512
GSV_PANODIM = 416       
GOOG_COPYRIGHT = "Google"


def load_panos_and_package_to_zip(pth_wrk, zipobj, fmt):
    panoids, pano_imgs = [], []
    pano_fnames = [file for file in os.listdir(pth_wrk) if file.endswith(fmt)]
    dpth_fnames = [file for file in os.listdir(pth_wrk) if file.endswith("json")]
    for pano_fname in pano_fnames:
        panoid = os.path.splitext(pano_fname)[0]
        if "{}.json".format(panoid) not in dpth_fnames:
            print("MISSING JSON FILE\nCould not find {} in working directory {}.\nThis pano will not be archived.".format("{}.json".format(panoid),pth_wrk))
            continue
        
        zipobj.write(os.path.join(pth_wrk,pano_fname), os.path.join("pano_img",pano_fname)) # write pano image to zip archive
        pano_imgs.append(Image.open(os.path.join(pth_wrk,pano_fname))) # load pano image to memory
        panoids.append(panoid)
    
    return panoids, pano_imgs
    
def panoid_to_img(panoid, api_key, zoom):
    w,h = 2**zoom, 2**(zoom-1)
    img = Image.new("RGB", (w*GSV_PANODIM, h*GSV_PANODIM), "red")
    
    try:
        for y in range(h):
            for x in range(w):
                url_pano = URL_STR.format(panoid=panoid, z=zoom, x=x, y=y, key=api_key)
                response = requests.get(url_pano)
                img_tile = Image.open(BytesIO(response.content))
                img.paste(img_tile, (GSV_TILEDIM*x,GSV_TILEDIM*y))
    except:
        print("!!!! FAILED TO DOWNLOAD PANO for {}".format(panoid))
        return False
    
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def gpts_to_panoids(gjpts, api_key):
    locstr = gsv_depth_scraper.geom.concat_gpts_to_goog_str(gjpts)
    apiargs = {
        'location': locstr,
        'key': api_key
    }
    api_list = google_streetview.helpers.api_list(apiargs)
    results = google_streetview.api.results(api_list)
        
    panoids = set()
    for meta in results.metadata:
        if not meta['status'] == "OK":
            print("NO PANORAMA FOUND FOR GIVEN LATLNG. status: {}".format(meta['status']))
            continue
            
        if 'copyright' not in meta:
            print("Found a panorama with no copyright tag. skipping this panorama as it likely doesn't have a depthmap.")
            continue
        else:
            if not ( meta['copyright'].split()[-1].lower() == GOOG_COPYRIGHT.lower() ):
                print("Found a non-google copyright ({}). skipping this panorama as it likely doesn't have a depthmap.".format(meta['copyright']))
                continue
            
        panoids.add( meta['pano_id'] )
    return list(panoids)