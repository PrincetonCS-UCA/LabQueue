__author__ = 'daifotis'
## THIS IS MEANT AS A LOCAL ONLY SCRIPT

from PIL import Image
import os

MAX_SIDE_PIXELS = 300

for fname in os.listdir("./img/TAs"):
    os.remove("./img/TAs/" + fname)

for fname in os.listdir("./img/OriginalTAs"):
    if fname.startswith('.'): #ignore hidden files
        continue
    im = Image.open(os.path.join("./img/OriginalTAs", fname))
    width, height = im.size
    orig_ratio = float(width) / height
    if width >= height:
        new_width = MAX_SIDE_PIXELS
        new_height = int(float(new_width) / orig_ratio)
    else:
        new_height = MAX_SIDE_PIXELS
        new_width = int(float(orig_ratio) * new_height)
    netid = os.path.splitext(fname)[0]
    im.resize((new_width, new_height), Image.ANTIALIAS).save("./img/TAs/" + os.path.splitext(fname)[0] + ".jpg")
    print "Processed photo...{}".format(fname)
print "Done."
