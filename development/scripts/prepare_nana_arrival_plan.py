"""원작 등장1/2와 공유 특수95/96의17참조를 읽기 전용으로 조사한다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import INV,write
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame
def main():
 inv=json.loads(INV.read_text('utf8'));parts=(INV.parent/'composition_entry.bin').read_bytes();assert sha256((INV.parent/'original.arc').read_bytes())==inv['archive']['sha256'];rows=[]
 for n in range(126,143):
  f=inv['base_frames'][n];body={p['tile']for p in f['composition']['parts']};armor={p['tile']for b in range(5,9)for p in composition_frame(parts,b,n)['parts']};assert not body&armor
  rows.append({'frame':n,'aliases':inv['stream_sharing'][str(f['offset'])],'budget':f['compressed_end']-f['offset'],'tile_count':f['tile_count'],'base_tiles':sorted(body),'armor_tiles':sorted(armor),'parts':f['composition']['parts'],'bounds':f['bounds']})
 out=ROOT/'work/ver_rin_nana/nana_art/arrival_v1';out.mkdir(parents=True,exist_ok=True);write(out/'plan.json',{'source_inventory':INV.relative_to(ROOT).as_posix(),'frames':list(range(126,143)),'groups':rows,'animations':{str(n):inv['animations'][n]for n in(1,2,95,96)},'runtime_verified':False});print(json.dumps([{k:v for k,v in r.items()if k!='parts'}for r in rows]))
if __name__=='__main__':main()
