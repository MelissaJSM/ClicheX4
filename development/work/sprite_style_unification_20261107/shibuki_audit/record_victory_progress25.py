"""새승리4의 실제열람/정적검증과 다음귀환의 미완료 범위를 분리 기록."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
 d=H/'prepared_ultimate_victory01';review=H/'ultimate_victory_author_review01.json';need(not review.exists()and not(H/'fullform_ledger25.json').exists(),'Fresh report')
 final=[H/'ultimate_victory_pack01'/f'{form}_readback_{i:02}.png'for form in('before','after')for i in range(2)]+[H/'ultimate_victory_pack01'/f'partial_{n}.png'for n in(204,205,206,207)]+[H/'ultimate_victory_sequence01'/f'{form}_id39_ordered.png'for form in('before','after')]+[H/'ultimate_victory_sequence01/browser_id39_call023.png']
 write(review,{'candidate':ev(d/'PL02_U.ARC'),'actual_view_image_files':[ev(p)for p in final],'actual_final_plates':len(final),'observations':['204/205와206/207의 새 머릿결/금색 안경/재킷 칼라와 후폼 맨팔 구분이 실제 재독출에 남는다.','후폼204 팔꿈치와206 손목의 국소 원화를 정합한 뒤 추가 주먹 같은 단절은 현재 판에서 발견하지 못했다.','207 앞팔과 머리가 겹치는 부위는 머리공유에서 제외하여 재킷 소매가 후폼 맨팔에 복사되지 않게 했다.','206/207 발바닥과207 최고주먹은 새 모듈 강체등록으로 원좌표높이에 맞췄다.','원표39 순서판에서81→204→205→206→207의 차이는 확인했으나 실제 연속영상이나 실제게임을 시청한 결과로 확대하지 않는다.'],'limitations':['206/207 발목+1/207 최고손목−1 접점은 원화 정합 정책이며 원US 전체 몸체 복원은 아니다.','두 의상의 최종미술은 root 별도검토를 기다린다.독립reader/실기/사용자수용은 분리한다.','귀환156..158과등장135 및특수95/96은 미완료 상태 그대로이며 승리4로 전체작업 완료를 주장하지 않는다.'],'source_art_repainted_by_code':False,'actual_gameplay':False,'full_project_complete':False})
 j=json.loads((H/'fullform_ledger24.json').read_text('utf8'));j['next_generation']={'group':'Ultimate 승리4 준비본/다음귀환156..158','candidate':ev(d/'PL02_U.ARC'),'proposal':ev(d/'proposal.json'),'source_lock':ev(d/'SOURCE_LOCK.json'),'verification':ev(d/'verification.json'),'author_review':ev(review),'native':ev(H/'ultimate_victory_components_native_checks.json'),'native_scope':'실제BR18부모b43 대비선행등장8+승리4총12.승리직전3e55의비대상508raw는별도정적검사.','sequence':ev(H/'ultimate_victory_sequence01/report.json'),'browser':ev(H/'ultimate_victory_sequence01/browser_verification.json'),'status':'승리204..207 새8표시20층 패킹/재현3/거부12/원MIPS/원표39의202폼canvas검사.독립감사/루트최종미술/실기는 대기.귀환은 원자료관계만 독립조사.','frozen':False,'packed':True,'runtime_verified':False,'return_relation':ev(H.parent/'zero_audit/shibuki_ultimate_return_relations01/report.json')}
 for r in j['references']:
  if r['form'].startswith('ultimate')and r['ref']in(204,205,206,207):r['candidate_progress']=j['next_generation'];r['decision']='새 승리4 원화·공통층·20층패킹·재현·원MIPS·원순서 정적 검토.독립/루트수용 전이므로동결완료로세지 않음.'
 j['counts_unchanged_from24']=True;j['frozen_counts_note']='현재동결표시/고유키수는ledger24·unique_art_keys24 기준.승리후보8표시는 아직더하지않음.';j['full_art_unification_complete']=False;write(H/'fullform_ledger25.json',j);print(json.dumps({'ledger':ev(H/'fullform_ledger25.json'),'review':ev(review)}))
if __name__=='__main__':main()
