import json
import gsv_depth_scraper.geom

# create compatible geojson files with http://geojson.io/
def main():
    ctr = (30.2049565,-81.6285211)
    ctr = (51.92885,4.46673)
    dim_x, dim_y = 0.01, 0.01
    cnt_x, cnt_y = 20,25
    geojson = gsv_depth_scraper.geom.grid( ctr, dim_lat=dim_y, dim_lng=dim_x, cnt_lat=cnt_y, cnt_lng=cnt_x )
    
    with open("out.geojson", 'w') as f: json.dump(geojson, f, separators=(',', ':'))
        
if __name__ == '__main__':
    main()
    
    
