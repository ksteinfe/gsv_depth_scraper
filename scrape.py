import configparser, os, argparse, ntpath
import gsv_depth_scraper.main


def main(args):
    print("========\nRunning in '{}' mode.".format(args.mode))
    limit = args.limit
    if limit <0: limit = False

    if args.mode == "scrape" or args.mode == "scrape_and_process":
        name = os.path.splitext(ntpath.basename(args.geojson))[0]
        pth_wrk, pth_zip = gsv_depth_scraper.main._prepare_working_directory(args.dir, name, args.mode == "scrape" or args.mode == "scrape_and_process")
    elif args.mode == "process":
        name = args.name
        pth_wrk, pth_zip = gsv_depth_scraper.main._prepare_working_directory(args.dir, args.name)

    if args.mode == "scrape" or args.mode == "scrape_and_process":
        print("Scraping...\nname: {}\t zoom: {}\t delay: {}\t limit: {}\n========".format(name, args.zoom, args.delay, limit))
        gsv_depth_scraper.main.gjpts_to_panos(args.geojson, args.key, pth_wrk, name, zoom=args.zoom, delay=args.delay, limit=limit)
    if args.mode == "scrape_and_process": print("========")
    if args.mode == "process" or args.mode == "scrape_and_process":
        print("Processing...\nname: {}\n========".format(name))
        gsv_depth_scraper.main.panos_to_package(pth_wrk, pth_zip, name, do_tile=args.do_tile, limit=limit)


if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.read('config.ini')
    if not 'dir' in config['DEFAULT'] or not 'key' in config['DEFAULT']:
        raise Exception("Configuration error. Please create a configuration file as described in README.md")

    if not os.path.isdir(config['DEFAULT']['dir']):
        raise Exception("Working directory defined in configuration file is not a directory: {}".format(config['DEFAULT']['dir']))
    else:
        config['DEFAULT']['dir'] = os.path.abspath(os.path.realpath(os.path.expanduser(config['DEFAULT']['dir'])))

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

    # common parent for defining arguments for 'scrape' and 'both' modes
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('geojson', help="Path to a .geojson file that describes sample locations from which to find nearby Street View panoramas. Note that panorama locations are not identical to sample locations, and that not all sample locations will result in a valid panorama. Geojson should be structured as a FeatureCollection - all coordinates described by contained Features will be sampled. Conforming .geojson data may be created at http://geojson.io/", type=is_file)
    parent_parser.add_argument('-delay', type=int, default=60, help="A delay in seconds between each subsequent call to the undocumented depthmap API. Limits on this undocumented API are not known. For small batches (around 20 panoramas), no delay appears to be required. For large batches, consider a range of 30-60 seconds.")
    parent_parser.add_argument('-zoom', type=int, default=1, help="Zoom level at which to download photographic panoramas. Lower values are smaller images, higher values are larger. Maximum of 3 is recommended.")
    parent_parser.add_argument('-limit', type=int, default=-1, help="Limits the number of sample points processed for debugging purposes. A value of -1 (default) indicates no limit.")

    # create main parser
    parser = argparse.ArgumentParser()

    # create subparsers
    subparsers = parser.add_subparsers(dest='mode', help="The mode in which to run the scraper. Choose 'scrape' to download pano and depth data from Google Street View panoramas nearby a given geojson list of sample locations. After scraping, local data may then be cleaned and cherry-picked. Next, we would choose 'process' to convert this local pano and depth data into a ZIP package of depthmap images and tiles.")
    subparsers.required = True

    parser_scrape = subparsers.add_parser('scrape', parents=[parent_parser], help="Scrape mode. Given a .geojson file containing coordinate locations, finds nearby Google Street View panoramas, and downloads both panoramic images and depth information to a defined working directory. Since this uses a combination of documented and undocumented APIs, scraping is designed to take a long time to avoid getting our IP address banned.")
    parser_both = subparsers.add_parser('scrape_and_process', parents=[parent_parser], help="Performs both scrape and process operations.")

    parser_process = subparsers.add_parser('process', help="Process mode. Given panoramic images and depth information saved to a defined working directory, for each panorama a corresponding depthmap image is created. This pair of depthmap and photographic panorama are then cut into tiles and packaged into a ZIP file.")
    parser_process.add_argument('name', help="The name of the subfolder of the working directory that contains the already-downloaded pano and depth data.")
    parser_process.add_argument('-limit', type=int, default=-1, help="Limits the number of panos processed for debugging purposes. A value of -1 (default) indicates no limit.")
    parser_process.add_argument('-do_tile', action='store_true', default=False)

    args = parser.parse_args()

    # add in configuration variables to arguments
    args.dir = config['DEFAULT']['dir']
    args.key = config['DEFAULT']['key']
    main(args)
