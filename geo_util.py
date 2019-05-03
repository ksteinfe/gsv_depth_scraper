import json, argparse
import gsv_depth_scraper.geom

# create compatible geojson files with http://geojson.io/
def rectangular(ctr):
    dim_x, dim_y = 0.01, 0.01
    cnt_x, cnt_y = 20,25
    feacoll = gsv_depth_scraper.geom.rectangular_grid( ctr, dim_lat=dim_y, dim_lng=dim_x, cnt_lat=cnt_y, cnt_lng=cnt_x )
    with open("out.geojson", 'w') as f: json.dump(feacoll, f, separators=(',', ':'))

def circular(ctr, count=500):
    dimension = 50 # in meters
    feacoll = gsv_depth_scraper.geom.circular_grid(ctr,dimension,count)
    with open("out.geojson", 'w') as f: json.dump(feacoll, f, separators=(',', ':'))


if __name__ == '__main__':
    # create args parser
    parser = argparse.ArgumentParser()
    parser.add_argument('lat', type=float, help="Latitude of center point.")
    parser.add_argument('lng', type=float, help="Longitude of center point.")
    parser.add_argument('count', type=int, help="Minimum number of samples to take.")

    args = parser.parse_args()
    print(args)

    ctr = (30.2049565,-81.6285211) #pickwick park
    ctr = (51.92885,4.46673) # blijdorp
    ctr = (37.7753407,-122.4362981) # alamo square
    ctr = (40.7139572,-73.9514868) # willamsburg
    ctr = (29.6479851,-82.3378642) # eastcampus gainesville
    ctr = (args.lat, args.lng)

    circular(ctr, args.count)
