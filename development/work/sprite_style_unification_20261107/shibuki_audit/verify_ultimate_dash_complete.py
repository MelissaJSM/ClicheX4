"""신 Ultimate20 준비본 재현/입력 거부 및 GPU 경계 증거를 고정한다."""
from pathlib import Path
import sys,json,shutil,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,SOURCE_SHA
from pack_ultimate_dash_complete import build,validate_inputs,P,PARENT,D,LOCK,PARTS
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import decode_stream,indexed_atlas
FINAL='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb'

def main():
    o=H/'prepared_ultimate_dash01';need(not o.exists(),'Fresh candidate only');old=P.read_bytes();probe=H/'ultimate_dash_pack_probe01';new=(probe/'PL02_U.ARC').read_bytes();need(sha(new)==FINAL,'Readback candidate changed');runs=[]
    for _ in range(2):r,p=build(old);need(r==new,'Non-deterministic repacking');runs.append(sha(r))
    tests=[]
    def reject(name,data,read):
        try:validate_inputs(data,read)
        except ValueError as e:tests.append({'test':name,'rejected':True,'reason':str(e)});return
        raise ValueError('Invalid input accepted '+name)
    normal=lambda p:(H/p).read_bytes();mut=bytearray(old);mut[100]^=1;reject('wrong_parent',bytes(mut),normal);reject('truncated_parent',old[:-1],normal)
    for name in ['ultimate_dash_complete_targets01/LOCK.json','ultimate_dash_complete_targets01/targets.json','ultimate_dash_complete_targets01/082_bank0_indices.png','ultimate_dash_shot_inputs01/page04/generated.png','ultimate_dash_contacts05/before_093_indices.png','register_ultimate_dash_shot_probe.py']:
        def reader(p,name=name):
            v=normal(p)
            return bytes([v[0]^1])+v[1:]if p==name else v
        reject('changed_'+name,old,reader)
    arc=Archive(new);meta=json.loads((D/'targets.json').read_text('utf8'));gpu=0
    for row in meta['rows']:
        n=row['ref'];f=arc.banks[0]['frames'][n];need(f['tile_count']==32,'Tile count changed');raw=decode_stream(arc.g,f['offset'],f['limit'],4096).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
        for b in PARTS:
            for fl,t,x,y in struct.iter_unpack('<BBbb',records(arc.c,b,n)):
                need(0<=t<32 and -128<=x<=127 and -128<=y<=127,'Native part overflow');tx,ty=t%16*16,t//16*16
                if t%16==0:need(not atlas[ty:ty+16,tx].any(),'GPU U underflow')
                if fl&128 and ty==0:need(not atlas[ty,tx:tx+16].any(),'GPU V underflow')
                gpu+=1
    need(sha(P.read_bytes())==PARENT,'Parent mutated');o.mkdir()
    for p in sorted(probe.glob('*.png')):shutil.copyfile(p,o/p.name)
    shutil.copyfile(probe/'PL02_U.ARC',o/'PL02_U.ARC');proof=json.loads((probe/'report.json').read_text('utf8'));proof.update({'reproduced_sha256':runs,'total_reproducible_runs_including_initial':3,'rejection_count':len(tests),'rejection_cases':tests,'gpu_part_checks':gpu,'source_inputs':len(json.loads((D/'LOCK.json').read_text('utf8'))['sources']),'actual_readback_art_review':{'agent':'overhaul_ui','sheets':[f'{form}_readback_{i:02}.png'for form in('before','after')for i in range(4)],'viewed':True,'observation':'대기 옆에서8판을 실제 열람. 새 머릿결·선글라스·칼라·맨팔과 발목 연결 확인.82는 원총구가 얼굴 앞에 가까우며 접힌 팔/손을 원위치 배럴 아래로 유지. 원작 속도선은새그림이아님.','gameplay_claim':False},'independent_reader_pending':True,'root_review_pending':True});write(o/'verification.json',proof)
    write(o/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL02_U.ARC':{'path':(o/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e','after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'targets':(D/'targets.json').relative_to(ROOT).as_posix(),'target_lock_sha256':LOCK,'source_art':json.loads((D/'targets.json').read_text('utf8'))['sources'],'selected_refs':sorted(r['ref']for r in meta['rows']),'scope':'기존 새Ultimate공중22와이동/벽/저체력/Rising을보존하고대시20참조의양의상40표시추가','runtime_verified':False,'native_cpu_pending':True,'frozen':False})
    write(o/'PREPARED_LOCK.json',{'candidate_assets_fixed':True,'final_approval_pending':True,'files':{p.name:sha(p.read_bytes())for p in sorted(o.iterdir())if p.is_file()},'source_scripts':{n:sha((H/n).read_bytes())for n in ['prepare_ultimate_dash_targets.py','pack_ultimate_dash_complete.py','verify_ultimate_dash_complete.py']}});print(json.dumps({'after':FINAL,'reproductions':len(runs)+1,'rejections':len(tests),'gpu_parts':gpu,'proposal_sha256':sha((o/'proposal.json').read_bytes())}))
if __name__=='__main__':main()
