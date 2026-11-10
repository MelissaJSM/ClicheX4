"""검토 결과를 UTF-8 파일로 기록. PowerShell stdin 인코딩을 경유하지 않는다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import TASK,OUT,write,relative,sha

for char in('shibuki','nana'):
 p=OUT/char/'findings.json';m=json.loads(p.read_text('utf8'));v=m['actual_visual_review']
 v['method']='view_image로 실제 시트 열람. bbox 차이만으로 결함을 판정하지 않음.'
 for r in v['main_forms'].values():r['viewing_scale']='원본 도트의 정수 2배 확대; 개별 문제는 4배 확대 확인'
 v['fourth_arm1']='237개 RGBA 해시가 개별 열람한 포스 arm2와 모두 동일. 별도의 육안 검토를 했다고 주장하지 않음.'
 v['capsule_palette']='인덱스 확인용 중성 팔레트. 실제 게임의 변화하는 잔상 CLUT 색상을 재현한 것이 아님.'
 v['note']='일부 원래 동작군 시트를 별도로 열지 않았으나, 그 안의 유효 본체 참조는 remaining_review에서 모두 확인했다. 부분 아머의 대부분 시트는 정적 수집·합성만 완료했다.'
 m['unverified']=['이번 전수 시각 검토와 준비 자원의 새 에뮬레이터 재생 검증은 수행하지 않았다.','부분 아머는16마스크·2팔모드 전수 추출했지만, 개별 육안 열람은 arm2의 대기0 시트만 했다.','105,175..182의 독립 복원 불가 참조를 예외로 유지했다. 미교체 그림으로 판정하지 않았다.','보조 그래픽 뱅크1..9의 본체 표시 소비 경로는 미확정이다.','고정 마스크 시트에는 실제 피격 CLUT 번쩍임과 등장 중 아머 표시 전환이 재현되지 않는다.']
 m['preserve_by_default']=['몸 숙임·원근·등 방향·귀와 베일의 정상적인 크기 차이.','184..203은 라이드 아머 탑승 머리이므로 몸체가 작아진 것으로 판정하지 않는다.','노바·호버 효과 및 캡슐 잔상을 본체 체형의 결함으로 판단하지 않는다.','이 정적 시각 검토에서 나머지 본체 동작의 새 명백한 불일치는 발견하지 않았다.']
 for r in m['findings']:
  i=r['id']
  if i=='NANA_PARTIAL_IDLE_VEIL_OWNERSHIP':
   r['forms']=['포스: 다리 파츠 있음/머리 파츠 없음의 부분 조합'];r['evidence']='world(11,-14),(11,-13) 및 호흡에 따른 대응점은 머리 윤곽인데 다리 뱅크8에 저장되어 있었다. 풀아머에서는 정상 윤곽이지만 다리만 장착하면 고립된 점으로 드러난다.';r['fix']='2~3픽셀의 소유권만 다리8에서 머리5로 이전. 기본형·풀아머 픽셀 동일. 저장 UI의 머리45/다리48도 같은 원리로 교정.';r['proposal']='work/sprite_consistency_20261105/x/nana_parts_fix/prepared_v2/proposal.json';r['gpu_fix']='최초 준비본의 tile16 col0 위험을 수정: col1 패딩+partx-1로 월드 픽셀 동일. v2만 사용. 7,296마스크·새 U/V 경계·7종 거부 검사 및 독립 검사 통과.'
  elif i=='NANA_ULTIMATE_AFTER_142_IDLE':
   r['evidence']='등장 animation2는142를33틱 유지한 후 terminal 단계에서 대기로 전환한다. 획득 후142는 idle0과234픽셀이 달랐다. 획득 전142는 이미 idle0과 동일했다.'
  elif i=='SHIBUKI_SPECIAL_TONE':
   r['status']='confirmed_style_inconsistency_prepared_fix';r['evidence']='특수 자세 얼굴·몸의 음영이 수용된 대기보다 넓게 단순화되어 있었다. 독립 담당이 이전 full_detail 도트를 복원했고 최종 PL00에 의미 단위로 순차 합성했다.'
  elif i=='SHIBUKI_142_IDLE':
   r['evidence']='등장 animation2의 마지막142가 대기로 연결된다. 기본 PL00는 이미 동일하나 포스는452픽셀, PL02의 전후 폼은513픽셀 차이가 있었다. 현재 각폼 대기0 참조로 연결했고 원화·팔레트·압축본문·타이밍은 유지했다.';r['integration']='독립 prepared PL00를 병합하지 말고 마지막141까지 포함한 최종2ARC proposal을 사용한다.'
  elif i=='SHIBUKI_FOURTH_LADDER183':
   r['status']='confirmed_registration_defect_prepared_fix';r['evidence']='실제 animation28/29의183에 기본 흰·붉은 소매와 몸통이 남았다. 포스143 및 대기의 검정·금색 의상과 이어지지 않았다. 원점이나 숙인 자세 자체가 결함인 것은 아니다.';r['cause']='기존 master183은 정상. 목96/허리108 등록으로 옷 영역이 잘려 있었다. 목84/허리98로 등록을 복구했고 기본형·머리·머리카락·손·실루엣을 보존했다.'
  elif i=='SHIBUKI_141_TRANSITION_HISTORY':
   r['status']='confirmed_style_inconsistency_prepared_fix';r['modified']=True;r['evidence']='work/sprite_consistency_20261105/x/arrival141_history/report.json';r['rule']='원작141은 양주먹을 든 별도 자세였다. 현재 수용된 Shibuki 기본형은 이미 idle0+12잔광이므로, 그 규칙을 포스 및 Ultimate 전후에 통일했다. 126..140 등장 동작은 그대로이다.'
  if char=='shibuki':r['final_proposal']='work/sprite_consistency_20261105/x/arrival141_history/prepared_v1/proposal.json'
 if char=='shibuki':m['actual_visual_review']['additional_focused_reviews']=['work/sprite_consistency_20261105/x/ladder183_review.png','work/sprite_consistency_20261105/x/ladder183_source_layers.png','work/sprite_consistency_20261105/x/arrival141_history/comparison.png','work/sprite_consistency_20261105/x/arrival141_history/prepared_v1/comparison.png']
 m['scope_note']='본 파일은 고정된 최초 수집 BIN의 전수 검토와 교정 준비 결과이다. 후속 통합 BIN의 실제 실행·사용자 수용은 부모 문서에서 별도로 기록한다.'
 write(p,m)

d=TASK/'arrival141_history';old=(d/'SLUS_005.61').read_bytes();new=(TASK/'shibuki/SLUS_005.61').read_bytes();start=0x80031410-0x80010000+2048;end=start+0x130
report={'original_bin':'MegaMan X4.bin','original_sha256':'3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',
 'original_141_role':'양팔 주먹을 든 별도 준비자세. 141에는 바깥 잔광, 142에는 잔광이 없다. 원작 idle0과 다른 그림이다.',
 'current_shibuki_PL00_base_141':'수용된 기본형은 idle0 몸체와 동일하고 바깥 잔광12픽셀만 추가된다.',
 'current_shibuki_PL02_jacket_141':'과거 production_fix04와 화면0픽셀 차이. 외형 교환에서 새로 생긴 손상이 아니다.',
 'historical_registration':{'file':'scripts/register_shibuki_ultimate_production.py','art':'work/ver_buki_riko/shibuki_art/ultimate_v1/production_layers03/art.json','master':85,'neck':75,'hip':87,'cx':77,'pixels':464,'note':'서서 사격하는 master85 의상을141/142에 매핑했다. 넓은 옷 덩어리가 현재 대기와 달랐다.'},
 'swimsuit_141':'C03 stage_vehicle_00에서 생성. 기존 재킷 full 보존 조건에 맞추어 같은 이전 실루엣과 연결되었다.',
 'native_player_beam_in':{'start':'0x80031410','end_exclusive':'0x80031540','current_code_original_exact':old[start:end]==new[start:end],'code_sha256':sha(old[start:end]),'source':'work/research/decomp/src/main/player.c:125..157'},
 'native_sequence2_final':[{'ref':141,'ticks':3},{'ref':142,'ticks':33},{'ref':142,'step':0,'exit':'player_enter_idle'}],
 'adopted_correction':'현재 수용된 PL00 기본형의 idle몸체+12잔광 규칙을 포스·Ultimate 전후에 적용. 새로운 앞선 등장 동작126..140을 삭제하지 않는다. 원작141이 처음부터 idle이었던 것으로 해석하지 않는다.',
 'proof':'각 ARC 1,140인덱스 레이어, 32부분마스크, 508/512압축참조, 새 GPU U/V 경계 검사. PL00기본141 원시 타일·조립·픽셀 보존. PL02공유 조립은141 header만 독립 변경하여138 및 다른 참조 보존.',
 'final_proposal':'work/sprite_consistency_20261105/x/arrival141_history/prepared_v1/proposal.json','runtime_verified':False,'comparison':relative(d/'comparison.png')}
write(d/'report.json',report)
print('UTF-8 Korean findings and 141 history written')
