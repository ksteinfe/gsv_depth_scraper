import datetime, requests, os, json, urllib.request
from io import BytesIO
import google_streetview.api
from PIL import Image

# for signing urls
import hashlib, hmac, base64
from requests.packages.urllib3.util import parse_url

import gsv_depth_scraper.geom

now = datetime.datetime.now()
PANO_URL = 'http://maps.google.com/cbk?output=tile&panoid={panoid}&zoom={z}&x={x}&y={y}&key={key}&' + str(now.microsecond)
STAT_URL = 'https://maps.googleapis.com/maps/api/staticmap?center=Berkeley,CA&zoom=14&size=400x400&key={key}'

GSV_TILEDIM = 512
GSV_PANODIM = 416
GOOG_COPYRIGHT = "Google"

#api_sign_secret = "LonEqRR9GhMC4S8cyJ5E0OvXCpg="
#b64sign = "pLa6oGQjAn17ijaPcx41wRZsfSQ="


def load_panos_and_package_to_zip(pth_wrk, zipobj, fmt, limit=False):
    panoids, pano_imgs = [], []
    pano_fnames = [file for file in os.listdir(pth_wrk) if file.endswith(fmt)]
    dpth_fnames = [file for file in os.listdir(pth_wrk) if file.endswith("json")]
    if limit: pano_fnames = pano_fnames[:limit]
    for pano_fname in pano_fnames:
        panoid = os.path.splitext(pano_fname)[0]
        if "{}.json".format(panoid) not in dpth_fnames:
            print("MISSING JSON FILE\nCould not find {} in working directory {}.\nThis pano will not be archived.".format("{}.json".format(panoid),pth_wrk))
            continue

        zipobj.write(os.path.join(pth_wrk,pano_fname), os.path.join("pano_img",pano_fname)) # write pano image to zip archive
        pano_imgs.append(Image.open(os.path.join(pth_wrk,pano_fname))) # load pano image to memory
        panoids.append(panoid)

    return panoids, pano_imgs

    
def plot_map(mapplot_data, pth_wrk, api_key):
    print("MAP PLOTTING IS A WORK IN PROGRESS")
    return False
    print(mapplot_data)
    stat_url = STAT_URL.format( key=api_key )
    print(stat_url)
    urllib.request.urlretrieve(stat_url, "plot.jpg")
    
    
def panoid_to_img(panoid, api_key, zoom):
    w,h = 2**zoom, 2**(zoom-1)
    img = Image.new("RGB", (w*GSV_PANODIM, h*GSV_PANODIM), "red")

    try:
        for y in range(h):
            for x in range(w):
                url_pano = PANO_URL.format(panoid=panoid, z=zoom, x=x, y=y, key=api_key)
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
            print("Found a panorama with no copyright tag. skipping.")
            continue
        else:
            if not ( meta['copyright'].split()[-1].lower() == GOOG_COPYRIGHT.lower() ):
                print("Found a non-google copyright ({}). skipping {}.".format(meta['copyright'], meta['pano_id']))
                continue

        panoids.add( meta['pano_id'] )
    return list(panoids)

    
# from https://gist.github.com/christ0pher/f2c4748a09ed31cf71a8
# NOT USED
def sign_url(input_url=None, client_id=None, client_secret=None):
  """ Sign a request URL with a Crypto Key.
      Usage:
      from urlsigner import sign_url
      signed_url = sign_url(input_url=my_url,
                            client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET)
      Args:
      input_url - The URL to sign
      client_id - Your Client ID
      client_secret - Your Crypto Key
      Returns:
      The signed request URL
  """

  # Return if any parameters aren't given
  if not input_url or not client_id or not client_secret:
    return None

  # Add the Client ID to the URL
  input_url += "&client=%s" % (client_id)

  url = parse_url(input_url)

  # We only need to sign the path+query part of the string
  url_to_sign = url.path + "?" + url.query

  # Decode the private key into its binary format
  # We need to decode the URL-encoded private key
  decoded_key = base64.urlsafe_b64decode(client_secret)

  # Create a signature using the private key and the URL-encoded
  # string using HMAC SHA1. This signature will be binary.
  signature = hmac.new(decoded_key, url_to_sign.encode(), hashlib.sha1)

  # Encode the binary signature into base64 for use within a URL
  encoded_signature = base64.urlsafe_b64encode(signature.digest())

  original_url = url.scheme + "://" + url.netloc + url.path + "?" + url.query

  # Return signed URL
  return original_url + "&signature=" + encoded_signature.decode()

