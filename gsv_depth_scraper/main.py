import requests, os, shutil, time, json, zipfile
from numpy.random import random_sample
import gsv_depth_scraper.pano, gsv_depth_scraper.dpth, gsv_depth_scraper.xform, gsv_depth_scraper.geom


# --------------------
# "scrape" mode
# --------------------
def gjpts_to_panos(pth_geo, api_key, pth_wrk, name, zoom=3, fmt="png", delay=False, limit=False, mapbox_key=False):
    print("loading coords from geojson: {}".format(pth_geo))
    gpts = gsv_depth_scraper.geom.load_gpts(pth_geo)
    if limit:
        print("limiting loaded coords from {} to {}".format(len(gpts),limit))
        gpts = gpts[:limit]

    print("getting panoids for {} sample locations".format(len(gpts)))
    panoids = gsv_depth_scraper.pano.gpts_to_panoids(gpts, api_key) # panoids are unique
    print("parsed {} sample locations and found {} unique panoids".format(len(gpts),len(panoids)))
    
    mapplot_data = {}
    for n, panoid in enumerate(panoids):
        dpth_inf, size_img, size_til = gsv_depth_scraper.dpth.panoid_to_depthinfo(panoid)
        pano_img = gsv_depth_scraper.pano.panoid_to_img(panoid, api_key, zoom, size_img)
        if not pano_img: continue
        
        if pano_img and dpth_inf:
            #print("==== {} of {} \t{}\t{} planes\tmax_depth: {}".format(n, len(panoids), panoid, len(dpth_inf['planes']),max(dpth_inf['depth_map'])))
            print("==== {} of {} \t{}".format((n+1), len(panoids), panoid))
            pano_img.save(os.path.join(pth_wrk,"{}.{}".format(panoid,fmt))) # save pano
            with open(os.path.join(pth_wrk,'{}.json'.format(panoid)), 'w') as f:
                json.dump(dpth_inf, f, separators=(',', ':')) # save depth data
                
            #print(dpth_inf)
            mapplot_data[panoid] = {"lat":dpth_inf['Location']['lat'], "lng":dpth_inf['Location']['lng']}
        else:
            print("!!!! FAILED\t{}".format(panoid))
        if delay:
            jitter = ((random_sample()-0.5)*2) * delay * 0.3 # +/- 30% of delay
            print("... pausing for {0:.2f}s".format(delay + jitter))
            time.sleep(delay + jitter)

    mapplot_geojson = gsv_depth_scraper.geom.locs_to_geojson(mapplot_data)
    if mapbox_key:
        gsv_depth_scraper.geom.plot_map(mapplot_geojson, pth_wrk, mapbox_key)
    
    with open(os.path.join(pth_wrk,"_result_locs.geojson"), 'w') as f:
        json.dump(mapplot_geojson, f, separators=(',', ':')) # save results  
    
    return True

# --------------------
# "process" mode
# --------------------
def panos_to_package(pth_wrk, pth_zip, name, do_tile=False, fmt="png", limit=False):

    # create ZIP archive object
    zipobj_imgs = zipfile.ZipFile(os.path.join(pth_zip,"{}_imgs.zip".format(name)), 'w', zipfile.ZIP_DEFLATED)

    print("loading panos from working directory and archiving: {}".format(pth_wrk))
    panoids, pano_imgs = gsv_depth_scraper.pano.load_panos_and_package_to_zip(pth_wrk, zipobj_imgs, fmt, limit)
    pair_count = len(panoids)

    print("creating depth images from depthmap data and archiving")
    metadata, dpth_imgs = gsv_depth_scraper.dpth.load_dpths_and_package_to_zip(name, panoids, pth_wrk, zipobj_imgs, pth_zip)

    # close ZIP archive object
    zipobj_imgs.close()
    print("full image archive is complete: {}".format(os.path.join(pth_zip,"{}_imgs.zip".format(name))))

    if do_tile:
        print("cutting tiles for {} depthpanos".format(pair_count))

        # create ZIP archive object
        zipobj_tils = zipfile.ZipFile(os.path.join(pth_zip,"{}_tils.zip".format(name)), 'w', zipfile.ZIP_DEFLATED)

        for n, (panoid, pano_img, dpth_img) in enumerate(zip(panoids, pano_imgs, dpth_imgs)):
            #panoid, pano_img, dpth_img = item[0], item[1]['pano'], item[1]['dpth']
            tic = time.clock()
            # gsv_depth_scraper.xform.cut_tiles_and_package_to_zip(dpth_img, "dpth", panoid, zipobj, fmt, gsv_depth_scraper.xform.face_size(pano_img))
            gsv_depth_scraper.xform.cut_tiles_and_package_to_zip(dpth_img, "dpth", panoid, zipobj_tils, fmt)
            gsv_depth_scraper.xform.cut_tiles_and_package_to_zip(pano_img, "pano", panoid, zipobj_tils, fmt)
            toc = time.clock()
            dur = int(toc-tic)
            print("cut tiles for {} ({}/{}) took {}s. at this rate, {}s ({:.2f}m) to go.".format(panoid, n+1, pair_count, dur, (pair_count-(n+1))*dur, ((pair_count-(n+1))*dur)/60.0 ))

        # close ZIP archive object
        zipobj_tils.close()

    print("packaged {} depthpanos to {} from {}".format(pair_count, pth_zip, pth_wrk))
    if not do_tile: print("TILES WERE NOT CUT. Consider using the -do_tile argument?")


def _prepare_working_directory(dir, name, delete_existing=False):
    pth_dest = os.path.join(dir, name)
    #pth_zip = os.path.join(dir,"{}".format(name))
    pth_zip = dir

    if delete_existing:
        if not os.path.isdir(pth_dest): os.mkdir(pth_dest)
        else:
            for f in os.listdir(pth_dest):
                fpth = os.path.join(pth_dest, f)
                try:
                    if os.path.isfile(fpth): os.unlink(fpth)
                    elif os.path.isdir(fpth): shutil.rmtree(fpth)
                except Exception as e:
                    print(e)
                    raise Exception("Contents of the specified working directory could not be deleted in preparation for the scrape. Are they in use?")
    else:
        if not os.path.isdir(pth_dest):
            raise Exception("The working directory does not contain existing data by this name.")

    return pth_dest, pth_zip
