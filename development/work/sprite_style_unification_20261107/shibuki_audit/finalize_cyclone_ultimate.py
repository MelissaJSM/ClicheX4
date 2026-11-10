"""Ultimate98·99 검토본의 재현/거부·출처를 고정한다. 실기수용은 별도."""
from pathlib import Path
import sys,json,subprocess
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,SOURCE_SHA
from pack_cyclone_ultimate import validate_inputs,LOCK_SHA
def main():
    o=H/'prepared_double_cyclone_ultimate01';need(not o.exists(),'Fresh output required');d=H/'double_cyclone_ultimate_shared01';p=H/'prepared_ultimate_wall01/PL02_U.ARC';parent=p.read_bytes();candidate=(H/'double_cyclone_ultimate_pack01/PL02_U.ARC').read_bytes();expected='dd6416c8840a1a0e5fd7ff4c73fe33b6ebd90e69b5f86f9be5f9671cc4d53c1d';need(sha(candidate)==expected,'Candidate changed');validate_inputs(parent,d);need(candidate==(H/'double_cyclone_ultimate_reproduction01/PL02_U.ARC').read_bytes(),'Reproduction changed');rejects=[];wrong=bytearray(parent);wrong[-1]^=1
    try:validate_inputs(bytes(wrong),d)
    except ValueError as e:rejects.append({'case':'wrong_parent','reason':str(e)})
    else:raise ValueError('Wrong parent accepted')
    for label,path in[('wrong_lock',d/'LOCK.json'),('changed_native',d/'before_098_indices.png'),('changed_generation',H/'double_cyclone_ultimate_costume01/generated.png')]:
        def read(p):
            raw=p.read_bytes();return bytes([raw[0]^1])+raw[1:]if p==path else raw
        try:validate_inputs(parent,d,read)
        except ValueError as e:rejects.append({'case':label,'reason':str(e)})
        else:raise ValueError('Changed source accepted')
    for label,value in[('output_escape','../outside_cyclone_not_written'),('existing_output','double_cyclone_ultimate_pack01')]:
        q=subprocess.run([sys.executable,'-B',str(H/'pack_cyclone_ultimate.py'),'--out',value],cwd=ROOT,capture_output=True,text=True);need(q.returncode!=0 and'ValueError'in q.stderr,'Invalid output accepted');rejects.append({'case':label,'reason':q.stderr.splitlines()[-1]})
    contact=H/'double_cyclone_ultimate_contact01/report.json';proof=json.loads(contact.read_text('utf8'));need(proof['passed']and proof['candidate_sha256']==expected,'Wrong contact proof');source=[]
    for form in('before','after'):
        path=d/f'{form}_098_indices.png';source.append({'form':form,'ref':98,'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes()),'ref99_translation':[1,0]})
    o.mkdir();(o/'PL02_U.ARC').write_bytes(candidate);proposal={'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL02_U.ARC':{'path':(o/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e','after':expected}},'sequential_parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(parent)},'supersedes':'prepared_ultimate_wall01; 이동3..32·벽55..66·저체력120..125의48참조 누적본에 더블 사이클론98/99 추가','selected_visual_refs':[98,99],'source_art':source,'source_art_manifest':(d/'LOCK.json').relative_to(ROOT).as_posix(),'source_art_manifest_sha256':LOCK_SHA,'scope':'새98 전신을 고정배율로 등록하고 바닥 y22에 평행정합. 새 머리/다리 공통, 전재킷·후맨팔 수영복 분리.99는 원래 x+1 관계. 게임시간표/효과/팔레트 불변.','actual_gameplay_pending':True,'native_cpu_pending':True,'independent_review_pending':True}
    write(o/'proposal.json',proposal);write(o/'verification.json',{'passed':True,'parent_sha256':sha(parent),'candidate_sha256':expected,'reproduction_exact':True,'input_rejections':rejects,'producer':json.loads((H/'double_cyclone_ultimate_pack01/report.json').read_text('utf8')),'effect_contact_cases':16,'effect_initializer_cases':8,'contact_proof':contact.relative_to(ROOT).as_posix(),'contact_proof_sha256':sha(contact.read_bytes()),'native_full_draw_pending':True,'runtime_verified':False})
    write(o/'INPUT_FROZEN.json',{'candidate_and_source_frozen':True,'files':{s:sha((o/s).read_bytes())for s in('PL02_U.ARC','proposal.json','verification.json')},'lock_sha256':LOCK_SHA,'producer_scripts':{s:sha((H/s).read_bytes())for s in('prepare_cyclone_ultimate_shared.py','pack_cyclone_ultimate.py','audit_cyclone_ultimate_contact.py','finalize_cyclone_ultimate.py')},'actual_gameplay_verified':False,'user_accepted':False});print(json.dumps({'path':str(o),'sha':expected,'rejections':len(rejects)}))
if __name__=='__main__':main()
