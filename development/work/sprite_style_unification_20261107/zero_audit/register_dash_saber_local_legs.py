"""수용 새 상체를 보존하고 새로 보완한 하체 원화를 의미 구역에 등록한다."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
from scripts.prepare_rin_run import connected_groups
D=Path(__file__).parent/'rin_extension'/'dash_saber_followup02';A=D/'local_legs01';O=A/'registered_probe_v2';assert not O.exists();O.mkdir()
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();assert hashlib.sha256(arc).hexdigest()==info['archive_sha256'];pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32)
assert hashlib.sha256((A/'generated.png').read_bytes()).hexdigest()=='294299cbf65a3f2946d80422ca522998f5fd53facffb492bbdca94e0eda01b66'
items={k:[]for k in('normal','black')};records=[]
regions={166:((145,168,157,172),(164,168,174,172)),170:((150,167,162,172),(165,168,175,172)),172:((148,168,159,172),(162,168,174,172))}
for n,dy in((166,2),(170,3),(172,3)):
 key=f'b0_{n:03}';before=np.array(Image.open(A/(key+'_before_indices.png')));upper=np.roll(before,dy,axis=0);donor=np.array(Image.open(A/'native_fixed'/(key+'_indices.png')))
 donor_dy=1 if n==170 else 0
 if donor_dy:donor=np.roll(donor,donor_dy,axis=0)
 mask=np.zeros_like(upper,bool);mask[172:]=True
 for x0,y0,x1,y1 in regions[n]:mask[y0:y1,x0:x1]=True
 v=upper.copy();v[mask]=donor[mask];assert np.array_equal(v[~mask],upper[~mask])
 old=render(arc,0,0,n)[0];assert np.nonzero(v)[0].max()==np.nonzero(old)[0].max()
 Image.fromarray(v).save(O/(key+'_indices.png'));Image.fromarray(mask.astype('uint8')*255).save(O/(key+'_leg_mask.png'))
 for name,words in [('normal',pal),('black',black)]:items[name].extend([(key+' original',rgba(old,words)),(key+' first repaint',rgba(before,words)),(key+' local source',rgba(donor,words)),(key+' preserved upper + new legs',rgba(v,words))])
 records.append({'key':key,'upper_source':str((A/(key+'_before_indices.png')).relative_to(ROOT)),'upper_rigid_translation':[0,dy],'lower_source':str((A/'native_fixed'/(key+'_indices.png')).relative_to(ROOT)),'lower_rigid_translation':[0,donor_dy],'leg_regions':regions[n],'all_y_from':172,'upper_outside_leg_mask_exact':True,'new_floor':int(np.nonzero(v)[0].max()),'new_eye':np.argwhere(v==15)[:,::-1].tolist(),'components':[len(g)for g in connected_groups(v>0)],'source_leg_pixels':int(np.count_nonzero((donor>0)&mask)),'output_sha256':hashlib.sha256((O/(key+'_indices.png')).read_bytes()).hexdigest()})
for name,words in [('normal',pal),('black',black)]:
 page(items[name],rgba(render(arc,0,0,147)[0],words),O/(name+'_comparison.png'),cols=4,scale=4)
 detail=[v for i,v in enumerate(items[name])if i%4 in(0,3)]
 page(detail,rgba(render(arc,0,0,147)[0],words),O/(name+'_detail.png'),cols=2,scale=6)
(O/'registration.json').write_text(json.dumps({'records':records,'candidate_only':True,'scope':'새 상체 전신축소/행삭제 없이 평행이동. 다리만 국소 새 원화. 미패킹/미실기.'},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
