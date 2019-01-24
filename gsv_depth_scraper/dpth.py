import os, requests, base64, zlib, math, tempfile, json, configparser
import numpy as np
from PIL import Image

#POW = 0.4
URL_STR = 'http://maps.google.com/cbk?output=json&cb_client=maps_sv&v=4&dm=1&pm=1&ph=1&hl=en&panoid={}'



def load_dpths_and_package_to_zip(name, panoids, pth_dpth, zipobj, pth_zip):
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not 'depth_max' in config['DEFAULT']: 
        raise Exception("Configuration error. Did not find depth_max defined in config.ini. Please create a configuration file as described in README.md")
    if not 'depth_pow' in config['DEFAULT']: 
        raise Exception("Configuration error. Did not find depth_pow defined in config.ini. Please create a configuration file as described in README.md")        

    max_depth_config = config.getfloat('DEFAULT','depth_max')
    pow_config = config.getfloat('DEFAULT','depth_pow')
    
    dpth_imgs = []
    metadata = {}
    max_depth_found = -2
    # create dpth images and save to temp
    with tempfile.TemporaryDirectory() as pth_tmp:
        for panoid in panoids:
            # get depth information
            dpth_resp = False 
            with open(os.path.join(pth_dpth,'{}.json'.format(panoid))) as f: 
                dpth_resp = json.load(f) # read dpth_resp from file
                zipobj.write(os.path.join(pth_dpth,'{}.json'.format(panoid)), os.path.join("json_rsp",'{}.json'.format(panoid))) # write dpth_resp to zip archive
            if not dpth_resp: raise Exception("THIS SHOULDN'T HAPPEN!\nCould not parse depth info file:{}".format(panoid))
            
            metadata[panoid], dpth_inf = process_depth_resp(panoid, dpth_resp) # decodes stored depth information and extracts useful metadata
            
            dpth_img = depthinfo_to_image(dpth_inf, max_depth_config, pow_config, panoid) # create dpth image
            dpth_img.save(os.path.join(pth_tmp,"{}.png".format(panoid))) # save dpth_img to temp folder
            dpth_imgs.append(dpth_img)
            
            if max(dpth_inf['depth_map']) > max_depth_found: max_depth_found = max(dpth_inf['depth_map'])

        # write dpth images to zip archive    
        for dpth_fname in os.listdir(pth_tmp):
            zipobj.write(os.path.join(pth_tmp,dpth_fname), os.path.join("dpth_img",dpth_fname))
                
    print("depthmap data processing complete. max depth found was {}".format(max_depth_found))
    if max_depth_found >= max_depth_config:
        print("!!!! MAXIMUM DEPTH EXCEEDED: expect to find some error-colored pixels in this batch of depthmaps.")
    return metadata, dpth_imgs

    
def process_depth_resp(panoid, dpth_resp):
        
    try:
        raw_depth_map = dpth_resp['model']['depth_map'] # get the base64 string of the depth map
        dm_data = decode_json(raw_depth_map) # open it and decode
    except:
        print("Failed to decode json depth_map")
        return False
    
    header = parse_header(dm_data)
    #print(header)
    
    planes, indices = parse_planes(header, dm_data)
    #print("{} planes and {} indices".format(len(planes), len(indices)))
    
    depth_map = compute_depthmap(header, indices, planes)
    #print(depth_map)
    #print("min: {}, max: {}".format(min(depth_map), max(depth_map)))
            
    dpth_inf = {}
    dpth_inf["depth_map"] = depth_map.tolist()
    dpth_inf["idx_map"] = indices
    dpth_inf["planes"] = planes
    dpth_inf["width"] = header["width"]
    dpth_inf["height"] = header["height"]
        
        
    metadata = {}
    metadata['max_depth'] = max(dpth_inf['depth_map'])
    metadata['number_of_planes'] = len(dpth_inf['planes'])  
    metadata['lat'] = dpth_resp['Location']['lat']
    metadata['lng'] = dpth_resp['Location']['lng']
    try:
        metadata['image_date'] = dpth_resp['Data']['image_date']
        metadata['imagery_type'] = dpth_resp['Data']['imagery_type']
    except:
        print("BADLY FORMED RESPONSE: METADATA INCOMPLETE for {}".format(panoid))
        metadata['image_date'] = False
        metadata['imagery_type'] = False      
        
    return metadata, dpth_inf  

def panoid_to_depthinfo(panoid):
    #URL of the json file of a GSV depth map
    #url_depthmap='http://maps.google.com/cbk?output=json&cb_client=maps_sv&v=4&dm=1&pm=1&ph=1&hl=en&panoid=lcptgwtxfJ6DccSzyWp0zA'
    url_depthmap = URL_STR.format(panoid)
    
    r = requests.get(url_depthmap) # getting the json file
    json_data = r.json()
    try:
        raw_depth_map = json_data['model']['depth_map'] # get the base64 string of the depth map
        dm_data = decode_json(raw_depth_map) # open it and decode (but don't store)
        
        size_img = (int(json_data['Data']['image_width']), int(json_data['Data']['image_height']))
        size_til = (int(json_data['Data']['tile_width']), int(json_data['Data']['tile_height']))
    except:
        print("The returned json could not be decoded")
        print(url_depthmap)
        print("status code: {}".format(r.status_code))
        return False, False, False
    
    return json_data, size_img, size_til
    '''
    metadata = {}
    metadata['lat'] = json_data['Location']['lat']
    metadata['lng'] = json_data['Location']['lng']
    try:
        metadata['image_date'] = json_data['Data']['image_date']
        metadata['imagery_type'] = json_data['Data']['imagery_type']
    except:
        print("BADLY FORMED RESPONSE: METADATA INCOMPLETE for {}".format(panoid))
        metadata['image_date'] = False
        metadata['imagery_type'] = False
        
    return {
        "metadata": metadata,
        "raw_response": json_data
    }
    '''

def decode_json(raw_depth_map):

    # fix the 'incorrect padding' error. The length of the string needs to be divisible by 4.
    raw_depth_map += "=" * ((4 - len(raw_depth_map) % 4) % 4)
    # convert the URL safe format to regular format.
    raw_depth_map = raw_depth_map.replace('-','+').replace('_','/')

    compressed_depth_map_data = base64.b64decode(raw_depth_map) # decode the raw_depth_map
    decompressed_depth_map_data = zlib.decompress(compressed_depth_map_data) #decompress the data
    #print(decompressed_depth_map_data)
    #print( "typ: {}".format(type(decompressed_depth_map_data)) )
    #print( "len: {}".format(len(decompressed_depth_map_data)) )
    
    #chars_depth_map_data = [chr(byt) for byt in decompressed_depth_map_data]
    #print(chars_depth_map_data[:20])

    dm_data = np.fromstring(decompressed_depth_map_data, dtype=np.uint8)
    #print(dm_data[:100])
    #print("1={}".format(dm_data[120000]))
    #print("4={}".format(dm_data[40000]))
    
    """
    dm_data16 = np.fromstring(decompressed_depth_map_data, dtype=np.uint16)
    print(dm_data16[:10])
    """
    return dm_data
    
def parse_header(data):
    return {
        "header_size" : get_uint8(data,0),
        "number_of_planes" : get_uint8(data,1),
        "width": get_uint16(data,3),
        "height": get_uint16(data,5),
        "offset": get_uint8(data,7),
    }
   
def parse_planes(header, data):    
    indices = []
    for i in range(header['width']*header['height']):
        indices.append( get_uint8(data,header['offset']+i) )
    
    #print("found {} indices".format(len(indices)))
    #print("2={}".format(indices[90000]))
    #print("3={}".format(indices[39300]))

    planes = []
    for i in range(header['number_of_planes']):
        byte_offset = header['offset'] + header['width']*header['height'] + i*4*4
        n = [ get_float32(data, byte_offset + 0), get_float32(data, byte_offset + 4), get_float32(data, byte_offset + 8) ]
        d = get_float32(data, byte_offset + 12)
        planes.append( {'n':n, 'd':d } )
    
    #print("found {} planes".format(len(planes)))
    #print("2.91={}".format(planes[1]))
    
    return planes, indices
    
def compute_depthmap(header, indices, planes):
    w, h = header['width'], header['height']
    depth_map = np.full((w*h), None)
    
    sin_theta = [ math.sin(  (h - y - 0.5) / h * math.pi  ) for y in range(h)]
    cos_theta = [ math.cos(  (h - y - 0.5) / h * math.pi  ) for y in range(h)]
    sin_phi = [ math.sin(  (w - x - 0.5) / w * 2 * math.pi + math.pi/2  ) for x in range(w)]
    cos_phi = [ math.cos(  (w - x - 0.5) / w * 2 * math.pi + math.pi/2  ) for x in range(w)]
    
    for y in range(h):
        for x in range(w):
            idx = indices[y*w + x]
            
            v0 = sin_theta[y] * cos_phi[x]
            v1 = sin_theta[y] * sin_phi[x]
            v2 = cos_theta[y]
            
            if idx>0:
                plane = planes[idx]
                t = abs( plane['d'] / (v0*plane['n'][0] + v1*plane['n'][1] + v2*plane['n'][2]) );
                depth_map[y*w + (w-x-1)] = t;
            else:
                #print(y*w + (w-x-1))
                depth_map[y*w + (w-x-1)] = 9999999999999999999.0
                depth_map[y*w + (w-x-1)] = -1
    
    return depth_map

def depthinfo_to_image(depthinfo, max_d, pow, panoid=None, clr_nohit=(255,255,255,0), clr_error=(255,255,255,255) ):
    w, h = depthinfo['width'], depthinfo['height']
    if max(depthinfo['depth_map']) > max_d:
        print("MAXIMUM DEPTH EXCEEDED. {} is greater than {} for panoid {}".format(max(depthinfo['depth_map']),max_d, panoid))
    
    
    # RGBA? TODO
    img = Image.new( "RGBA", (w,h), clr_error )
    pxls = img.load( )
    
    for y in range(h):
        for x in range(w):
            d = depthinfo['depth_map'][y*w + x]
            if d < 0: pxls[x,y] = clr_nohit
            elif d > max_d:
                pass # this pixel will show the error color that the image was initialized with
            else:
                c = int( (d/max_d)**(pow) * 255)
                pxls[x,y] = (c,c,c)
    
    return img
    
def get_uint8(data, offset): return int(data[offset])
def get_uint16(data, offset): return int(np.frombuffer(data, dtype='<i2', count=1, offset=offset)[0])
def get_float32(data, offset): return float(np.frombuffer(data, dtype='<f', count=1, offset=offset)[0])

