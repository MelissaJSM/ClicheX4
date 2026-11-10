"""시부키 전 폼의 실제 열람·수정·보존·잔여 범위를 분리한다. 게임 쓰기 없음."""
from pathlib import Path
import json, hashlib, sys
from collections import Counter
H=Path(__file__).resolve().parent
ROOT=H.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,GROUPS

def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(p.read_text('utf8'))
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def span(a,b):return list(range(a,b+1))

REVIEW_AGAIN=[
'ultimate_before/nova_hover_00.png','ultimate_after/nova_hover_00.png',
'ultimate_before/ride_chaser_00.png','ultimate_after/ride_chaser_00.png',
'ultimate_before/shoot_special_00.png','ultimate_after/shoot_special_00.png',
'ultimate_before/shoot_special_01.png','ultimate_after/shoot_special_01.png',
'base/nova_hover_00.png','fourth/nova_hover_00.png','base/ride_chaser_00.png','fourth/ride_armor_00.png',
'ultimate_after/hurt_lowhp_00.png','ultimate_before/ladder_00.png','ultimate_after/arrival_00.png','ultimate_before/victory_teleport_00.png',
'base/air_00.png','fourth/dash_00.png','base/shoot_special_00.png','fourth/hurt_lowhp_00.png',
'base/run_00.png','fourth/run_00.png','ultimate_before/wall_00.png','ultimate_after/ride_armor_00.png']

COMMON_NOTES={
'run':('머리·옷 재검토','3~32의 머리 옆면이 대기보다 넓은 연보라 면으로 남고 소매/허리 접힘이 적다. 보폭·다리 교차를 결함으로 판정하지 않는다. 사격짝 총구 고정 필요.'),
'air':('공중 상체 재작화 필요','33~54·93/94에서 뒷머리 큰 단색면, 얼굴/칼라·소매 주름 감소가 보인다. 정상적인 무릎 굽힘·회전과 분리하며 손/총구·착지 축 보존.'),
'dash':('대시 머리·옷 세부묘사 필요','67~84의 귀 사이·뒷머리와 상의가 대기보다 단순하다. 71~76의 낮은 몸높이는 정상 대시 자세다. 속도선·뒤팔·발 접점 보존.'),
'shoot_special':('특수 본체/효과 분리','88~96·98~104·231/232의 옆/뒤 얼굴과 상의가 단순하다. 특히100/101·231/232는 얼굴과 머리의 큰 밝은 면이 남는다. 85~87·97은 대기와 가까운 세부묘사를 보존하고, 효과 전용208~212는 재작화로 세지 않는다.'),
'hurt_lowhp':('피격 몸체 후속','106/108·110 및233/234의 눈감김/입 표현은 피격 의미를 유지한다. 110의 뒷머리·가슴은 대기보다 단순하며 기본/포스120~125는 이번 새 저체력으로 해결했다. 107/111/235/236 외부 번개는 몸체 수정 시 그대로 보존.'),
'arrival':('등장 본체·실루엣 동기화','126~129·132는 에너지 전용. 130/131/134는 본체에 의존하는 빛. 140은 현 대기 알파,141은 대기+잔광,142는 대기이므로 보존. 기본/포스133~139는 새 후보에 포함.'),
'ride_chaser':('체이서 자세의 머리/소매 보강 필요','162~174의 얼굴 옆면이 작은 밝은 덩어리이고 뒷머리·팔/소매 구조가 대기보다 적다. 앉은 하체를 서 있는 체형으로 늘리지 않는다. 핸들·좌석 접점과174의 별도 자세 유지.'),
'ride_armor':('탑승 전용 머리 보존 조건부','184~203은 탑승물 위에 놓이는 작은 머리 자원이다. 몸통이 없는 것을 누락으로 세지 않는다. 귀·눈과 방향은 읽히므로 우선 유지하되, Ultimate 이마 장식 생략은 같은 픽셀 영역에서 보완 가능한지 별도 확인. 확대/전신 추가 금지.'),
'nova_hover':('아머 기술·호버 상세화 필요','213~216의 머리/얼굴·상의,221~230의 옆/정면 머리·가슴과 소매가 대기보다 단순하다.217~220은 실제 몸/효과 합성 구분 후 처리한다. 발과 추진 불꽃 위치·사격 총구·에너지 외곽을 보존한다.'),
}
ULT_EXTRA={
'shoot_special':('특수·정지사격 양의상 상세화 필요','85~104·231/232의 머리 옆면·이마 장식·칼라/가슴 정보가 수용 대기보다 줄었다.85~87/97도 기본/포스와 달리 Ultimate 재킷/수영복 별도 검토에 남긴다.208~212 단색 잔상은 연결 몸체 변화 여부만 검사한다.'),
'run':('새 양폼 이동/사격 동결','3~32 두 의상의 새 머리·칼라·소매·맨팔과 원래 배럴을 정합한 complete03으로 해결. 1/2는 수용된 기존 그림 유지.'),
'wall':('벽 양폼 재작화 필요','55~66의 머리 옆면과 재킷 가슴/소매가 큰 단색면이다. 기본/포스 새 벽은 의상이 달라 그대로 덮을 수 없다. 원래 벽 손/발 및 총구 보존.'),
'hurt_lowhp':('독립 PL02 다음 우선군','120~125는 대기보다 좁고 길게 보이는 머리/상체, 빠진 이마 장식·칼라가 뚜렷하다. 두 폼을 같은 체형으로 새로 제작하고 여섯 호흡 프레임에 같은 변환을 적용한다. 피격106~114·233~236은 별도 후속.'),
'ladder':('뒷머리·뒤 의상 재작화 필요','143~155·183에서144~153 뒷머리 큰 연보라 면과 단순한 등/소매가 두드러진다. 정상 뒤통수 방향은 유지하고 머릿결 중간톤·재킷 접힘을 복원.150/155 사격과 손/발 접점은 별도 보호.'),
'victory_teleport':('정면 재작화·광선 동기화 필요','156~158의 평평한 얼굴·머리와 재킷 큰 흰면/수영복 몸통이 대기보다 단순하다. 새 정면 하나를157 외곽빛·158 광선 몸체에 연결.159~161의 몸 없는 광선은 보존.'),
'other_action':('승리 네 자세 재작화 필요','204~207의 정면/측면 머리와 재킷 소매가 단순하고 선글라스/칼라 정보가 줄어든다. 손 최고점·접지를 보존해 양폼 제작. 기본/포스 신규 승리와 혼동하지 않는다.'),
'arrival':('Ultimate 등장 별도 남음','133/135/137/138의 양의상 얼굴·앞머리/칼라가 단순하다.136/139와130/131/134 몸체 실루엣을 같이 동기화. 기본/포스 신규 등장 적용으로 Ultimate까지 해결되지 않는다.140~142 대기 연결은 이미 일치하여 보존.'),
}

def main():
 manifest=load(H/'source_manifest.json');f=load(H/'findings.json');root=load(H/'root_visual_review.json')
 current={'PL00_U.ARC':H/'prepared_arrival_victory01/PL00_U.ARC','PL02_U.ARC':H/'prepared_run_complete03/PL02_U.ARC'}
 expected={'PL00_U.ARC':'78b329a07d888682c24b440386cb365f826572402346b3ee6620216ce951617e','PL02_U.ARC':'c7eb1c7998a6780d04f4397a64af653265e3d83985c3c05768dd3de46eae5265'}
 arcs={n:Archive(p.read_bytes()) for n,p in current.items()}
 assert all(sha(current[n].read_bytes())==v for n,v in expected.items())
 main_sheets={q['form']+'/'+Path(q['path']).name for q in manifest['sheets']}
 reviewed=set(root['actual_view_image_files'])|set(f['reviewed_current_images'])
 assert main_sheets<=reviewed and len(main_sheets)==64
 valid={(q['form'],q['ref']):q for q in manifest['frames']}
 fixed=set(span(55,66)+span(120,125)+[130,131]+span(133,139)+span(143,158)+[183]+span(204,207))
 assert len(fixed)==48
 groups={r:g for g,refs in GROUPS.items() for r in refs}
 assert len(groups)==237
 allrows=[];grouprows=[]
 for form,file,mask in manifest['forms']:
  ult=form.startswith('ultimate');a=arcs[file]
  for group,refs in GROUPS.items():
   for r in refs:
    row={'form':form,'ref':r,'group':group,'source_gallery':valid.get((form,r),{}).get('path'),'structural_decode':(form,r) in valid}
    if not row['structural_decode']:
     row.update(status='reserved_or_unrenderable',decision='기존 자료의 빈/예약 참조. 가짜 몸체를 채우지 않는다.')
    else:
     effective_mask=15 if ult and r in span(217,230) else mask
     im,_=a.composite(r,effective_mask)
     row.update(effective_render_mask=effective_mask,current_rgba_sha256=sha(im.tobytes()),opaque_pixels=sum(v>0 for v in im.getchannel('A').getdata()))
     previous=valid[(form,r)]['rgba_sha256'];changed=row['current_rgba_sha256']!=previous
     frozen=not ult and r in fixed or ult and r in span(3,32)
     if frozen:
      row.update(status='new_art_frozen_for_integration',decision='새 원화/파생 레이어 등록 및 정적 검증 완료. 전체 게임 실기와 별개.',proposal='prepared_run_complete03/proposal.json' if ult else 'prepared_arrival_victory01/proposal.json')
     else:
      assert not changed,(form,r,'unexpected art delta')
      if r in [0,1,2]+span(115,119)+span(140,142) or not ult and r in [85,86,87,97]:
       row.update(status='preserve_accepted_detail',decision='현 수용 대기 또는 대기와 가까운 머리/옷 묘사와 연결을 보존. 새 몸체 전체복사 불필요.')
      elif r in [109,112,113,114]+span(126,129)+[132]+span(159,161)+span(208,212) or not ult and r in [218,219]:
       row.update(status='preserve_effect_check_body_dependency',decision='단색/광선/피격 전용 효과를 저밀도 본체로 오판하지 않는다. 연결 몸체가 바뀌면 고정 외부 효과 보존하에 실루엣만 검토.')
      elif r in span(184,203):
       row.update(status='preserve_vehicle_head_pending_accessory_check',decision=COMMON_NOTES['ride_armor'][1])
      else:
       note=(ULT_EXTRA if ult else {}).get(group,COMMON_NOTES.get(group,('잔여 본체 검토','미술 상세화 범위를 별도 확인한다.')))
       row.update(status='art_rework_group_pending',decision=note[1])
     row['changed_from_reviewed_parent']=changed
     if r in span(213,230):
      row['reachability_limit']='정적 자원 폼 비교다. 무아머/캡슐 전의 해당 능력 사용 가능을 증명하지 않는다.217~230 표시 예외와 실제 소유 능력은 분리한다.'
    allrows.append(row)
   rs=[q for q in allrows if q['form']==form and q['group']==group]
   note=(ULT_EXTRA if ult else {}).get(group,COMMON_NOTES.get(group,('준비/보존 판단','개별 참조 상태를 따른다.')))
   grouprows.append({'form':form,'group':group,'refs':refs,'status_counts':dict(Counter(q['status'] for q in rs)),'focus':note[0],'observation':note[1], 'reviewed_baseline_sheets':sorted(x for x in main_sheets if x.startswith(form+'/'+group+'_'))})
 assert len(allrows)==948 and sum(q['structural_decode'] for q in allrows)==912
 counts=Counter(q['status'] for q in allrows)
 frozenrows=[q for q in allrows if q['status']=='new_art_frozen_for_integration']
 assert len(frozenrows)==156
 ledger={'scope':'Shibuki 기본/포스/Ultimate 획득 전 재킷·획득 후 수영복 전 참조','source_bin_sha256':manifest['sha256'],
 'current_candidates':{n:{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':expected[n]}for n,p in current.items()},
 'review_basis':{'baseline_main_sheets_actually_viewed':64,'this_agent_original':19,'root_original':45,'additional_rechecked_this_turn':REVIEW_AGAIN,'all_baseline_sheets_covered':True,'all_partial_combinations_individually_viewed':False,'not_runtime_video':True},
 'counts':{'reference_form_slots':948,'decoded_form_images':912,'reserved_form_slots':36,'new_frozen_form_images':156,'status_counts':dict(counts),'pending_meaning':'동작군 수준의 후속 상세화/공유 파생 검토 대상 수. 모두 독립 원화가 필요하거나 모든 픽셀이 결함이라는 뜻이 아니다.'},
 'partial_armor':{'all_16_masks_and_two_arms_static_regression':'각 준비본 verification에 포함. 선택한 새48참조는 부모별 회귀와 누적보존으로 보호. 전237참조×32조합을 모두 눈으로 봤다는 뜻은 아니다.',
 'actually_viewed_targeted_partial_refs':span(55,66)+[120]+span(143,155)+[183]+span(204,207)+[138,139],
 'not_all_partial_poses_aesthetically_final':True,'capacity_head5_bytes':4,'capacity_arm7_bytes':24,'capacity_policy':'픽셀 생략·옛 몸 덮기로 맞추지 않는다. 후속 새 PL00 레이어는 무손실 공유/공간계획 먼저.'},
 'ui_and_capsule':[
 {'asset':'선택 ST0E bank2 18..21','status':'synchronized_frozen','decision':'새 게임207/156/157/158을 원래 좌표변환으로 무손실 동기화. 전체25개 중 나머지21개의 표시/조립 의미 보존.'},
 {'asset':'선택 작은0..17,22..24','status':'reviewed_preserve_dependency','decision':'이전 선택 전체 시트 실제 열람. 대기·이동 등의 사본은 연관 본체를 향후 바꾸면 별도 바인딩 검사 후 동기화. 현재새18..21과 혼동하지 않는다.'},
 {'asset':'저장/불러오기 기본/16부분/Ultimate전후','status':'preserve_accepted_idle_copy','decision':'이전 save_sheet34조합 실제열람. 현재 대기 기준 사본이므로 새 그림 필요 근거 없음. 현재 저장자원 미변경.'},
 {'asset':'캡슐 4banks48잔상','status':'preserve_existing_alpha_binding','decision':'이전 native 캡슐 조사에서 획득후 몸체idle0와 정합. 이번 대기를 보존하므로 자동재작화하지 않는다. 이번64주요시트는 캡슐48개 추가육안검사를 포함하지 않는다.'}],
 'priority_next':[{'rank':1,'forms':['ultimate_before','ultimate_after'],'refs':span(120,125),'why':'독립 PL02·작은6호흡군. 대기 대비 좁은 몸/거친 머리를 양폼에서 함께 해결.'},
 {'rank':2,'forms':['ultimate_before','ultimate_after'],'refs':span(55,66)+span(143,158)+[183]+span(204,207),'why':'벽/사다리/정면/승리의 큰 단색머리·재킷면. 몸 접점과 총구·광선 별도보호.'},
 {'rank':3,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':span(33,54)+[93,94]+span(67,84)+span(162,174)+span(213,230),'why':'공중·대시·체이서·아머 기술/호버를 누락하지 않음. PL00남은공간과실제상태별표시를먼저계획.'}],
 'groups':grouprows,'references':allrows,'full_art_unification_complete':False,'new_candidate_emulator_test':False,
 'unverified':['모든 잔여 본체의 새 미술 제작','모든237참조×부분마스크의 개별 육안 수용','새 등장누적본 실제 MIPS/GPU와 게임플레이','모든 희귀 동작 실기 접점·전환']}
 write(H/'fullform_ledger01.json',ledger)
 f['whole_form_ledger']='fullform_ledger01.json';f['full_art_unification_complete']=False
 f['whole_form_ledger_counts']=ledger['counts']
 f['victory_working_candidate']['superseded_by']='prepared_arrival_victory01/proposal.json'
 f['victory_working_candidate']['historical_record_only']=True
 write(H/'findings.json',f)
 lines=['# 시부키 전 폼 잔여 작업 장부','','이 문서는 검토 누락과 수정 완료를 구분한다. 64개 기존 주요 시트는 실제 열람했고 이번24개를 다시 대기와 비교했다. 원래 한 장에 보이는 정상적인 회전·굽힘이나 단색 이펙트를 미술 결함으로 세지 않는다.','','현재 동결 그림: PL00 48참조×기본/포스, PL02 30참조×재킷/수영복 =156폼별 그림. 전체912개 복원 그림의 미술 통일 완료가 아니다.','','| 폼 | 군 | 새 그림 동결 | 후속 미술 대상 | 보존/효과/예약 |','|---|---|---:|---:|---:|']
 for q in grouprows:
  c=q['status_counts'];n=c.get('new_art_frozen_for_integration',0);p=c.get('art_rework_group_pending',0)
  lines.append(f"| {q['form']} | {q['group']} | {n} | {p} | {len(q['refs'])-n-p} |")
 lines+=['','## 구체적인 잔여 관찰','']
 for form in ('base','fourth','ultimate_before','ultimate_after'):
  lines.extend(['### '+form,''])
  for q in grouprows:
   if q['form']==form and q['status_counts'].get('art_rework_group_pending'):
    rr=[str(r['ref']) for r in allrows if r['form']==form and r['group']==q['group'] and r['status']=='art_rework_group_pending']
    lines.append('- '+q['group']+' `'+','.join(rr)+'`: '+q['observation'])
  lines.append('')
 lines+=['## 보존 판단과 미확인','','- 대기0/115~119, 이미 대기와 연결되는140~142, 시작1/2 및 기본/포스의85~87/97은 새 그림 필요 근거보다 보존 근거가 크다. 새로 안 그렸다고 누락으로 세지 않는다.','- 184~203 작은 머리는 라이드 아머 합성용이다. 전신 부재는 정상이며, Ultimate 장식 누락은 작은 영역 안에서의 별도 후보다.','- 에너지126~129/132/159~161와208~212, 피격109/112~114는 본체 디테일 평가에서 분리한다. 연관 본체를 바꿀 때 실루엣 동기화 여부는 다시 검사한다.','- Ultimate217~230의 같은 그림은 표시 마스크15 예외 때문이다. 무아머·캡슐 전 능력이 실제 사용 가능하다는 의미가 아니다.','- 부분아머 새 프레임들은16mask×팔1/2 회귀를 통과했으나, 모든 옛 참조의 모든 조합을 개별 육안 수용한 것은 아니다. head5 여유4B/arm7 여유24B이므로 다음 PL00 파츠 추가에는 무손실 공유/공간계획이 필요하다.','- 선택18~21 새 사본 동기화 완료. 전체25개 중 나머지21개는 보존되었고 향후 원본 모션 변경 시 별도 동기화한다. 저장 그림은 수용된 대기 사본이므로 현 상태를 유지한다.','- 캡슐48개는 이전 idle0 정합조사 근거로 유지한다. 이번64시트 육안검토 개수에 캡슐48을 추가로 세지 않았다.','- 새 후보의 연속 WEBP는 그림 순서 검토이며 실제 게임 플레이가 아니다.','','다음 우선은 독립 PL02 저체력120~125 양폼이다. 이후 벽·사다리·정면/승리, 공중·대시·특수·호버·체이서를 빠뜨리지 않고 순차 진행한다.']
 (H/'FULLFORM_LEDGER.md').write_text('\n'.join(lines)+'\n','utf8')
 print(json.dumps(ledger['counts'],ensure_ascii=False))
if __name__=='__main__':main()
