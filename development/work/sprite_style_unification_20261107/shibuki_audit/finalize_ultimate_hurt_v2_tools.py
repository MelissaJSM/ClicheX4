"""실패한 v1을 보존하며 GPU 경계 교정 v2의 입력·재현 도구를 고정한다."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
FINAL='b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94'

def main():
    d=H/'ultimate_hurt_locked_inputs02';need(not d.exists(),'Fresh v2 lock')
    lk=json.loads((H/'ultimate_hurt_locked_inputs01/LOCK.json').read_text('utf8'))
    for n,h in lk['files'].items():need(sha((ROOT/n).read_bytes())==h,'Changed source '+n)
    lk['candidate_sha256']=FINAL
    lk['storage_correction']='111의 layer5만 원 효과 tile16의 256색인을 빈 tile31로 복제한다. 원 base tile16·효과 색·원점·모든 표시 목표는 보존한다.'
    lk['supersedes_intermediate_candidate']='8c9a83077a6973b5ea2fff46ee3273ae281bf0d0d2190db4f67dbc792ee3e3c3'
    d.mkdir();write(d/'LOCK.json',lk);lock_sha=sha((d/'LOCK.json').read_bytes())
    p=H/'pack_ultimate_hurt.py';s=p.read_text('utf8')
    s=s.replace('ultimate_hurt_locked_inputs01/LOCK.json','ultimate_hurt_locked_inputs02/LOCK.json').replace('5ea7ec757e9d5a4f0dddadce6bcefcfe50b8f4567fbf5e9fe07394eef8cf1449',lock_sha).replace(lk['supersedes_intermediate_candidate'],FINAL)
    s=s.replace("need(sha(data)==PARENT,'Wrong parent');lock=json.loads(LOCK.read_text('utf8'));need",'lock=validate(data);need')
    s=s.replace('# v2 fixed source-tile duplication probe; exact final hash bound after initial build',"need(sha(new)==FINAL,'Candidate hash differs')")
    need('lock=validate(data)'in s and "need(sha(new)==FINAL"in s,'Guard not installed');p.write_text(s,'utf8')
    p=H/'verify_ultimate_hurt_v2.py';need(not p.exists(),'Fresh verifier')
    s=(H/'verify_ultimate_hurt.py').read_text('utf8').replace('from pack_ultimate_hurt_probe import','from pack_ultimate_hurt import').replace('prepared_ultimate_hurt01','prepared_ultimate_hurt02').replace('ultimate_hurt_pack_probe01','ultimate_hurt_pack_probe02').replace('ultimate_hurt_locked_inputs01','ultimate_hurt_locked_inputs02').replace('ultimate_hurt_components.json','ultimate_hurt_v2_components.json').replace("('pack_ultimate_hurt_probe.py','verify_ultimate_hurt.py')","('pack_ultimate_hurt.py','verify_ultimate_hurt_v2.py')")
    s=s.replace("'원순서/원MIPS/실제피격은별도미검증.'", "'111 새 layer5의 U경계 실패 v1은 제외하고, 동일 원 효과 tile16을31로 복제해 v2에서 해결했다. 원 base16과 표시 픽셀은 그대로다.','원순서/원MIPS/실제피격은별도미검증.'")
    p.write_text(s,'utf8')
    print(json.dumps({'candidate':FINAL,'lock':lock_sha,'inputs':len(lk['files'])}))

if __name__=='__main__':main()
