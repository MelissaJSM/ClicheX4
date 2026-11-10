"""기본형 X의 무기 전환/점멸 CLUT를 Shibuki 몸 색으로 맞춘다. 효과·아머 행 보존."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json
from scripts.discover_inputs import psx_arc,sha256

WEAPON_ROWS=[3+4*i for i in range(8)]
FLASHES={35:((31,31,31),.65),38:((22,28,31),.35),41:((31,31,25),.45),44:((29,23,31),.45),47:((31,29,20),.45),50:((31,31,31),.18),73:((19,27,31),.60)}

def edited_palette(old):
 if len(old)!=2464:raise ValueError('Unsupported X palette entry')
 base=struct.unpack('<16H',old[:32])
 if base[0]!=0 or any(not v for v in base[1:]):raise ValueError('Unsupported transparency')
 result=bytearray(old);rows={}
 for row in WEAPON_ROWS+list(FLASHES):
  original=struct.unpack_from('<16H',old,row*32)
  if original[0]!=0:raise ValueError('Unexpected body palette transparency')
  words=[0]
  for i in range(1,16):
   rgb=[(base[i]>>s)&31 for s in (0,5,10)]
   if row in FLASHES:
    target,weight=FLASHES[row];rgb=[round(c*(1-weight)+t*weight) for c,t in zip(rgb,target)]
   words.append((original[i]&0x8000)|sum(c<<s for c,s in zip(rgb,(0,5,10))))
  struct.pack_into('<16H',result,row*32,*words);rows[str(row)]=words
 allowed={i for row in WEAPON_ROWS+list(FLASHES) for i in range(row*32,(row+1)*32)}
 if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(old,result))):raise AssertionError('Unexpected palette edit')
 return bytes(result),rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);args=p.parse_args();parent=args.parent.resolve()
 if not parent.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Isolated parent required')
 pm=json.loads((parent/'manifest.json').read_text());arc=(parent/'modified.arc').read_bytes();cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text())
 if pm['task']!='x_shibuki' or sha256(arc)!=pm['modified_archive_sha256']:raise ValueError('Parent changed')
 e=next(e for e in psx_arc(arc) if int(e['type'],16)==9);old=arc[e['offset']:e['offset']+e['size']];new,rows=edited_palette(old);changed=[e['offset']+i for i,(x,y) in enumerate(zip(old,new)) if x!=y];patched=bytearray(arc);patched[e['offset']:e['offset']+e['size']]=new
 out=new_run(ROOT,'ver_buki_riko','shibuki_weapon_palette');(out/'modified.arc').write_bytes(patched)
 recipe={'task':'x_shibuki','scope':'base_weapon_body_palettes','parent_build':str(parent.relative_to(ROOT)),'parent_bin_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha256(arc),'original_arc_sha256':cfg['archive']['sha256'],'modified_arc_sha256':sha256(patched),'arc_size':len(patched),'weapon_body_rows':WEAPON_ROWS,'flash_body_rows':list(FLASHES),'palette_words':rows,'changed_archive_bytes':changed,'base_palette_preserved':True,'all_graphics_and_compositions_preserved':True,'effect_and_armor_palette_rows_preserved':True,'run_frames_preserved':True,'shooting_body_uses_same_run_pose':True,'shooting_arm_art_pending':False,'runtime_verified':False,'evidence':'Local US runtime weapon 1 = row 3; player_common.c player_reset_palette copies body row 3+4*(weapon-1), player_set_palette flashes; only first/body row changed'}
 write_json(out/'recipe.json',recipe);print(json.dumps({'output':str(out),'arc_sha256':sha256(patched),'edited_body_rows':len(rows),'changed_bytes':len(changed)}))
if __name__=='__main__':main()
