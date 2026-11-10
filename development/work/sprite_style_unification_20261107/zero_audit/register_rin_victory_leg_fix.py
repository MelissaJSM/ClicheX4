from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension/detail_priority_singles';O=D/'registered_v4';assert not O.exists();O.mkdir()
arc=(D.parent/'prepared_air_continuation2_v2/PL01_U.ARC').read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
key='b1_005';p=D/'registered_v3'/f'{key}_indices.png';before=np.array(Image.open(p));npng=D/'victory_leg_fix02/native'/f'{key}_indices.png';new=np.array(Image.open(npng))
mask=np.zeros_like(before,bool);mask[161:177,158:167]=True;after=before.copy();after[mask]=new[mask]
assert np.array_equal(after[~mask],before[~mask])
for k in('b0_061','b0_174','b1_005','b1_183'):
 a=after if k==key else np.array(Image.open(D/'registered_v3'/f'{k}_indices.png'));Image.fromarray(a).save(O/f'{k}_indices.png')
Image.fromarray(mask.astype(np.uint8)*255).save(O/'b1_005_edit_mask.png')
for name,row in(('normal',0),('black',13)):
 pal=struct.unpack_from('<16H',entry(arc,9),row*32);sheet=Image.new('RGB',(1280,660),'#626c78');draw=ImageDraw.Draw(sheet)
 for i,(label,a)in enumerate((('idle147',render(arc,0,0,147)[0]),('previous_detail',before),('new_leg',after))):
  pic=rgba(a,pal).crop((128,120,192,184)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(pic,(i*420+10,30),pic);draw.text((i*420+10,10),label,fill='white')
  detail=rgba(a,pal).crop((148,156,174,184)).resize((208,224),Image.Resampling.NEAREST);sheet.paste(detail,(i*420+80,425),detail)
 sheet.save(O/f'{name}_victory_comparison.png')
proof={'edit_parent_sha256':sha(p),'generated_sha256':sha(D/'victory_leg_fix02/generated.png'),'native_source_sha256':sha(npng),'target_sha256':sha(O/f'{key}_indices.png'),'edit_rect':[158,161,167,177],'changed_pixels':int(np.count_nonzero(before!=after)),'head_hands_ribbon_and_feet_exact':True,'outside_rect_including_transparency_exact':True,'other_three_art_pngs_unchanged':True,'game_changed':False,'native_readback_note':'지지 허벅지 가운데 단면5→6px, 장딴지 최협부4→5px. 지시했던7px에 정확 도달했다고 주장하지 않음. 전체 크기·발 위치 불변.'}
(O/'registration.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(proof))
