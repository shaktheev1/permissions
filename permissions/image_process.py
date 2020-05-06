import os, sys
import PIL
from PIL import Image
from fnmatch import fnmatch
import os.path
from os import path

def i_process(isbn, media_path):
    images = 'resized'
    basewidth = 450
    #root=input("Enter folder name:")
    root=media_path+"/documents/"+isbn
    if path.exists(root):
        for infile in os.listdir(root):
            if infile.endswith('.png') or infile.endswith('.tif') or infile.endswith('.jpg') or infile.endswith('.eps')  or infile.endswith('.gif'):
                im = Image.open(os.path.join(root,infile))
                wpercent = (basewidth / float(im.size[0]))
                hsize = int((float(im.size[1]) * float(wpercent)))
                im = im.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                if not(os.path.exists(os.path.join(root,images))):
                    os.mkdir(os.path.join(root,images))
                outfile = os.path.join(root,images,os.path.splitext(infile)[0]+".jpg")
                out = im.convert("RGB")
                out.save(outfile, "JPEG")
            # do something
        # return something
        return isbn
    else:
        return "Images are not available for this ISBN: {} inside documents folder. Please make sure to run PROCESS IMAGES script.".format(isbn)

if __name__ == '__main__':
    try:
        arg = sys.argv[1]
    except IndexError:
        arg = None
    return_val = i_process(arg)
