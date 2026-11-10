"""실제 열람 및 8참조 준비 진척을 기록. 동결 전 완료 수는 늘리지 않는다."""
from pathlib import Path
import sys,json,copy
from PIL import Image
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
 out=H/'ultimate_arrival_author_review01.json';need(not out.exists(),'Fresh author record')
 pack=H/'ultimate_arrival_pack02';prep=H/'prepared_ultimate_arrival_partial01';seq=H/'ultimate_arrival_sequence01';common=H/'ultimate_arrival_common_probe03'
 packed=[pack/f'{form}_readback_{i:02}.png'for form in('before','after')for i in range(3)];partial=[pack/f'partial_{n}.png'for n in(133,136,138,139)];ordered=[seq/f'{form}_id{aid}_ordered.png'for form in('before','after')for aid in(2,95,96)];commons=[common/f'{form}_comparison_{i:02}.png'for form in('before','after')for i in range(3)]
 write(out,{'candidate':ev(prep/'PL02_U.ARC'),'actually_viewed':{'final_packed_sheets':[ev(p)for p in packed],'partial_sheets':[ev(p)for p in partial],'native_order_sheets':[ev(p)for p in ordered],'final_common_sheets':[ev(p)for p in commons]},'observations':['133의 낮은 진입 자세에서 새 머릿결/선글라스/소매·맨팔이 남고 빛구체 내부 몸체도 동일한 새133이다.','136은 상부 관절을 유지한 발 모듈 정합 후 양발 접지가 부모 높이로 돌아왔다. 새 번개는 원46픽셀과 앞뒤 순서를 유지한다.','138/139 후폼의 흰 소매는 국소 원화의 맨팔·팔꿈치로 교정됐으며 머리/몸통과 별개로 붙은 추가 손은 이 판에서 찾지 못했다.','부분조합에서는 기존 Ultimate 규칙대로 layer5 선택이 두 의상을 바꾼다. 다른 세 파츠층은 빈칸을 유지하며 체형이 분리되지 않는다.','원표2의135는 부모 구형으로 남아 새133/136 사이에서 세부 묘사 차이가 보인다. 미완료 참조로 유지하며 이번 후보에 재작화 완료라고 세지 않는다.','공유 원표95/96의138/139 뒤에 이어지는 구형95/96은 큰 단색 머리/의상 면이 남는다. 새8참조의 패킹 결함과 별개인 기존 재작화 잔여다.'],'foot_preview_note':'ultimate_arrival136_foot_contacts01/comparison.png는 after 줄도 before idle을 쓰는 옛 비교판이다. 최종 common_probe03와 pack02의 양폼별 idle이 정확한 검토 기준이다.','native_sequence':ev(seq/'report.json'),'browser':ev(seq/'browser_verification.json'),'runtime_performed':False,'continuous_video_watched':False,'user_final_accepted':False,'root_final_review_pending':True,'independent_pending':True})
 j=json.loads((H/'fullform_ledger22.json').read_text('utf8'));u=json.loads((H/'unique_art_keys22.json').read_text('utf8'));refs=[130,131,133,134,136,137,138,139]
 evidence={k:ev(p)for k,p in{'proposal':prep/'proposal.json','lock':prep/'SOURCE_LOCK.json','verification':prep/'verification.json','native':H/'ultimate_arrival_partial_components_native_checks.json','author_review':out,'sequence':seq/'report.json','browser':seq/'browser_verification.json'}.items()}
 j['next_generation']={'group':'Ultimate 등장8 부분 후보','selected_refs':refs,'new_body_keys':[133,136,137,138,139],'new_body_form_images':10,'packed_form_displays':16,'packed':True,'frozen':False,'integrated':False,'status':'새8참조 패킹·재현3·거부12·원MIPS/GPU·원표2/95/96 canvas406 통과. 독립 reader/루트 최종검토 대기.135는 부모 보존 미완료.','evidence':evidence,'blocked_ref135':ev(H/'ultimate_arrival135_arms01/generation_failure.json'),'corrected_ref138139':'흰 소매 반려 후 별도 새 국소 원화c33bd8ff로 맨팔·팔꿈치 수정.135거부 편집과 다른 자세이며135는 건드리지 않았다.','foot136':'새 발모듈 강체 y+1만 적용. 눈/무릎/상부 종아리 exact.','protected_refs':[0,115,116,117,118,119,126,127,128,129,132,135,140,141,142]}
 for r in j['references']:
  if r['form']in('ultimate_before','ultimate_after')and r['ref']in refs:r['candidate_progress']={'state':'packed_native_passed_independent_pending','ref':r['ref'],'evidence':evidence,'frozen':False,'integrated':False}
  elif r['form']in('ultimate_before','ultimate_after')and r['ref']==135:r['candidate_progress']={'state':'parent_preserved_incomplete','reason':'국소 편집 거부 후 재시도하지 않음. 새8참조에 포함하지 않는다.','blocked_edit':ev(H/'ultimate_arrival135_arms01/generation_failure.json')}
 j['counts_unchanged_from22']=True;j['pending_related_old_frames']=[95,96,135];write(H/'fullform_ledger23.json',j);u['source_ledger']=ev(H/'fullform_ledger23.json');u['unfinished_arrival_progress']=j['next_generation'];u['counts_unchanged_from22']=True;write(H/'unique_art_keys23.json',u)
 print(json.dumps({'author_review':ev(out),'ledger':ev(H/'fullform_ledger23.json'),'unique':ev(H/'unique_art_keys23.json')}))
if __name__=='__main__':main()
