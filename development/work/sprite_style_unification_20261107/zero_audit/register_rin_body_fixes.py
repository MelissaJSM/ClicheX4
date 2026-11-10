"""Register only the newly drawn local sleeve/waist/thigh artwork."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension/detail_priority_singles';O=D/'registered_v3';assert not O.exists();O.mkdir()
arc=(D.parent/'prepared_air_continuation2_v2/PL01_U.ARC').read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rects={'b0_061':[(151,154,170,164)],'b1_005':[(157,154,169,167),(158,167,165,170)],'b1_183':[(141,166,163,173)]}
protect={'b0_061':[(140,157,154,164),(167,160,180,166)],'b1_005':[(150,153,158,157),(150,165,158,173)],'b1_183':[(153,170,156,172)]}
targets={};records=[]
for key in('b0_061','b0_174','b1_005','b1_183'):
 p=D/'registered_v2'/f'{key}_indices.png';previous=np.array(Image.open(p));target=previous.copy();mask=np.zeros_like(previous,bool)
 if key in rects:
  newpath=D/'body_fix01'/key/'native'/f'{key}_indices.png';new=np.array(Image.open(newpath))
  for x0,y0,x1,y1 in rects[key]:mask[y0:y1,x0:x1]=True
  for x0,y0,x1,y1 in protect[key]:mask[y0:y1,x0:x1]=False
  target[mask]=new[mask]
  assert np.array_equal(target[~mask],previous[~mask])
  source=D/'body_fix01'/key/'generated.png'
 else:source=None;newpath=None
 targets[key]=target;Image.fromarray(target).save(O/f'{key}_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(O/f'{key}_edit_mask.png')
 diff=target!=previous;added=int(np.count_nonzero((target>0)&(previous==0)));removed=int(np.count_nonzero((target==0)&(previous>0)))
 records.append({'key':key,'parent':str(p.relative_to(ROOT)),'parent_sha256':sha(p),'generated':str(source.relative_to(ROOT))if source else None,'generated_sha256':sha(source)if source else None,'registered_source':str(newpath.relative_to(ROOT))if newpath else None,'registered_source_sha256':sha(newpath)if newpath else None,'edit_rects':rects.get(key,[]),'protected_contact_rects':protect.get(key,[]),'changed_pixels':int(diff.sum()),'alpha_added':added,'alpha_removed':removed,'target':str((O/f'{key}_indices.png').relative_to(ROOT)),'target_sha256':sha(O/f'{key}_indices.png'),'all_pixels_outside_edit_mask_exact':True,'existing_detailed_head_hands_feet_exact':True})
for name,row in(('normal',0),('black',13)):
 pal=struct.unpack_from('<16H',entry(arc,9),row*32);sheet=Image.new('RGB',(1440,1576),'#626c78');draw=ImageDraw.Draw(sheet)
 for rr,(key,target)in enumerate(targets.items()):
  old=np.array(Image.open(D/'registered_v2'/f'{key}_indices.png'))
  for col,(label,a)in enumerate((('idle147',render(arc,0,0,147)[0]),('detailed_before',old),('local_body_fix',target))):
   pic=rgba(a,pal).crop((112,104,208,200)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(pic,(col*480+40,rr*394+10),pic);draw.text((col*480+8,rr*394+8),key+' '+label,fill='white')
 sheet.save(O/(name+'_comparison.png'))
report={'parent_art_directory':str((D/'registered_v2').relative_to(ROOT)),'edit_source':'내장 imagegen으로 3개 자세의 체형만 국소 재작화. 기존 세밀 머리·손·발·리본은 불투명/투명 픽셀 모두 그대로 보존.','old_game_art_overwrite':False,'geometry_timing_changed':False,'arc_applied':False,'records':records,'review_status':'네이티브 비교 후 검토 중'}
(O/'registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
# Correct earlier metadata language without touching art or immutable source files.
for key in rects:
 p=D/'body_fix01'/key/'inputs.json';j=json.loads(p.read_text('utf8'));j['edit_scope']='의상과 체형의 국소 보완. 이미 세밀하게 그린 머리·손·발 보호.';p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
p=D/'body_review/findings.json';j=json.loads(p.read_text('utf8'));j['status']='국소 재작화 필요. 42참조 확정 ARC에는 미적용.';p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(records))
