"""작은 머리19 재현/거부 검증과 준비본 잠금. 동결은 독립/미술 후 별도."""
from pathlib import Path
import json,sys,shutil,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_vehicle_head_ultimate import build,validate,P,PARENT,TD,MANIFEST,REFS
FINAL='a0629d169d6b5a0d88f31faa5dc4866c7fef99245b278caedc92f523acb3f024'
def main():
    d=H/'prepared_vehicle_head_ultimate01';need(not d.exists(),'기존 준비본 보호');s=H/'vehicle_head_ultimate_pack01';candidate=(s/'PL02_U.ARC').read_bytes();need(sha(candidate)==FINAL,'후보 변경');source=P.read_bytes();repros=[]
    for i in range(2):
        result,proof=build(source);need(result==candidate,'재현 실패');repros.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
    normal=lambda p:p.read_bytes();rejected=[]
    def reject(name,data,reader):
        try:validate(data,reader)
        except (ValueError,json.JSONDecodeError,OSError) as ex:rejected.append({'case':name,'reason':str(ex),'rejected':True});return
        raise ValueError('변조 입력 수용 '+name)
    bad=bytearray(source);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',source[:-1],normal)
    paths=[TD/'manifest.json',TD/'184_bank0_indices.png',TD/'203_bank5_indices.png',TD/'196_bank8_indices.png',H/'vehicle_head_ultimate_inputs01/generated_v1.png',H/'vehicle_head_ultimate_inputs01/prompt.txt',H/'vehicle_head_ultimate_native02/registration.json',H/'register_vehicle_head_gold.py',H/'prepare_vehicle_head_targets.py']
    for p in paths:
        def reader(q,p=p):
            blob=normal(q);return bytes([blob[0]^1])+blob[1:] if q.resolve()==p.resolve() else blob
        reject('changed_'+p.relative_to(H).as_posix(),source,reader)
    need(sha(P.read_bytes())==PARENT,'부모 변경');d.mkdir()
    for p in s.glob('*.png'):shutil.copy2(p,d/p.name)
    shutil.copy2(s/'PL02_U.ARC',d/'PL02_U.ARC');proof.update(total_identical_builds=3,reproduction_sha256=repros,rejected_inputs=rejected,rejected_count=len(rejected),source_parent_preserved=True);write(d/'verification.json',proof)
    meta=json.loads((TD/'manifest.json').read_text('utf8'));files=dict(meta['source_files'])
    for p in TD.iterdir():
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    deps=['pack_vehicle_head_ultimate.py','verify_vehicle_head_ultimate.py','native_pose_pack.py','pack_shibuki_hurt.py','pack_dash_complete.py','prepare_lowhp_final.py']
    for name in deps:p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in ('scripts/export_x_consistency.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','src/psx_player.py','src/psx_compress.py'):files[name]=sha((ROOT/name).read_bytes())
    write(d/'INPUT_LOCK.json',{'parent_sha256':PARENT,'candidate_sha256':FINAL,'target_manifest_sha256':MANIFEST,'refs':list(REFS),'files':files,'all_inputs_fixed':True});locksha=sha((d/'INPUT_LOCK.json').read_bytes());previous=json.loads((H/'prepared_hover_ultimate01/proposal.json').read_text('utf8'))
    write(d/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':previous['baseline_sha256'],'files':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':previous['files']['PL02_U.ARC']['before'],'after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'selected_refs':list(REFS),'target_manifest':(TD/'manifest.json').relative_to(ROOT).as_posix(),'target_manifest_sha256':MANIFEST,'target_lock':(d/'INPUT_LOCK.json').relative_to(ROOT).as_posix(),'target_lock_sha256':locksha,'scope':'Ultimate 차량 작은머리1셀을19원위치별칭으로 등록. 새13×15/144px·눈/원점 동일, 내부고글/머릿결. 기존빈678 기록57개와198 원시/조립/빈표시 보존.95목표층 중38새소유층,608부분,512raw/493비대상·1045층/1753기타조립·95GPU·모든은행경계 보존.','limits':['귀사이 계단의1픽셀추가/1픽셀제거를 기록하며 외곽exact라고 주장하지 않는다.','고글10금색표본은 기존색인7로 의미등록했으며 최근접양자화 대비5셀이다.','before 측면머리9기존소유창 중8셀만파랑4, 새고글1셀은공통. 대기와기본/포스머리자원은수정하지않는다.','원차량실제조종석·탑승이벤트·머리좌우반전·게임실기는별도.'],'native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,'runtime_verified':False,'frozen':False})
    write(d/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes()) for p in sorted(d.iterdir()) if p.is_file()},'source_scripts':{name:sha((H/name).read_bytes()) for name in deps},'target_lock_sha256':locksha,'candidate_assets_fixed':True})
    binpath=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v30/shibuki_riko.bin';hh=hashlib.sha256()
    with binpath.open('rb') as f:
        for block in iter(lambda:f.read(8388608),b''):hh.update(block)
    write(H/'vehicle_head_ultimate_components.json',{'project':'ver_buki_riko','source_bin':binpath.relative_to(ROOT).as_posix(),'source_sha256':hh.hexdigest(),'resources':{'PL02_U.ARC':{'path':(d/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},'checkpoint_only':True,'scope_note':'Ultimate 작은머리19 원디코더/업로드/GPU 검사. 실제게임/전체디렉터리검사와 구분.'})
    print(json.dumps({'candidate':FINAL,'input_lock':locksha,'input_files':len(files),'rejects':len(rejected),'proposal':sha((d/'proposal.json').read_bytes()),'prepared_lock':sha((d/'PREPARED_LOCK.json').read_bytes()),'native_source_bin_sha256':hh.hexdigest()}))
if __name__=='__main__':main()
