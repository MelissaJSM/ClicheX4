"""새32 가역 시험 자원의 재현/잘못된 입력 거부를 검사하고 준비본을 고정."""
from pathlib import Path
import json,sys,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_base_run_relocated import build,validate,P,PARENT,D,TARGET_LOCK,SLOCK,STORAGE,STORAGE_LOCK_SHA
FINAL='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'
def main():
    o=H/'prepared_base_run01';need(not o.exists(),'Fresh prepared output');probe=H/'base_run_complete_pack06';source=P.read_bytes();candidate=(probe/'PL00_U.ARC').read_bytes();need(sha(candidate)==FINAL,'Candidate changed');repros=[]
    for i in range(2):
        result,report=build(source);need(result==candidate,'Reproduction mismatch');repros.append(sha(result));print(json.dumps({'reproduction':i+1,'sha256':sha(result)}),flush=True)
    rejected=[]
    def reject(name,data,reader):
        try:validate(data,reader)
        except(ValueError,json.JSONDecodeError)as e:rejected.append({'case':name,'rejected':True,'reason':str(e)});return
        raise ValueError('Bad input accepted '+name)
    normal=lambda p:p.read_bytes();bad=bytearray(source);bad[100]^=1;reject('wrong_parent',bytes(bad),normal);reject('truncated_parent',source[:-1],normal)
    for p in[D/'LOCK.json',D/'targets.json',D/'002_bank0_indices.png',SLOCK,*[H/n for n in STORAGE],H/'base_run_standing02_registered03/fourth_002_registered_arm_indices.png']:
        def reader(q,p=p):
            raw=normal(q)
            return bytes([raw[0]^1])+raw[1:]if q==p else raw
        reject('changed_'+p.relative_to(H).as_posix(),source,reader)
    need(sha(P.read_bytes())==PARENT,'Parent modified');o.mkdir()
    for p in probe.glob('*.png'):shutil.copyfile(p,o/p.name)
    shutil.copyfile(probe/'PL00_U.ARC',o/'PL00_U.ARC');proof=json.loads((probe/'report.json').read_text('utf8'));proof.update(reproduction_sha256=repros,total_identical_builds=3,rejected_inputs=rejected,rejection_count=len(rejected),source_parent_preserved=True,independent_reader_pending=True,native_cpu_pending=True,root_art_review_pending=True)
    write(o/'verification.json',proof)
    prev=json.loads((H/'prepared_dash_base01/proposal.json').read_text('utf8'))
    proposal={'project':'ver_buki_riko','baseline_sha256':prev['baseline_sha256'],'files':{'PL00_U.ARC':{'path':(o/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':prev['files']['PL00_U.ARC']['before'],'after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'selected_refs':list(range(1,33)),'target_manifest':(D/'targets.json').relative_to(ROOT).as_posix(),'target_lock_sha256':TARGET_LOCK,'storage_lock_sha256':STORAGE_LOCK_SHA,'source_files':json.loads((D/'targets.json').read_text('utf8'))['source_files'],'scope':'기본/포스 이동·사격32. ref1은 기존idle0 재사용,ref2 새팔+기존idle몸,3..32 새몸/새팔.0/141/142 불변.','graphics_directory_change':{'entry_length_unchanged':186228,'bank0_growth':proof['bank0_growth'],'tail_trims':proof['capsule_tail_trims'],'bank12_13_absolute_bytes_unchanged':True,'other_bank_raw_count_and_compressed_body_preserved':True,'reason':'원화 전체160층을 줄이지 않고 고정 entry2 안에 넣는 가역 시험. root 판단으로허용,사용자의새주소직접승인주장아님.'},'palette_audio_exe_lba_unchanged':True,'native_cpu_pending':True,'runtime_verified':False,'frozen':False}
    write(o/'proposal.json',proposal);write(o/'PREPARED_LOCK.json',{'candidate_assets_fixed':True,'files':{p.name:sha(p.read_bytes())for p in sorted(o.iterdir())if p.is_file()},'source_scripts':{n:sha((H/n).read_bytes())for n in('pack_base_run_relocated.py','verify_base_run_relocated.py')},'input_storage_lock':STORAGE_LOCK_SHA,'approval_scope':'독립/원MIPS/미술 검토 대기. 현재게임 미적용.'});print(json.dumps({'prepared':str(o),'sha256':FINAL,'rejections':len(rejected),'reproductions':3}))
if __name__=='__main__':main()
