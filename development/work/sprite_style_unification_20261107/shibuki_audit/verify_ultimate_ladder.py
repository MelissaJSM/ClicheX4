"""사다리14 후보를 재현하고 입력 거부·GPU경계·출처를 검토용 패키지로 고정."""
from pathlib import Path
import sys,json,shutil,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,SOURCE_SHA
from pack_ultimate_ladder import build,validate,P,PARENT,D,LOCK,PARTS,REFS
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import decode_stream,indexed_atlas
FINAL='03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a'
def main():
    o=H/'prepared_ultimate_ladder01';need(not o.exists(),'Fresh candidate only');old=P.read_bytes();probe=H/'ultimate_ladder_pack01';new=(probe/'PL02_U.ARC').read_bytes();need(sha(new)==FINAL,'Candidate changed');runs=[]
    for _ in range(2):r,p=build(old);need(r==new,'Nondeterministic pack');runs.append(sha(r))
    tests=[];normal=lambda p:(H/p).read_bytes()
    def reject(name,data,read):
        try:validate(data,read)
        except ValueError as e:tests.append({'test':name,'rejected':True,'reason':str(e)});return
        raise ValueError('Bad input accepted '+name)
    mut=bytearray(old);mut[100]^=1;reject('wrong_parent',bytes(mut),normal);reject('truncated_parent',old[:-1],normal)
    for name in ['ultimate_ladder_complete_targets01/LOCK.json','ultimate_ladder_complete_targets01/targets.json','ultimate_ladder_complete_targets01/155_bank0_indices.png','ultimate_ladder_shot_inputs01/generated.png','ultimate_ladder151_arm_composed01/before_151_indices.png','register_ultimate_ladder_shots.py']:
        def reader(p,name=name):
            v=normal(p);return bytes([v[0]^1])+v[1:]if p==name else v
        reject('changed_'+name,old,reader)
    arc=Archive(new);gpu=0
    for n in REFS:
        f=arc.banks[0]['frames'][n];need(f['tile_count']==32,'Tile count');raw=decode_stream(arc.g,f['offset'],f['limit'],4096).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
        for b in PARTS:
            for fl,t,x,y in struct.iter_unpack('<BBbb',records(arc.c,b,n)):
                need(t<32,'Tile overflow');tx,ty=t%16*16,t//16*16
                if t%16==0:need(not atlas[ty:ty+16,tx].any(),'U boundary')
                if fl&128 and ty==0:need(not atlas[ty,tx:tx+16].any(),'V boundary')
                gpu+=1
    need(sha(P.read_bytes())==PARENT,'Parent mutated');o.mkdir()
    for p in sorted(probe.glob('*.png')):shutil.copyfile(p,o/p.name)
    shutil.copyfile(probe/'PL02_U.ARC',o/'PL02_U.ARC');proof=json.loads((probe/'report.json').read_text('utf8'));proof.update({'reproduced_sha256':runs,'total_reproducible_runs_including_initial':3,'rejection_count':len(tests),'rejection_cases':tests,'gpu_part_checks':gpu,'actual_readback_art_review':{'agent':'overhaul_ui','sheets':[f'{form}_readback_{i:02}.png'for form in('before','after')for i in range(3)],'viewed':True,'observation':'재추출6판에서 새 머릿결·후면·소매/맨팔과 팔뿌리 연결을 확인. 추가 확정 분리 못 찾음. 실제 사다리 발판 접촉과155 원전신 반동은 검증 주장에서 제외.','gameplay_claim':False},'independent_reader_pending':True,'root_final_packed_review_pending':True});write(o/'verification.json',proof)
    meta=json.loads((D/'targets.json').read_text('utf8'));write(o/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL02_U.ARC':{'path':(o/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e','after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'targets':(D/'targets.json').relative_to(ROOT).as_posix(),'target_lock_sha256':LOCK,'source_art':meta['sources'],'selected_refs':list(REFS),'scope':'새 Ultimate 사다리14의 전후28표시. 원32타일/은행경계/팔레트/효과/시간표 보존. 원US155 전신반동복원이 아닌 수용기본형 공통몸체+팔반동 정책.','foot_contact_caveat':proof['foot_contact_caveat'],'runtime_verified':False,'native_cpu_pending':True,'frozen':False})
    write(o/'PREPARED_LOCK.json',{'candidate_assets_fixed':True,'final_approval_pending':True,'files':{p.name:sha(p.read_bytes())for p in sorted(o.iterdir())if p.is_file()},'source_scripts':{n:sha((H/n).read_bytes())for n in ['prepare_ultimate_ladder_targets.py','pack_ultimate_ladder.py','verify_ultimate_ladder.py']}});print(json.dumps({'after':FINAL,'reproductions':len(runs)+1,'rejections':len(tests),'gpu_parts':gpu,'proposal_sha256':sha((o/'proposal.json').read_bytes())}))
if __name__=='__main__':main()
