from pathlib import Path
import json,sys,hashlib,shutil,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,helper
from register_page import register
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
ap=argparse.ArgumentParser();ap.add_argument('page',type=int);ap.add_argument('source',type=Path);a=ap.parse_args()
out=D/f'art_page{a.page:02}';out.mkdir(exist_ok=False);dest=out/'generated.png';shutil.copy2(a.source,dest)
im=Image.open(dest).convert('RGBA');m=read(D/f'inputs_page{a.page:02}/manifest.json');arcpath=ROOT/m['source_arc'];assert sha(arcpath.read_bytes())==m['source_arc_sha256'];arc=Archive(arcpath.read_bytes())
for q in m['inputs']:assert sha((ROOT/q['path']).read_bytes())==q['sha256']
gen={'tool':'builtin image_gen','source_path':str(a.source),'workspace_path':dest.relative_to(ROOT).as_posix(),'workspace_sha256':sha(dest.read_bytes()),'source_sha256':sha(a.source.read_bytes()),'size':list(im.size),'alpha_extrema':list(im.getchannel('A').getextrema()),'input_manifest_sha256':sha((D/f'inputs_page{a.page:02}/manifest.json').read_bytes()),'prompt_path':(D/f'inputs_page{a.page:02}/prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':sha((D/f'inputs_page{a.page:02}/prompt.txt').read_bytes()),'native_packed':False,'runtime_verified':False}
(out/'generation.json').write_text(json.dumps(gen,ensure_ascii=False,indent=2)+'\n','utf8')
reg=D/f'registered_page{a.page:02}';reg.mkdir(exist_ok=False);records=[];rows=[]
for q in m['frames']:
 cell=q['cell'];form=q['form'];ref=q['ref'];start=16 if q['mask'] else 0
 box=tuple(round(v) for v in ((cell%2)*im.width/2,(cell//2)*im.height/2,(cell%2+1)*im.width/2,(cell//2+1)*im.height/2));crop=im.crop(box)
 arr=np.array(crop);labs,_=label(arr[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;assert sum(counts>1000)==1
 palette=np.array([[((int(w)>>s)&31)*255//31 for s in (0,5,10)] for w in arc.words[start:start+16]],np.float32)
 z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(crop,(96,96),palette,'area_vote')
 Image.fromarray(z).save(reg/f'{form}_{ref:03}_indices.png');image=arc.rgba(z,start);image.save(reg/f'{form}_{ref:03}_rgba.png')
 old=arc.composite(ref,q['mask'],2)[0];rows.append((f'{form} {ref}',[('accepted idle',arc.composite(0,q['mask'],2)[0]),('current ladder',old),('new fixed cell',image)]))
 records.append({'form':form,'ref':ref,'source_cell_crop':box,'native_cell':[96,96],'world_origin':[160,160],'whole_body_translation':[0,0],'old_bbox':old.getbbox(),'new_bbox':image.getbbox(),'native_indices_sha256':sha(z.tobytes()),'native_rgba_sha256':sha(image.tobytes()),'connected_components8':int(label(z>0,np.ones((3,3)))[1]),'old_art_pixels_copied':0})
for j in range(0,len(rows),2):helper.grid(rows[j:j+2],reg/f'comparison_{j//2+1}.png',6)
(reg/'registration.json').write_text(json.dumps({'source_art_sha256':gen['workspace_sha256'],'parent_arc_sha256':m['source_arc_sha256'],'method':'96x96 전체셀 면적투표 팔레트등록. bbox 재축척/행삭제/기존머리덮기 없음.','frames':records,'contacts_verified':False,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'source_size':list(im.size),'alpha':gen['alpha_extrema'],'frames':records}))
