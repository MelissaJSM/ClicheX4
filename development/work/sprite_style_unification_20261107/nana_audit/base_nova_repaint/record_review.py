"""실제열람한동일후보 비교판과 최종검증 출처를 구분한다."""
from pack_candidate import *
def main():
 p=D/'packed_nova_candidate_v1';probe=D/'packed_nova_probe_v5';need(digest(p/'PL00_U.ARC')==digest(probe/'PL00_U.ARC'),'열람후보 동일')
 viewed=[D/f'dash_layers_probe_v1/{n}.png'for n in('body_comparison','effects_comparison','partial')]+[D/f'preparation_effect_probe_v2/{n}.png'for n in('comparison','partial')]+[probe/f'readback_{i}.png'for i in range(1,4)]+[D/f'native_cycle_v1/timeline_106_{i}.png'for i in range(1,5)]
 matches=[]
 for i in range(1,4):
  source=probe/f'readback_{i}.png';final=p/f'readback_{i}.png';need(digest(source)==digest(final),'최종판 바이트동일');matches.append({'actually_viewed':source.relative_to(ROOT).as_posix(),'final_same_bytes':final.relative_to(ROOT).as_posix(),'sha256':digest(final)})
 write(p/'producer_visual_review.json',{'candidate_sha256':digest(p/'PL00_U.ARC'),'actually_viewed_files':[{'path':f.relative_to(ROOT).as_posix(),'sha256':digest(f),'actually_viewed':True}for f in viewed],'final_images_exact_matches':matches,'observations':['새213/215의 머릿결·옷 주름·높은 주먹과 포스 맨다리·치맛단을 대기와 비교했다. 새 손목·발목에서 확정된 분리는 찾지 못했다.','큰 뒤베일의 소유를 기존16px head창 밖 leg8로 정리한 뒤에도 전체 기본/포스 그림은 동일하다. 부분 조합의 앞모자와 뒤베일을 나눈 정책을 확인했다.','217 접힌 두 신발과 팔의 자세가 유지되며220 효과의 새머리/발 부분에 확정절단은 보이지 않는다.','원표213→215→216→214→217 및218/219/220 순서에서 새몸의 급격한 크기변화는 보이지 않는다.'],'limits':['정지판 직접열람과 브라우저48canvas 기계재생 검사는 실제게임·CLUT 시간변화·물리/판정 실행이 아니다.','214 원외부124효과와220 새몸가림/구멍복원은 기존전체원효과 raw 불변 주장과 구분한다.','최종 독립reader와루트수용은 별도로결속한다.'],'runtime_verified':False})
 v=json.loads((p/'verification.json').read_text('utf8'));write(p/'proposal.json',{'project':'ver_rin_nana','baseline_sha256':'e765577ac65cff3348a76ab0d2719ea96471b2c7895a35ac5a3c428db87385b3','parent_arc_sha256':BEFORE,'files':{'PL00_U.ARC':{'path':(p/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':BEFORE,'after':v['after'],'parent_arc_sha256':BEFORE}},'new_unique_body_keys':[213,215,217],'new_source_cells':6,'changed_refs':list(REFS),'preserved_energy_refs':[218,219]});print(json.dumps({'viewed_files':len(viewed),'proposal':digest(p/'proposal.json')}))
if __name__=='__main__':main()
