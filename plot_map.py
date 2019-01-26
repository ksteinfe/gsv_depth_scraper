import configparser, os, argparse, json
import gsv_depth_scraper.geom


def main(args,fmt="png"):
    print("========\nPlotting map from JSON found in working folder {}".format(args.name))
    pth_wrk = os.path.join(args.dir, args.name)
    dpth_fnames = [file for file in os.listdir(pth_wrk) if file.endswith(".json")]
    pano_fnames = [file for file in os.listdir(pth_wrk) if file.endswith(fmt)]
    
    mapplot_data = {}
    for dpth_fname in dpth_fnames:
        panoid = os.path.splitext(dpth_fname)[0]
        if "{}.{}".format(panoid,fmt) not in pano_fnames:
            print("Could not find {} in working directory. This pano must have been deleted.".format("{}.{}".format(panoid,fmt)))
            continue
            
        dpth_inf = False
        with open(os.path.join(pth_wrk,dpth_fname)) as f: dpth_inf = json.load(f)        
        if not dpth_inf:
            print("trouble loading JSON file {}".format(dpth_fname))
            continue
        mapplot_data[panoid] = {"lat":dpth_inf['Location']['lat'], "lng":dpth_inf['Location']['lng']}
        
    mapplot_geojson = gsv_depth_scraper.geom.locs_to_geojson(mapplot_data)
    
    pth_map = os.path.join(pth_wrk,"__map.html")
    gsv_depth_scraper.geom.plot_map(mapplot_geojson, pth_map, args.mapbox_key, True)
    
    with open(os.path.join(pth_wrk,"__result_locs.geojson"), 'w') as f:
        json.dump(mapplot_geojson, f, separators=(',', ':')) # save results  

if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.read('config.ini')
    if not 'dir' in config['DEFAULT'] or not 'key' in config['DEFAULT']:
        raise Exception("Configuration error. Please create a configuration file as described in README.md")

    if not os.path.isdir(config['DEFAULT']['dir']):
        raise Exception("Working directory defined in configuration file is not a directory: {}".format(config['DEFAULT']['dir']))
    else:
        config['DEFAULT']['dir'] = os.path.abspath(os.path.realpath(os.path.expanduser(config['DEFAULT']['dir'])))
    
    mapbox_key = False
    if 'mapbox_key' in config['DEFAULT'] and len(config['DEFAULT']['mapbox_key']) > 10:
        mapbox_key = config['DEFAULT']['mapbox_key']
    else:
        print("Cannot plot a map without a mapbox_key defined in config.ini")
        exit()
    
    """Checks if a path is an actual directory"""
    def is_dir(pth):
        if not os.path.isdir(pth):
            msg = "{0} is not a directory".format(pth)
            raise argparse.ArgumentTypeError(msg)
        else:
            return os.path.abspath(os.path.realpath(os.path.expanduser(pth)))

    """Checks if a path is an actual file"""
    def is_file(pth):
        if not os.path.isfile(pth):
            msg = "{0} is not a file".format(pth)
            raise argparse.ArgumentTypeError(msg)
        else:
            return os.path.abspath(os.path.realpath(os.path.expanduser(pth)))

    # create main parser
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help="The name of the subfolder of the working directory that contains the already-downloaded pano and depth data.")
    args = parser.parse_args()

    # add in configuration variables to arguments
    args.dir = config['DEFAULT']['dir']
    args.mapbox_key = mapbox_key
    main(args)
