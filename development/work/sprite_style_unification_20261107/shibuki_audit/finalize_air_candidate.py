"""공중 후보의 입력 거부/재현/바이트 보호를 확인하고 검토용 제안을 고정한다."""
from pathlib import Path
import json,sys,subprocess
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from scripts.discover_inputs import psx_arc
from pack_air_targets_probe import validate_inputs,P,PARENT_SHA,LOCK_SHA
from native_pose_pack import need,sha,write

EXPECTED='c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be'
def main():
    output=H/'prepared_air01';need(not output.exists(),'Fresh output required')
    d=H/'air_targets_probe02';parent=P.read_bytes();candidate=(H/'air_pack_probe01/candidate_PL00_U.ARC').read_bytes()
    need(sha(parent)==PARENT_SHA and sha(candidate)==EXPECTED,'Resource changed')
    validate_inputs(parent,d)
    needed=[]
    for kind in (2,3):
        e=next(e for e in psx_arc(parent) if e['type']==hex(kind));needed.append((kind,e['offset'],e['size']))
    need(len(candidate)==len(parent),'ARC size changed')
    allowed=np.zeros(len(parent),bool)
    for _,offset,size in needed:allowed[offset:offset+size]=True
    delta=np.frombuffer(parent,np.uint8)!=np.frombuffer(candidate,np.uint8)
    need(not np.any(delta&~allowed),'Bytes outside exact graphics/composition spans changed')
    repro=(H/'air_pack_reproduction01/candidate_PL00_U.ARC').read_bytes();need(repro==candidate,'Reproduction differs')
    lock=json.loads((d/'LOCK.json').read_text('utf8'))
    rejects=[]
    changed=bytearray(parent);changed[-1]^=1
    try:validate_inputs(bytes(changed),d)
    except ValueError as e:rejects.append({'case':'wrong_parent_sha','reason':str(e)})
    else:raise ValueError('Wrong parent was accepted')
    tests=[('wrong_lock',d/'LOCK.json'),('wrong_manifest',d/'targets.json'),('changed_native_png',d/next(iter(lock['files']))),('changed_generation',H/next(iter(lock['accepted_generation_inputs'])))]
    for label,path in tests:
        def read(p):
            raw=p.read_bytes()
            if p==path:raw=bytes([raw[0]^1])+raw[1:]
            return raw
        try:validate_inputs(parent,d,read)
        except ValueError as e:rejects.append({'case':label,'reason':str(e)})
        else:raise ValueError('Changed input accepted: '+label)
    for label,value in [('output_escape','../outside_air_not_written'),('existing_output','air_pack_probe01')]:
        cp=subprocess.run([sys.executable,'-B',str(H/'pack_air_targets_probe.py'),'--output',value],cwd=ROOT,capture_output=True,text=True)
        need(cp.returncode!=0 and 'ValueError' in cp.stderr,'Invalid output was accepted')
        rejects.append({'case':label,'returncode':cp.returncode,'reason':cp.stderr.splitlines()[-1]})
    verification={'passed':True,'source_sha256':sha(parent),'candidate_sha256':sha(candidate),'changed_bytes':int(delta.sum()),'allowed_entries':[{'type':kind,'offset':offset,'size':size,'changed_bytes':int(delta[offset:offset+size].sum())}for kind,offset,size in needed],'bytes_outside_both_entries_exact':int((~allowed).sum()),'whole_arc_outside_entries_exact':True,'reproduction_exact':True,'reproduction_sha256':sha(repro),'rejected_input_cases':rejects,'no_input_files_modified':True,'mips_gpu_runtime_not_run_here':True}
    output.mkdir();(output/'PL00_U.ARC').write_bytes(candidate)
    old=json.loads((P.parent/'proposal.json').read_text('utf8'));proposal={**old,'replaces':str((P.parent/'proposal.json').relative_to(ROOT)).replace('\\','/'),'selected_visual_refs':list(range(33,55)),'same_display_repacked':[],'unchanged_selection_from_victory':True,'source_art_manifest':str((d/'LOCK.json').relative_to(ROOT)).replace('\\','/'),'source_art_manifest_sha256':LOCK_SHA,'parent_arc_sha256':PARENT_SHA,'scope':'基本/포스 공중 33~54: 새 원화 머리·의상·팔을 보존하고 원래 총구와 16부분아머를 유지. 이전 등장/승리/귀환/사다리/벽/저체력 누적 포함.','static_review_passed':True,'native_cpu_pending':True,'independent_review_pending':True,'actual_gameplay_pending':True}
    proposal['scope']=proposal['scope'].replace('基本','기본')
    proposal['files']={**old['files'],'PL00_U.ARC':{**old['files']['PL00_U.ARC'],'path':str((output/'PL00_U.ARC').relative_to(ROOT)).replace('\\','/'),'after':EXPECTED}}
    write(output/'proposal.json',proposal);write(output/'repro_and_rejections.json',verification)
    sources=['pack_air_targets_probe.py','prepare_air_all_targets.py','register_air_shot_arms.py','probe_air_head_ownership.py','verify_air_candidate.py','finalize_air_candidate.py']
    write(output/'INPUT_FROZEN.json',{'input_art_and_resource_frozen':True,'runtime_accepted':False,'files':{name:sha((output/name).read_bytes())for name in('PL00_U.ARC','proposal.json','repro_and_rejections.json')},'target_lock_sha256':LOCK_SHA,'producer_scripts':{name:sha((H/name).read_bytes())for name in sources},'source_art':lock['accepted_generation_inputs']})
    print(json.dumps({'proposal':str(output/'proposal.json'),'sha256':EXPECTED,'changed_bytes':verification['changed_bytes'],'outside_exact':verification['bytes_outside_both_entries_exact'],'rejected':len(rejects)},ensure_ascii=False))
if __name__=='__main__':main()
