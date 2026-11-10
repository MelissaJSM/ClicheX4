"""남은 프로스트/라이징 계열9참조의 원작 조립·공유와 아머 분리를 확인한다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import INV,write
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame
FRAMES=[95,96,100,101,102,103,104,231,232]
def main():
 inv=json.loads(INV.read_text('utf8'));parts=(INV.parent/'composition_entry.bin').read_bytes();assert sha256((INV.parent/'original.arc').read_bytes())==inv['archive']['sha256'];rows=[]
 for n in FRAMES:
  f=inv['base_frames'][n];body={p['tile']for p in f['composition']['parts']};armor={p['tile']for b in range(5,9)for p in composition_frame(parts,b,n)['parts']}
  if body&armor:raise ValueError('Base/armor overlap')
  rows.append({'frame':n,'aliases':inv['stream_sharing'][str(f['offset'])],'budget':f['compressed_end']-f['offset'],'tile_count':f['tile_count'],'base_tiles':sorted(body),'armor_tiles':sorted(armor),'overlap':sorted(body&armor),'parts':f['composition']['parts'],'animations':[a['id']for a in inv['animations']if any(s['frame']==n for s in a['steps'])],'bounds':f['bounds']})
 aids=sorted({a for r in rows for a in r['animations']});d=ROOT/'work/ver_rin_nana/nana_art/special_remaining_v1';plan={'source_inventory':INV.relative_to(ROOT).as_posix(),'frames':FRAMES,'groups':rows,'animations':{str(a):inv['animations'][a]for a in aids}}
 if (d/'plan.json').exists():
  if json.loads((d/'plan.json').read_text('utf8'))!=plan:raise ValueError('Existing plan differs')
 else:d.mkdir(parents=True,exist_ok=True);write(d/'plan.json',plan)
 print(json.dumps({'frames':FRAMES,'streams':8,'existing_plan_reproduced':True,'original_arc_verified':True}))
if __name__=='__main__':main()
