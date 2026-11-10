import json,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
d=Path(__file__).parent;a=d/'production05';a.mkdir(exist_ok=True)
parent=ROOT/'out/ver_buki_riko/shibuki_special_style_20261026T230854606760Z'
arc=(parent/'modified.arc').read_bytes();es=psx_arc(arc)
g,c,pal=[arc[e['offset']:e['offset']+e['size']] for t in (2,3,9) for e in es if int(e['type'],16)==t]
words=list(struct.unpack('<16H',pal[:32]));rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.int32)
old=json.loads((d.parent/'remaining_v1/production14/art.json').read_text());ns=list(range(133,143))+list(range(204,208));groups=[q for q in old['groups'] if q['frame'] in ns];bank=graphics_bank(g,0,allow_bank_aliases=True)
for q in groups:
 f=bank['frames'][q['frame']];q['budget']=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).end-f['offset']
 q['part_slots']={str(k):[p['index'] for p in composition_frame(c,0,k)['parts'] if p['tile'] in q['writable']] for k in q['aliases']}
src=Image.open(d/'generated_v2.png').convert('RGBA');crop=[]
# Actual transparent row gutter is below the top-row soles; the overhead hands start above the bottom-row ears.
row_cut=475
for i in range(10):
 cell=src.crop((round(i%5*src.width/5),0 if i<5 else row_cut,round((i%5+1)*src.width/5),row_cut if i<5 else src.height))
 yy,xx=np.nonzero(np.array(cell)[:,:,3]>=160);bb=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));crop.append((cell.crop(bb),bb))
scale=47/crop[9][0].height;targets={};records=[]
for i,n in enumerate([133,135,137,138,142,204,205,206,207,0]):
 im,bb=crop[i];size=(round(im.width*scale*23/26),round(im.height*scale));arr=quantize(im,size,rgb,128);yy,xx=np.nonzero(arr)
 ey,ex=np.nonzero((arr==7)&(np.indices(arr.shape)[0]<arr.shape[0]*.7));left=round(75-float(np.median(ex[ey<=ey.min()+1])));top=102-int(yy.max());v=np.zeros((160,160),np.uint8);v[top:top+size[1],left:left+size[0]]=arr;targets[n]=v
 records.append({'frame':n,'source_cell':i,'crop':bb,'scale':scale,'common_horizontal_calibration':23/26,'size':size,'offset':[left,top],'eye':[float(np.median(ex[ey<=ey.min()+1]))+left,float(np.median(ey[ey<=ey.min()+1]))+top]})
def move(v,dy):
 out=np.zeros_like(v);y,x=np.nonzero(v);out[y+dy,x]=v[y,x];return out
targets[136]=move(targets[135],-1);targets[139]=move(targets[138],-1);targets[141]=targets[142].copy();targets[140]=np.where(targets[142]!=0,9,0).astype(np.uint8)
# 134 is a three-tick bright materialization of crouch133 inside the existing effect.
f=bank['frames'][134];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;bg=canvas_from_parts(raw,f['tile_count'],composition_frame(c,0,134))%16
oldbody=np.array(Image.open(d.parent/'remaining_v1/production14/frame_133.png'));ef=bank['frames'][129];eraw=decode_stream(g,ef['offset'],ef['limit'],ef['tile_count']*128).data;ebg=canvas_from_parts(eraw,ef['tile_count'],composition_frame(c,0,129))%16;bg=ebg.copy()
v=targets[133];bright=np.array([0,14,14,9,14,5,9,9,14,9,14,14,9,9,14,5],np.uint8);bg[v!=0]=bright[v[v!=0]];targets[134]=bg
for n,v in targets.items():save_image(v.tobytes(),(160,160),words,a/f'frame_{n:03}.png')
art={**old,'parent':str(parent.relative_to(ROOT)),'groups':groups,'remaining_frames':ns,'frames':[{'frame':n,'image':f'frame_{n:03}.png'} for n in ns],'effect_index_mapping':list(range(16)),'normalization':records,'revision_source_sha256':sha256((d/'generated_v2.png').read_bytes())}
(a/'art.json').write_text(json.dumps(art,indent=2));sheet=Image.new('RGB',(7*240,3*264),'#253546');dr=ImageDraw.Draw(sheet)
items=[('APPROVED 0',parent/'sprite_review/frame_000.png'),('CALIBRATION',a/'frame_000.png')]+[(str(n),a/f'frame_{n:03}.png') for n in ns]
for i,(label,path) in enumerate(items):
 im=Image.open(path).convert('RGBA').crop((40,35,120,115)).resize((240,240),Image.Resampling.NEAREST);x=i%7*240;y=i//7*264;sheet.paste(im,(x,y+24),im);dr.text((x+5,y+5),label,fill='white')
sheet.save(a/'comparison.png');print(json.dumps(records));print('source_size',src.size,'row_cut',row_cut)
