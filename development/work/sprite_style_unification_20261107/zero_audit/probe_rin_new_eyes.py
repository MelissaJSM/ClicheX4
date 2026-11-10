from pathlib import Path
import json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;R=D/'rin_extension/detail_priority_singles'
from scripts.prepare_riko_ui import entry
arc=(D/'rin_extension/prepared_air_continuation2_v2/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
rows=[]
for key,box in [('b0_061',(140,130,170,162)),('b1_005',(150,125,174,155)),('b1_183',(130,150,160,176))]:
 p=R/key;im=Image.open(p/'generated.png').convert('RGBA');full=np.array(im);near=np.zeros(full.shape[:2],np.uint8)
 for y in range(im.height):near[y]=np.argmin(((full[y,:,:3].astype(np.int32)[:,None]-colors[None])**2).sum(2),axis=1)+1
 v=np.stack([np.array(Image.fromarray(np.where(near==i,full[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
 dy=json.loads((p/'native/registration.json').read_text('utf8'))['records'][0]['translate'][1];new=np.array(Image.open(p/'native'/(key+'_indices.png')));opts=[]
 for yy,xx in np.argwhere(v[14]>10):
  y,x=int(yy)+104+dy,int(xx)+112
  if box[0]<=x<box[2] and box[1]<=y<box[3] and new[y,x]>0:
   opts.append({'x':x,'y':y,'cyan':int(v[14,yy,xx]),'winner':int(np.argmax(v[:,yy,xx])+1),'winner_weight':int(v[:,yy,xx].max()),'skin_neighbors':int(np.isin(new[y-1:y+2,x-1:x+2],[12,13,14]).sum())})
 rows.append({'key':key,'source_size':im.size,'candidate_cells':sorted(opts,key=lambda x:-x['cyan'])[:10]})
out=R/'eye_vote_probe.json';out.write_text(json.dumps(rows,indent=2)+'\n','utf8');print(json.dumps(rows))
