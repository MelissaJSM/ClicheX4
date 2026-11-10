"""ref1의 수용 idle0 무변경 공유와 ref2 단독 atlas 절감량 시험."""
from pathlib import Path
import sys,json,numpy as np,struct
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,write,sha
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import decode_stream
from probe_run_mixed_common import pack_pair
from probe_run_compact_flip import optimize
from probe_run_occluded_tile_union import decode_parts

def main():
    o=H/'base_run_idle_alias02';need(not o.exists(),'Fresh output');o.mkdir();a=Archive((H/'prepared_dash_base01/PL00_U.ARC').read_bytes());target={n:{b:np.array(Image.open(H/f'base_run_complete_targets01/{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}for n in(1,2)}
    for b in target[1]:need(np.array_equal(a.layer(0,b)[0],target[1][b]),'ref1 is not exact idle0')
    v=pack_pair((2,2),target,(0,6),True);rr={(b,2):decode_parts(v['parts'][str(b)]['2'])for b in(0,5,6,7,8)};raw,pp,proof=optimize(bytes.fromhex(v['raw']),rr,2,a.banks[0]['frames'][2]['tile_count'])
    f=a.banks[0]['frames'][0];old=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data
    r={'analysis_only':True,'resource_written':False,'parent_sha256':sha(a.data),'idle_alias':{'target_ref':1,'source_ref':0,'tile_count':f['tile_count'],'raw_sha256':sha(old),'raw':old.hex(),'parts':{str(b):records(a.c,b,0).hex()for b in target[1]},'no_new_stream_bytes':True},'shot2':dict(proof,refs=[2],raw=raw.hex(),parts={str(b):{'2':b''.join(struct.pack('<BBbb',*x)for x in pp[b,2]).hex()}for b in target[1]})}
    write(o/'result.json',r);print(json.dumps({k:v for k,v in proof.items()if k not in('tile_mapping','storage_hflip')},ensure_ascii=True))
if __name__=='__main__':main()
