"""작은머리 실제열람/원표 바이트 읽기를 고정후보와 결속한다."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.c01_audio_build import read_disc
FINAL='a0629d169d6b5a0d88f31faa5dc4866c7fef99245b278caedc92f523acb3f024'
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    d=H/'prepared_vehicle_head_ultimate01';need(not(d/'post_lock_evidence.json').exists(),'추가 근거 보호');need(sha((d/'PL02_U.ARC').read_bytes())==FINAL,'후보 변경')
    names=['before_readback_00.png','before_readback_01.png','after_readback_00.png','after_readback_01.png','ownership_184.png','ownership_196.png'];views=[d/n for n in names]+[H/'vehicle_head_ultimate_native01/comparison.png',H/'vehicle_head_ultimate_native02/comparison.png'];write(d/'author_visual_review.json',{'actually_viewed':True,'candidate_sha256':FINAL,'images':[ev(p) for p in views],'actual_images':8,'findings':['최종19위치×전후 재추출4판에서 새고글과 머릿결이13×15 머리에 남으며 갑자기 늘어난 귀/머리 크기는 보이지 않는다.','184/196 부분16조합2판의 공통고글/눈과 측면머리색이 유지되며 새 부유 파편이나 잘린얼굴은 발견하지 못했다.','첫 최근접팔레트와 금색표본등록2판을 직접 비교했다. 금색5셀 등록은실제원화 색계열을기존색인7로선택하며 새화소/팔레트추가없음.','귀사이 계단에서 이전외곽1추가/1제거가 있고13×15크기/눈/머리 원점은같다. 완전동일외곽 주장은하지않는다.'],'new_confirmed_defect':False,'limits':['실제 차량/조종석과의 가림은 이 정적판에 없으며 게임실기를 수행하지 않았다.','현재19동일머리는 수용Shibuki 제작정책이다. 원US5~6고유머리 복원을 뜻하지 않는다.','전체 미술 수용과 독립검사는 별도다.'],'root_review_pending':True,'independent_pending':True,'runtime_verified':False})
    mp=ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json';meta=json.loads(mp.read_text('utf8'));seq=[r for r in meta['animations'] if any(184<=q['frame']<=203 for q in r['steps'])];bp=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v30/shibuki_riko.bin';ce=read_disc(bp,('SLUS_005.61',))[0]['SLUS_005.61'];oe=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61',))[0]['SLUS_005.61'];off=lambda x:x-0x80010000+2048
    for r in seq:
        at=off(int(meta['table_address'],16))+r['id']*4;need(ce[at:at+4]==oe[at:at+4] and struct.unpack_from('<I',ce,at)[0]==int(r['address'],16),'원표 포인터')
        for q in r['steps']:
            at=off(int(q['address'],16));need(ce[at:at+4]==oe[at:at+4] and ce[at:at+4].hex()==q['bytes'],'원표 스텝')
    write(d/'original_sequence_read.json',{'scope':'실제 원US/BR30 EXE의 작은머리 소비표 포인터와4바이트 스텝 직접읽기. 재생/원caller실행 아님.','candidate_sha256':FINAL,'original_EXE_sha256':sha(oe),'current_EXE_sha256':sha(ce),'metadata':ev(mp),'animation_ids':[r['id'] for r in seq],'table_count':len(seq),'step_count':sum(len(r['steps']) for r in seq),'all_pointer_step_bytes_exact':True,'sequences':seq,'changes_to_EXE':False,'limits':['96호출 self-loop는 외부상태 변경전 유지이고 전체차량동작 시간으로세지않음.','현재 Shibuki19동일머리 위치별칭을 유지한새제작정책. 원US고유크롭5~6차이를복원했다고세지않음.','실제 차량/배경·카메라·입력·가림·좌우반전의 게임실기는별도.'],'runtime_verified':False})
    evs=[d/'author_visual_review.json',d/'original_sequence_read.json',H/'vehicle_head_ultimate_components.json',H/'vehicle_head_ultimate_components_native_checks.json',Path(__file__)]
    write(d/'post_lock_evidence.json',{'candidate_sha256':FINAL,'evidence':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in evs},'candidate_unchanged':True,'new_runtime_execution':False});print(json.dumps({'author':sha((d/'author_visual_review.json').read_bytes()),'original_table_count':len(seq),'original_steps':sum(len(r['steps']) for r in seq),'native':sha((H/'vehicle_head_ultimate_components_native_checks.json').read_bytes()),'post':sha((d/'post_lock_evidence.json').read_bytes())}))
if __name__=='__main__':main()
