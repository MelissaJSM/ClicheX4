"""현재 후보의 고정 entry2 후미 여유를 읽기만 집계한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from src.psx_player import decode_stream
def main():
 p=H/'prepared_hurt_base01/PL00_U.ARC';a=Archive(p.read_bytes());rows=[];seen={}
 for bi,b in enumerate(a.banks):
  if b['base']in seen:rows.append({'bank':bi,'alias':seen[b['base']]});continue
  seen[b['base']]=bi;end=b['base']+4*len(b['frames']);streams={}
  for f in b['frames']:
   dec=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128);end=max(end,dec.end);streams[f['offset']]={'end':dec.end,'count':f['tile_count'],'decoded_sha256':sha(dec.data)}
  aligned=(end+3)//4*4;rows.append({'bank':bi,'start':b['base'],'end':b['end'],'span':b['end']-b['base'],'refs':len(b['frames']),'unique_streams':len(streams),'last_consumed':end,'minimum_unchanged_span':aligned-b['base'],'unconsumed_aligned_tail':b['end']-aligned,'bank_sha256':sha(a.g[b['base']:b['end']]),'compressed_prefix_sha256':sha(a.g[b['base']:aligned])})
 write(H/'standing_special_capacity_readonly.json',{'parent_sha256':sha(a.data),'entry2_length':len(a.g),'rows':rows,'new_targets':[95,96,97],'target_15_layers_unchanged':True,'best_current_joint_stream':{'path':str((H/'standing_special_storage03/joint.raw').relative_to(ROOT)).replace('\\','/'),'sha256':sha((H/'standing_special_storage03/joint.raw').read_bytes()),'compressed_bytes':2222,'fixed_bank_shortfall':280},'no_relocation_applied':True,'arc_written':False,'read_only_method_limit':'후미 여유는 종료 토큰까지의 실제 디코더 읽기 기준이다. 전체 실행 코드의 미참조 증명이나 변경 허가를 뜻하지 않는다.'});print(json.dumps(rows))
if __name__=='__main__':main()
