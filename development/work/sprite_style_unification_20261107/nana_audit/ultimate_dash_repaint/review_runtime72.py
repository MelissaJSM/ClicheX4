"""루트가 저장한 실기 관측 파일만 읽는다. 프로세스/입력/게임 파일에 쓰지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from src.psx_player import decode_stream
def main():
 out=D/'runtime72_review_v2';out.mkdir(exist_ok=False);R=ROOT/'work/sprite_style_unification_20261107/runtime';first=R/'nana_dash12_watch';retry=R/'nana_dash12_left_retry_watch';a=Archive((D/'packed_dash_candidate_v1/PL02_U.ARC').read_bytes());need(sha(a.data)=='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0','Frozen');raws={n:decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data for n,f in enumerate(a.banks[0]['frames'])};records=[]
 for directory in(first,retry):
  p=directory/'evidence.json';m=json.loads(p.read_text('utf8'));need(m['resident_assets'][0]['archive_sha256']==sha(a.data),'Resident parent');evs=[e for e in m['events']if e['frame']==72];total=sum(e['stable_samples']for e in evs);bad=sum(e['gpu_mismatches']for e in evs);records.append({'evidence':str(p.relative_to(ROOT)),'sha256':digest(p),'events72':evs,'stable_samples72':total,'gpu_failed_samples72':bad,'ram_failed_samples72':sum(e['ram_mismatches']for e in evs),'any_failed_event72':any(not e['verified']for e in evs),'all72_mask0':all(e['derived_renderer_visual_mask']==0 for e in evs)})
 diags=[]
 m=json.loads((retry/'evidence.json').read_text('utf8'))
 for index,e in enumerate(m['events']):
  if not e.get('diagnostic'):continue
  q=e['diagnostic'];expected=(retry/q['expected']).read_bytes();gpu=(retry/q['gpu']).read_bytes();need(expected==raws[e['frame']],'Expected tied to actual final ARC');need(len(gpu)==len(expected),'Length');diff=np.frombuffer(expected,np.uint8)!=np.frombuffer(gpu,np.uint8);need(int(diff.sum())==q['differing_bytes'],'Count');scores=[]
  for n,r in raws.items():
   # 16/32타일에서는 각16타일 행의128B폭이 동일하다.
   if len(r)>=len(gpu)and len(r)>=2048:
    scores.append((sum(x!=y for x,y in zip(r[:len(gpu)],gpu)),n))
  best=sorted(scores)[:12];rows=[]
  for row in range(len(gpu)//128):
   piece=gpu[row*128:(row+1)*128];matches=[n for n,r in raws.items()if len(r)>=max(2048,(row+1)*128)and r[row*128:(row+1)*128]==piece];rows.append({'row':row,'different_bytes_from_expected':int(diff[row*128:(row+1)*128].sum()),'matching_full_width_source_frames':matches})
  diags.append({'event':index,'frame':e['frame'],'facing':e['facing_raw'],'expected_sha256':sha(expected),'gpu_sha256':sha(gpu),'different_bytes':int(diff.sum()),'closest_full_width_frame_prefixes':best,'rows':rows,'neighbor_events':m['events'][max(0,index-2):index+3]})
 before=a.layer(72,0)[0];delta=a.layer(72,5)[0];need(int(before[164,125])==0 and int(delta[164,125])==1,'Preserved72 mask point')
 result={'passed':True,'scope':'保存된 관측/원화 자원을 읽은 사후 검사. 새 프로세스 접근·키·쓰기·실기 없음.','candidate_sha256':sha(a.data),'observations':records,'retry_diagnostics':diags,'mask_policy':{'frame':72,'ultimate':1,'owned':15,'derived_mask':0,'original_point_world':[-35,4],'base_index':0,'before_layer_index':1,'upload_independent_of_mask':True,'reason':'관측기131~140행은전체그래픽디코드바이트와16행씩VRAM읽기를대조한다.파츠조립/마스크는이비교에개입하지않는다.'},'stable_scope_limitation':'stable은player[0x38:0x4a] 전후동일만검사한다.32행의각ReadProcessMemory가원자적인GPU snapshot인것을보장하지않는다.최초실패시GPU미저장으로첫72실패의정확원인은확정불가.','observer_script_sha256':digest(ROOT/'scripts/observe_sprite_consistency_runtime.py'),'runtime_verified_by_this_audit':False}
 idle=(retry/'event_0038_b0_f0_gpu.bin').read_bytes();moving=(retry/'event_0089_b0_f76_gpu.bin').read_bytes()
 need(idle==raws[119],'Idle diagnostic equals previous119 exactly')
 need(moving[:11*128]==raws[72][:11*128]and moving[11*128:]==raws[76][11*128:],'Mixed scanline transition71/72 to75/76')
 need(moving!=raws[76]and moving!=raws[72],'Mixed sample is neither completed frame')
 result['diagnostic_conclusion']={'idle0_exact_previous_frame':119,'frame76_row_sources':[{'rows_inclusive':[0,10],'raw_refs':[71,72]},{'rows_inclusive':[11,31],'raw_refs':[75,76]}],'interpretation':'저장된 GPU 표본에서 직전 업로드 전체 및 직전/목표 업로드의 행 단위 혼합을 직접 확인했다. 비원자적 행 읽기 또는 업로드 전환 시점의 관측이며 고정된72 원화·마스크 결함의 근거가 아니다. 최초72 실패는 덤프가 없어 원인을 동일하게 확정하지 않는다.','retry72_stable_samples':records[1]['stable_samples72'],'retry72_failed_samples':records[1]['gpu_failed_samples72']}
 result['scope']='저장된 관측/원화 자원을 읽은 사후 검사. 새 프로세스 접근·키·쓰기·실기 없음.'
 write(out/'report.json',result);print(json.dumps({'observations':[(r['stable_samples72'],r['gpu_failed_samples72'])for r in records],'diagnostics':[(q['frame'],q['closest_full_width_frame_prefixes'][:3])for q in diags],'report_sha256':digest(out/'report.json')}))
if __name__=='__main__':main()
