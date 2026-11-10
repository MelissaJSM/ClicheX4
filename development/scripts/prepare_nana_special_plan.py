"""원작 차지 연계91·더블 사이클론104/105의 몸7참조와 공유 범위를 조사한다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_idle_shot import INV,write
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame,bank_offsets
import struct
FRAMES={88,89,90,91,97,98,99}
def main():
 inv=json.loads(INV.read_text('utf8'));parts=(INV.parent/'composition_entry.bin').read_bytes();assert sha256((INV.parent/'original.arc').read_bytes())==inv['archive']['sha256'];rows=[]
 for n in sorted(FRAMES):
  f=inv['base_frames'][n];body={p['tile'] for p in f['composition']['parts']};armor={p['tile']for b in range(5,9)for p in composition_frame(parts,b,n)['parts']}
  if body&armor:raise ValueError('Base/armor overlap')
  rows.append({'frame':n,'aliases':inv['stream_sharing'][str(f['offset'])],'budget':f['compressed_end']-f['offset'],'tile_count':f['tile_count'],'base_tiles':sorted(body),'armor_tiles':sorted(armor),'parts':f['composition']['parts'],'bounds':f['bounds']})
 for b,o in enumerate(bank_offsets(parts)):
  if struct.unpack_from('<I',parts,o)[0]>>16>97 and {12,13}&{p['tile']for p in composition_frame(parts,b,97)['parts']}:raise ValueError('97 spare referenced')
 out=ROOT/'work/ver_rin_nana/nana_art/special_v1';out.mkdir(parents=True,exist_ok=True)
 write(out/'plan.json',{'source_inventory':INV.relative_to(ROOT).as_posix(),'frames':sorted(FRAMES),'groups':rows,'animations':{str(n):inv['animations'][n]for n in(91,104,105)},'preserve_frame88_trail_tiles':[7,8],'97_spares_checked_all_banks':[12,13],'runtime_verified':False})
 print(json.dumps({'frames':sorted(FRAMES),'stream_groups':5,'all_banks_spares_clear':True}))
if __name__=='__main__':main()
