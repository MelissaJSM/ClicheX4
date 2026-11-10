from pathlib import Path
import json
from PIL import Image
d=Path(__file__).parent;root=d.parents[3];inv=json.loads((root/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json').read_text('utf8'));source=root/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z'
nums=[13,15,17,19,21,23,25,27]
board=Image.new('RGBA',(8*256,288),(0,0,0,0))
for i,n in enumerate(nums):
 im=Image.open(source/f'base_{n:03d}.png').convert('RGBA');b=inv['base_frames'][n]['bounds'];im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST);board.paste(im,(i*256+128+b[0]*4,144+b[1]*4),im)
board.save(d/'second_half_native.png')
im=Image.open(d/'stride_revision.png');im.crop((0,im.height//2,im.width,im.height)).save(d/'second_half_target.png')
