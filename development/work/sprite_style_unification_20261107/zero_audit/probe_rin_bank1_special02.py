"""새 뇌신격 찌르기 원화의 고정배율 등록과 원손·발 접점을 비교한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension/bank1_special02';O=D/'anchor_probe_v1';assert not O.exists();O.mkdir()
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();assert hashlib.sha256(arc).hexdigest()==info['archive_sha256'];pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32)
shifts={108:(-1,-3),110:(1,-3),112:(-1,0),119:(1,0)};items={k:[]for k in('normal','black')};records=[]
def feet(a):
 y=int(np.nonzero(a)[0].max());xs=np.nonzero(np.any(a[y-2:y+1]>0,axis=0))[0];groups=[]
 for x in xs:
  if not groups or x>groups[-1][-1]+1:groups.append([int(x)])
  else:groups[-1].append(int(x))
 return {'floor':y,'last_three_rows_x_runs':[[g[0],g[-1]]for g in groups]}
for f in info['frames']:
 key=f['key'];old=render(arc,1,5,f['ref'])[0];a=np.array(Image.open(D/'native_fixed'/(key+'_indices.png')));dx,dy=shifts[f['ref']];v=np.roll(a,(dy,dx),(0,1));assert np.count_nonzero(v)==np.count_nonzero(a);assert feet(v)['floor']==feet(old)['floor'];p=O/(key+'_indices.png');Image.fromarray(v).save(p)
 for name,words in [('normal',pal),('black',black)]:items[name].extend([(key+' old',rgba(old,words)),(key+f' new {dx:+},{dy:+}',rgba(v,words))])
 records.append({'key':key,'translation':[dx,dy],'old_bbox':rgba(old,pal).getbbox(),'new_bbox':rgba(v,pal).getbbox(),'old_feet':feet(old),'new_feet':feet(v),'old_cyan':np.argwhere(old==15)[:,::-1].tolist(),'new_cyan':np.argwhere(v==15)[:,::-1].tolist(),'head_old_override':False,'local_warp':False,'output_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for name,words in [('normal',pal),('black',black)]:page(items[name],rgba(render(arc,0,0,147)[0],words),O/(name+'_comparison.png'),cols=2,scale=5)
full=np.array(Image.open(D/'generated.png').convert('RGBA').crop((627,627,1254,1254)));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);nearest=np.zeros(full.shape[:2],np.uint8)
for y in range(627):nearest[y]=np.argmin(((full[y,:,:3].astype(np.int32)[:,None]-colors[None])**2).sum(2),axis=1)+1
votes=np.stack([np.array(Image.fromarray(np.where(nearest==i,full[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
eye=[]
for y,x in np.argwhere(votes[14]>5):
 xx,yy=int(x)+113,int(y)+104
 if 126<=xx<145 and 147<=yy<162:eye.append({'xy':[xx,yy],'cyan_weight':int(votes[14,y,x]),'winner':int(votes[:,y,x].argmax()+1),'winner_weight':int(votes[:,y,x].max())})
(O/'registration.json').write_text(json.dumps({'source_art_sha256':hashlib.sha256((D/'generated.png').read_bytes()).hexdigest(),'records':records,'119_eye_vote_candidates':sorted(eye,key=lambda a:-a['cyan_weight']),'needs_art_and_hand_effect_contact_review':True,'game_changed':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'records':records,'119_eye_votes':eye}))
