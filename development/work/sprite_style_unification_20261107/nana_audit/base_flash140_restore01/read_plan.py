"""후속140 추가알파의 원자료/수납가능성 읽기. 후보ARC는 쓰지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(W/'shibuki_audit')]
from preview_restore import Archive,digest,sha,write,need
from src.psx_player import composition_frame,indexed_atlas
from scripts.prepare_shibuki_ultimate_production import records
from probe_air_body_capacity import candidates
P=N/'base_nova_repaint/packed_nova_candidate_v1/PL00_U.ARC';EXPECTED='94cf560530c87ac11a03c029a9b6e98be44c06ea6d30d6c5ce66204c8a8e3cb3'
def main():
 need(digest(P)==EXPECTED,'고정노바후보');a=Archive(P.read_bytes());idle=a.layer(0)[0];base=a.layer(140)[0];fx=(base>0)&(idle==0);need(int(fx.sum())==46 and np.all(base[base>0]==13),'기본실루엣/원46효과')
 extras={pb:np.where((a.layer(0,pb)[0]>0)&(idle==0),13,0).astype(np.uint8)for pb in(5,6,7,8)};need([int((z>0).sum())for z in extras.values()]==[72,3,1,73],'파츠별추가알파')
 group=a.banks[0]['frames'][140];need(group['tile_count']==10 and[q['index']for q in a.banks[0]['frames']if q['offset']==group['offset']]==[140],'단독10타일')
 used={p['tile']for p in composition_frame(a.c,0,140)['parts']};head=[r.hex()for r in candidates(a.c,5,extras[5])]
 out=D/'read_plan.json';need(not out.exists(),'새읽기기록');write(out,{'read_only':True,'parent_candidate':P.relative_to(ROOT).as_posix(),'parent_sha256':EXPECTED,'parent_frozen_at_read':P.with_name('FROZEN.json').exists(),'effect46_world_samples':[[int(x-160),int(y-160),int(base[y,x])]for y,x in np.argwhere(fx)],'extra_alpha_by_layer':{str(pb):int((z>0).sum())for pb,z in extras.items()},'raw_single_owner':[140],'original_tile_count':10,'base_consumed_tiles':sorted(used),'available_after_replacing_empty_armor':sorted(set(range(10))-used),'head_record_candidates':head,'proposed_lossless_storage':'기존head기록 tile1/x−4/y−23를재사용하고140base옛tile1을미소비6으로이동.원FXtile8전체는불변.남은0/7/9중leg2타일과13색단일점공유1타일로body3/arm1을수납할수있는지후속메모리시험.10타일유지를우선하며불가하면정확한이유를기록.','proposed_art_policy':'140base와원46효과는변경없음.각아머idle밖알파72/3/1/73만색13추가.208..212다른참조는raw/조립/표시그대로.','source_callers':{'path':(W/'zero_audit/nana_base_effect_callers01/conclusions.json').relative_to(ROOT).as_posix(),'sha256':digest(W/'zero_audit/nana_base_effect_callers01/conclusions.json')},'native_packed':False,'runtime_verified':False});print(json.dumps({'extra':[72,3,1,73],'unused':sorted(set(range(10))-used),'head':head}))
if __name__=='__main__':main()
