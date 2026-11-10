"""남은 기본 X 참조 전체를 분류하고 원본 조립/공유/제약을 기록한다."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.psx_player import composition_frame
from scripts.discover_inputs import sha256

APPLIED=set(range(88))|{92}|set(range(106,126))|set(range(143,156))|{183}
STUBS={105,*range(175,183)}
HEADS=set(range(184,204))
EFFECTS={126,127,128,129,132,159,160,161,211,212,218,219}

def main():
 source=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';inv=json.loads((source/'inventory.json').read_text());parts=(source/'composition_entry.bin').read_bytes();assert sha256((source/'original.arc').read_bytes())==inv['archive']['sha256']
 out=ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1';out.mkdir(exist_ok=True);records=[]
 for f in inv['base_frames']:
  n=f['index'];body={q['tile'] for q in f['composition']['parts']};armor={q['tile'] for b in range(5,9) for q in composition_frame(parts,b,n)['parts']}
  records.append({'frame':n,'status':'applied' if n in APPLIED else 'placeholder' if n in STUBS else 'pending','kind':'head_overlay' if n in HEADS else 'effect' if n in EFFECTS else 'body','aliases':inv['stream_sharing'][str(f['offset'])],'budget':f['compressed_end']-f['offset'],'tile_count':f['tile_count'],'part_count':len(f['composition']['parts']),'base_tiles':sorted(body),'armor_tiles':sorted(armor),'base_armor_shared':sorted(body&armor),'bounds':f.get('bounds'),'parts':f['composition']['parts'],'animations':[a['id'] for a in inv['animations'] if any(s['frame']==n for s in a['steps'])]})
 groups={'arrival':[130,131,133,134,135,136,137,138,139,140,141,142], 'special':[88,89,90,91,95,96,97,98,99,100,101,102,103,104,231,232], 'clear_return':[156,157,158,204,205,206,207,208,209,210], 'vehicle':[162,166,170,174,184,193,195,196,199], 'air_extra':[93,94,213,214,215,216,217,220,221,223,225,227,229], 'hurt_extra':[233,234,235,236]}
 for name,ns in groups.items():
  sheet=Image.new('RGB',(4*288,((len(ns)+3)//4)*264),'#28394b');dr=ImageDraw.Draw(sheet)
  for i,n in enumerate(ns):
   f=inv['base_frames'][n];im=Image.open(source/f['image']).convert('RGBA');im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);x=i%4*288;y=i//4*264;sheet.paste(im,(x+(288-im.width)//2,y+24+(240-im.height)//2),im);dr.text((x+8,y+5),str(n),fill='white')
  sheet.save(out/f'original_{name}.png')
 plan={'source_inventory':str((source/'inventory.json').relative_to(ROOT)),'source_sha256':inv['source_sha256'],'applied_frames':sorted(APPLIED),'placeholder_frames':sorted(STUBS),'remaining_frames':sorted(set(range(237))-APPLIED-STUBS),'groups':records,'art_groups':groups,'runtime_deferred_by_user':True,'armor_design_in_scope':False}
 (out/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
 for r in records:
  if r['status']=='pending':print(r['frame'],r['kind'],'budget',r['budget'],'parts',r['part_count'],'base',r['base_tiles'],'shared',r['base_armor_shared'],'clut',sorted({q['clut'] for q in r['parts']}))
if __name__=='__main__':main()
