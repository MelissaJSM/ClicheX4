"""새 피격13의 세 번째 재현과 입력 거부를 수행하고 검토용 ARC를 고정."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,SOURCE_SHA
from pack_shibuki_hurt import build,validate_inputs,LOCK,LOCK_SHA,TD,REFS,PARENT
FINAL='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b'

def main():
    out=H/'prepared_hurt_base01';need(not out.exists(),'Fresh prepared output')
    parent=H/'prepared_base_run01/PL00_U.ARC';old=parent.read_bytes();probe=H/'hurt_pack_probe06';candidate=(probe/'PL00_U.ARC').read_bytes()
    need(sha(candidate)==FINAL,'Candidate changed');rep=(H/'hurt_pack_reproduction01/PL00_U.ARC').read_bytes();need(rep==candidate,'First reproduction differs')
    rebuilt,proof=build(old,lambda row:None);need(rebuilt==candidate,'Second reproduction differs')
    tests=[]
    def reject(name,data,read=lambda p:p.read_bytes()):
        try:validate_inputs(data,read)
        except ValueError as e:tests.append({'test':name,'rejected':True,'reason':str(e)});return
        raise ValueError('Invalid input accepted: '+name)
    bad=bytearray(old);bad[100]^=1;reject('wrong_parent',bytes(bad));reject('truncated_parent',old[:-1])
    names=['hurt_locked_inputs01/LOCK.json','hurt_locked_inputs01/tile_recipe.json','hurt_effect_probe01/manifest.json','hurt_effect_probe01/235_bank0_indices.png','hurt_common_probe02/233_bank5_indices.png','hurt_inputs01/page01/generated.png','hurt_inputs01/page02/generated.png','hurt_inputs01/page02/prompt.txt','probe_shibuki_hurt_common.py','prepare_shibuki_hurt_effects.py']
    for name in names:
        selected=(H/name).resolve()
        def reader(p,selected=selected):
            data=p.read_bytes();return bytes([data[0]^1])+data[1:]if p.resolve()==selected else data
        reject('changed_'+name,old,reader)
    need(sha(parent.read_bytes())==PARENT,'Parent mutated')
    effect=json.loads((TD/'manifest.json').read_text('utf8'));common=json.loads((H/'hurt_common_probe02/report.json').read_text('utf8'))
    boundary=[p for r in common['rows']for p in r['boundary_registered']]
    proof.update({'reproduction_runs':3,'reproduced_sha256':[FINAL]*3,'rejection_count':len(tests),'rejection_cases':tests,'new_native_body_keys':[106,110,233,234],'generated_pages':2,'registered_costume_images':8,'boundary_material_registrations':len(boundary),'boundary_registration_detail':boundary,'effect_policies':effect['records'],'actual_art_review':{'agent':'overhaul_ui','view_image_readback_sheets':[f'{form}_readback_{i:02}.png'for form in('base','fourth')for i in range(4)],'observation':'새 머리 내부 명암·옷깃·소매·부츠 세부가 재추출에도 유지되고 현재8판에서 새 팔/몸체/발목의 확정 분리를 찾지 못했다. 원효과와 새몸의 가림 순서는 정적 합성으로 확인했다.','gameplay_claim':False},'independent_reader_pending':True,'root_final_packed_review_pending':True,'aura_colour_policy_pending_root_review':True,'limitations':['109는 원PL00과 같은 기본106 실루엣이며 포스 전용 실루엣이 아니다.','112..114는 실제 부모의 CLUT2 규칙과 외부효과로 새110을 표현하며, 새몸의 작은 성분을 삭제하지 않았다.','235/236은 원시부키 제작식 백색/청색 오라 뒤에 새234를 그린다. 옛 포스 의상조각 및 외부 오라 재색상은 복사하지 않은 수정 후보이다.','233 기본 머리/귀 외곽은 이전보다 상단1px·좌우각1px 넓어졌고 발바닥 높이는 유지했다. 전신 리사이즈는 없다.','새몸/오라가 실제 피격 연속 화면에서 보이는 모습은 아직 검증하지 않았다.']})
    out.mkdir();(out/'PL00_U.ARC').write_bytes(candidate)
    for f in sorted(probe.glob('*_readback_*.png')):shutil.copyfile(f,out/f.name)
    write(out/'verification.json',proof)
    proposal={'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':'b6a4f2a5a321e8c37575e6593c3b86f396151c16a16690e16054c86e75f3fd59','after':FINAL}},'sequential_parent':{'path':parent.relative_to(ROOT).as_posix(),'sha256':PARENT},'targets':(TD/'manifest.json').relative_to(ROOT).as_posix(),'target_lock':LOCK.relative_to(ROOT).as_posix(),'target_lock_sha256':LOCK_SHA,'source_art':json.loads(LOCK.read_text('utf8'))['files'],'selected_refs':list(REFS),'scope':'기본/포스 피격13, 새4몸체×2의상 및 원효과 분리. 고정은행 내 원효과 슬롯과 도트 보존, 공동몸체/전체타일 순열로 손실 없이 패킹.','runtime_verified':False,'native_cpu_pending':True,'frozen':False}
    write(out/'proposal.json',proposal)
    write(out/'PREPARED_LOCK.json',{'candidate_assets_fixed':True,'final_approval_pending':True,'files':{f.name:sha(f.read_bytes())for f in sorted(out.iterdir())if f.is_file()},'source_scripts':{name:sha((H/name).read_bytes())for name in('pack_shibuki_hurt.py','verify_shibuki_hurt.py','optimize_hurt_tile_storage.py')}})
    plan={'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin','source_sha256':SOURCE_SHA,'resources':proposal['files'],'checkpoint_only':True}
    write(H/'hurt_base_components.json',plan)
    print(json.dumps({'candidate':FINAL,'reproductions':3,'rejections':len(tests),'proposal_sha256':sha((out/'proposal.json').read_bytes()),'prepared_lock_sha256':sha((out/'PREPARED_LOCK.json').read_bytes()),'boundary_samples':len(boundary)}))
if __name__=='__main__':main()
