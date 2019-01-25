import json
import gsv_depth_scraper.geom

# create compatible geojson files with http://geojson.io/
def rectangular(ctr):
    dim_x, dim_y = 0.01, 0.01
    cnt_x, cnt_y = 20,25
    feacoll = gsv_depth_scraper.geom.rectangular_grid( ctr, dim_lat=dim_y, dim_lng=dim_x, cnt_lat=cnt_y, cnt_lng=cnt_x )
    with open("out.geojson", 'w') as f: json.dump(feacoll, f, separators=(',', ':'))

def circular(ctr):
    dimension = 50 # in meters
    count = 500 # minimum sample count
    feacoll = gsv_depth_scraper.geom.circular_grid(ctr,dimension,count)
    with open("out.geojson", 'w') as f: json.dump(feacoll, f, separators=(',', ':'))

    
if __name__ == '__main__':
    
    ctr = (30.2049565,-81.6285211) #pickwick park
    ctr = (51.92885,4.46673) # blijdorp
    ctr = (37.7753407,-122.4362981) # alamo square
    ctr = (40.7139572,-73.9514868) # willamsburg
    
    circular(ctr)
    
    
    
