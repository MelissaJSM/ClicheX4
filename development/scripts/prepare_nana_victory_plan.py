"""원작 승리39·귀환3/40의10참조 및 공유 아머를 읽기 전용 조사한다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import INV,write
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame
FRAMES=set(range(156,162))|set(range(204,208))

def main():
 inv=json.loads(INV.read_text('utf8'));parts=(INV.parent/'composition_entry.bin').read_bytes();assert sha256((INV.parent/'original.arc').read_bytes())==inv['archive']['sha256'];rows=[]
 for n in sorted(FRAMES):
  f=inv['base_frames'][n];body={p['tile']for p in f['composition']['parts']};armor={p['tile']for b in range(5,9)for p in composition_frame(parts,b,n)['parts']}
  if body&armor:raise ValueError('Base/armor overlap')
  rows.append({'frame':n,'aliases':inv['stream_sharing'][str(f['offset'])],'budget':f['compressed_end']-f['offset'],'tile_count':f['tile_count'],'base_tiles':sorted(body),'armor_tiles':sorted(armor),'parts':f['composition']['parts'],'bounds':f['bounds']})
 out=ROOT/'work/ver_rin_nana/nana_art/victory_v1';out.mkdir(parents=True,exist_ok=True);write(out/'plan.json',{'source_inventory':INV.relative_to(ROOT).as_posix(),'frames':sorted(FRAMES),'groups':rows,'animations':{str(n):inv['animations'][n]for n in(3,39,40)},'excluded_special98':list(range(208,213)),'runtime_verified':False});print(json.dumps([{k:v for k,v in r.items()if k!='parts'}for r in rows]))
if __name__=='__main__':main()
