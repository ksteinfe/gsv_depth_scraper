# Google Street View Depth Scraper
A utility for downloading photographic panoramas and related depth data from Google Street View.


## Configuration

### dir
Path to a working directory. Scraped data will be downloaded into a program-created subdirectory in this location. When processing, this same subdirectory will be expected to contain the scraped data.

### key
GSV API key.

### depth_max
Depth values are normalized from a range of 0->depth_max.
TODO: allow for dynamic max depths for a batch

### depth_pow
Normalized depth values are raised to a power of depth_pow (d**depth_pow).
