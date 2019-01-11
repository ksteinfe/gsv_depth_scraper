import tempfile, os, time
from PIL import Image
from math import pi,sin,cos,tan,atan2,hypot,floor
from numpy import clip



# given an equalrectangular image of a layer, cuts cubemap tiles at some number of rotations, and appends resulting images to a given zip archive
def cut_tiles_and_package_to_zip(img, layer, panoid, zipobj, fmt, resize_to=False):
    print("{} {}".format(panoid, layer))
    with tempfile.TemporaryDirectory() as pth_tmp:
        tiles = _tiles_from_equirectangular(img) # a nested dict of rots and facs
        for rot, faces in tiles.items():
            for fac, img in faces.items():
                if resize_to: img = img.resize((resize_to,resize_to), Image.ANTIALIAS)
                img.save(os.path.join(pth_tmp,"{}_{}_{}_{}.{}".format(panoid,layer,rot,fac,fmt))) # save img to temp folder
                
        # write images to zip archive
        for fname in os.listdir(pth_tmp):
            zipobj.write(os.path.join(pth_tmp,fname), os.path.join("{}_til".format(layer),fname))
    
    

def _tiles_from_equirectangular(img):
    # we could alter rotations here if desired
    rot00 = _faces_from_equirectangular(img)
    rot30 = _faces_from_equirectangular(_rotate_equirectangular(img, 12)) # rot of 12 = 30deg
    rot60 = _faces_from_equirectangular(_rotate_equirectangular(img, 6)) # rot of 6 = 60deg
    return {'00':rot00, '30':rot30, '60':rot60}


def _faces_from_equirectangular(img_eqrc):
    img_cmap = Image.new("RGB",(img_eqrc.size[0],int(img_eqrc.size[0]*3/4)),"black")
    _convert_back(img_eqrc,img_cmap)
        
    dim = face_size(img_eqrc)
    box = (0,0,dim,dim)
    tile_top = Image.new(img_cmap.mode,(dim,dim),color=None)
    tile_top.paste( img_cmap.crop((dim*2,0,dim*3,dim)), box ) 
    
    tile_bottom = Image.new(img_cmap.mode,(dim,dim),color=None)
    tile_bottom.paste( img_cmap.crop((dim*2,dim*2,dim*3,dim*3)), box ) 
    
    tile_back = Image.new(img_cmap.mode,(dim,dim),color=None)
    tile_back.paste( img_cmap.crop((0,dim,dim,dim*2)), box )     
    
    tile_right = Image.new(img_cmap.mode,(dim,dim),color=None)
    tile_right.paste( img_cmap.crop((dim,dim,dim*2,dim*2)), box ) 
    
    tile_front = Image.new(img_cmap.mode,(dim,dim),color=None)
    tile_front.paste( img_cmap.crop((dim*2,dim,dim*3,dim*2)), box ) 
    
    tile_left = Image.new(img_cmap.mode,(dim,dim),color=None)
    tile_left.paste( img_cmap.crop((dim*3,dim,dim*4,dim*2)), box ) 
        
    return {"top":tile_top,"btm":tile_bottom,"bck":tile_back,"rht":tile_right,"fnt":tile_front,"lft":tile_left}

def face_size(img_eqrc):
    return int(img_eqrc.size[0]/4)
    
# rotates an equirectangular image
# rot is the amount of rotation, given in terms of integer number of divisions of a circle
# rot=12=30deg; rot=8=45deg; rot=6=60deg; rot=4=90deg 
def _rotate_equirectangular(img_src, rot=8):
    img_tar = Image.new(img_src.mode,img_src.size,color=None)
    fmt = img_src.format
    w,h = img_src.size
    div = int(w/8) # amount to rotate
    
    img_tar.paste( img_src.crop((0,0,div,h)), (w-div,0,w,h) ) 
    img_tar.paste( img_src.crop((div,0,w,h)), (0,0,w-div,h) ) 
    return img_tar
    
# adapted from https://gist.github.com/muminoff/25f7a86f28968eb89a4b722e960603fe    
# get x,y,z coords from out image pixels coords
# i,j are pixel coords
# face is face number
# edge is edge length
def _out_img_to_xyz(i,j,face,edge):
    a = 2.0*float(i)/edge
    b = 2.0*float(j)/edge
    if face==0: # back
        (x,y,z) = (-1.0, 1.0-a, 3.0 - b)
    elif face==1: # left
        (x,y,z) = (a-3.0, -1.0, 3.0 - b)
    elif face==2: # front
        (x,y,z) = (1.0, a - 5.0, 3.0 - b)
    elif face==3: # right
        (x,y,z) = (7.0-a, 1.0, 3.0 - b)
    elif face==4: # top
        (x,y,z) = (b-1.0, a -5.0, 1.0)
    elif face==5: # bottom
        (x,y,z) = (5.0-b, a-5.0, -1.0)
    return (x,y,z)

# adapted from https://gist.github.com/muminoff/25f7a86f28968eb89a4b722e960603fe
# convert using an inverse transformation
def _convert_back(imgIn,imgOut):
    inSize = imgIn.size
    outSize = imgOut.size
    inPix = imgIn.load()
    outPix = imgOut.load()
    edge = inSize[0]/4   # the length of each edge in pixels
    for i in range(outSize[0]):
        face = int(i/edge) # 0 - back, 1 - left 2 - front, 3 - right
        if face==2:
            rng = range(0,int(edge*3))
        else:
            rng = range(int(edge), int(edge) * 2)

        for j in rng:
            if j<edge:
                face2 = 4 # top
            elif j>=2*edge:
                face2 = 5 # bottom
            else:
                face2 = face

            (x,y,z) = _out_img_to_xyz(i,j,face2,edge)
            theta = atan2(y,x) # range -pi to pi
            r = hypot(x,y)
            phi = atan2(z,r) # range -pi/2 to pi/2
            # source img coords
            uf = ( 2.0*edge*(theta + pi)/pi )
            vf = ( 2.0*edge * (pi/2 - phi)/pi)
            # Use bilinear interpolation between the four surrounding pixels
            ui = floor(uf)  # coord of pixel to bottom left
            vi = floor(vf)
            u2 = ui+1       # coords of pixel to top right
            v2 = vi+1
            mu = uf-ui      # fraction of way across pixel
            nu = vf-vi
            A = inPix[ui % inSize[0],int(clip(vi,0,inSize[1]-1))]
            B = inPix[u2 % inSize[0],int(clip(vi,0,inSize[1]-1))]
            C = inPix[ui % inSize[0],int(clip(v2,0,inSize[1]-1))]
            D = inPix[u2 % inSize[0],int(clip(v2,0,inSize[1]-1))]
            # interpolate
            (r,g,b) = (
              A[0]*(1-mu)*(1-nu) + B[0]*(mu)*(1-nu) + C[0]*(1-mu)*nu+D[0]*mu*nu,
              A[1]*(1-mu)*(1-nu) + B[1]*(mu)*(1-nu) + C[1]*(1-mu)*nu+D[1]*mu*nu,
              A[2]*(1-mu)*(1-nu) + B[2]*(mu)*(1-nu) + C[2]*(1-mu)*nu+D[2]*mu*nu )

            outPix[i,j] = (int(round(r)),int(round(g)),int(round(b)))

