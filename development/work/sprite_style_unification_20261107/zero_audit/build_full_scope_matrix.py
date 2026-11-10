"""Read existing evidence; produce a scope table, never mutate game/art sources."""
import collections
import copy
import hashlib
import html
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / 'work/sprite_style_unification_20261107'
D = B / 'zero_audit'
OUT = D / 'full_scope_matrix01'
OUT.mkdir(exist_ok=True)

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def relative(p):
    return p.relative_to(ROOT).as_posix()

def compact(values):
    values = sorted(set(values))
    if not values or isinstance(values[0], str):
        return ', '.join(values)
    chunks = []
    start = last = values[0]
    for n in values[1:] + [values[-1] + 2]:
        if n != last + 1:
            chunks.append(str(start) if start == last else f'{start}..{last}')
            start = n
        last = n
    return ', '.join(chunks)

evidence = {}
def ev(key, rel, purpose):
    p = B / rel
    assert p.is_file(), p
    evidence[key] = {'path': relative(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'purpose': purpose}
    return key

ev('br14', 'staging_br_v14.json', '현재 시부키/리코 통합 계획; 새 미패킹 원화와 구분')
ev('rn15', 'staging_rn_v15.json', '현재 나나/린 통합 계획')
ev('rn16', 'staging_rn_v16.json', '라이징 기본/포스7 추가 통합; 나머지 나나/린 자원은 RN15 유지')
ev('shibuki_ledger', 'shibuki_audit/fullform_ledger14.json', '4폼948참조 분류와 기존/추가 실제 열람 기록; 이동32 용량 대기 분리')
ev('shibuki_base', 'shibuki_audit/prepared_dash_base01/FROZEN.json', '누적 PL00 동결·기술·미술 근거')
ev('shibuki_ultimate', 'shibuki_audit/prepared_ultimate_dash01/FROZEN.json', '누적 PL02 동결·기술·미술 근거')
ev('shibuki_run_candidate', 'shibuki_audit/base_run_complete_targets01/LOCK.json', '새 이동32 목표160층; 고정은행 용량 문제로 미패킹')
ev('nana_ledger', 'nana_audit/scope_summary_v8/manifest.json', '최신 수정 상태; 기존 분류를 상속하고 이동32·Rising7 동결을 갱신')
ev('nana_decisions', 'nana_audit/scope_summary_v5/manifest.json', '참조별 보존/재검토/재작화 판단. 원화/후보 최신성은 별도 덮어쓰기')
ev('nana_old_views', 'nana_audit/remaining_review_v1/review.json', '제작자 실제 모션판 열람 목록. 이후 원화까지 재열람했다는 뜻 아님')
ev('nana_base', 'nana_audit/dash_repaint/packed_dash_candidate_v1/FROZEN.json', '현재 기본/포스 누적 후보 동결')
ev('nana_ultimate', 'nana_audit/ultimate_run_repaint/packed_run_candidate_v1/FROZEN.json', '현재 얼티밋 누적 후보 동결')
ev('nana_rising', 'nana_audit/rising_repaint/packed_base_candidate_v1/proposal.json', '기본/포스 라이징7 후보 원화·패킹 근거; RN16에 통합')
ev('nana_rising_frozen', 'nana_audit/rising_repaint/packed_base_candidate_v1/FROZEN.json', '독립/루트65·66/원MIPS 결속 동결; 현재 RN16 통합')
ev('nana_rising_runtime', 'runtime/nana_rising16_summary.json', '포스352/기본176 실제캡처20판. 포스 새7·기본4 업로드확인, 비동기 미확정0. 부분 전조합 실기 아님')
ev('nana_rising_runtime_views', 'root_review_checkpoint68.json', 'RN16 기본/포스 실제캡처20판 루트 열람')
ev('nana_rising_reader', 'zero_audit/nana_rising7_independent01/report.json', '별도 reader/실제 재독출3판·부분3판 열람; 실기 아님')
ev('nana_rising_art', 'root_review_checkpoint66.json', '루트 후보 원순서/미술 검토')
ev('nana_ultimate_rising_source', 'nana_audit/rising_repaint/ultimate_air_v1/generated.png', '얼티밋103/104 새 원화만; 등록/패킹과 구분')
ev('nana_ultimate_rising_registered', 'nana_audit/rising_repaint/ultimate_costume_pair_probe_v4/registration.json', '100..104/231 양의상12표시 정합 중간안; ARC 미패킹·232 파생은 별도')
ev('nana_arrival', 'zero_audit/nana_arrival_endpoint_audit01/report.json', '133..137 재킷층 존재/기존 원화 동일; 의상 가독성 후보')
ev('riko_views', 'riko/all_unique_review_v8/inventory.json', '최신313몸체/머리·216형태24판 루트 실제 열람')
ev('riko_patch', 'riko/prepared_ground_boots_v13/proposal.json', '누적 최신 Riko 원화/등록/별도 정적 몸체 근거')
ev('rin_ledger', 'zero_audit/rin_extension/progress_ledger.json', '최신303·수용 대기/정적효과·대표 실기 분리 장부')
ev('rin_views', 'zero_audit/rin_extension/all_unique_review303/visual_review.json', '436표시/319형태 일반29·레드29 실제 열람')
ev('rin_patch', 'zero_audit/rin_extension/prepared_burst_remaining02/FROZEN.json', '최신303 누적 동결')
ev('zero_groups', 'zero_audit/group_map.json', 'Zero 동작별 실제 몸체/머리·별도 효과·부분VRAM 분류')
ev('zero_endpoints', 'zero_audit/final_endpoint_audit01/report.json', '현재 BIN의 선택32/저장/정적효과 바인딩 및 별도 HQ·잔기·대사')
ev('zero_endpoint_views', 'root_review_checkpoint62.json', '루트 HQ/잔기/대사/끝점 총8판 실제 열람')
ev('x_endpoints', 'zero_audit/x_endpoint_supplement01/report.json', 'BR14/RN15 HQ·대사·잔기·pause84표시/8판 실제 열람; RN16은 별도 사본 변경 없음')
ev('x_endpoint_views', 'root_review_checkpoint69.json', '루트 X 별도 사본8판 실제 열람·용도별 수용 디자인 보존 판단')
for key, filename in [('rin_normal_runtime','rin_checkpoint15_summary.json'),('rin_red_runtime','red_rin15_summary.json'),('riko_normal_runtime','riko_allboss_summary.json'),('riko_black_runtime','riko_black_checkpoint12_summary.json'),('nana_runtime','nana_ultimate_run14_summary.json'),('shibuki_runtime','shibuki_ultimate_dash14_summary.json'),('shibuki_selection','shibuki_selection14_summary.json'),('zero_selection','selection_checkpoint13_summary.json')]:
    ev(key, 'runtime/' + filename, '대표 실제 실행 범위·미검증 사건. 전폼/전모션 실기 완료가 아님')

CATEGORIES = {
 'idle':'대기', 'run':'보행·이동사격', 'air':'공중', 'wall':'벽', 'dash':'대시',
 'hurt':'피격·저체력', 'ladder':'사다리', 'special':'공격·특수', 'ride':'차량',
 'ceremony':'등장·승리·귀환', 'ui':'선택·저장', 'hq':'HQ·대사·잔기 별도그림'}
FORMS = {'base':'기본','fourth':'포스','ultimate_before':'얼티밋 캡슐 전 재킷','ultimate_after':'얼티밋 획득 후 수영복','normal':'일반','black':'블랙'}
XREFS = {
 'idle':[0,*range(115,120)],'run':list(range(1,33)),'air':list(range(33,55)),
 'wall':list(range(55,67)),'dash':[*range(67,85),93,94],
 'hurt':[*range(106,115),*range(120,126),*range(233,237)],
 'ladder':[*range(143,156),183],
 'special':[*range(85,93),*range(95,105),*range(208,233)],
 'ride':[*range(162,175),*range(184,204)],
 'ceremony':[*range(126,143),*range(156,162),*range(204,208)]}
RESERVED = [105,*range(175,183)]
assert sorted(sum(XREFS.values(), []) + RESERVED) == list(range(237))

LABELS = {
 'integrated_new_art':'새 원화 동결·현재 통합',
 'preserve_reviewed':'기존 세부 보존 판단',
 'needs_redraw':'재작화 대상·미착수',
 'review_before_decision':'보존/수정 판단 추가 필요',
 'effect_only':'효과 보존·몸체 의존 확인',
 'reachability_review_required':'사용 경로·몸체/효과 분류 필요',
 'candidate_unpacked':'새 원화·등록 후보, 미패킹',
 'candidate_ready':'패킹·독립/미술검토 동결 후보, 현재 BIN 미통합',
 'source_only':'새 원화·초기 등록, 접점/패킹 검증 전',
 'vehicle_conditional':'작은 차량 머리 조건부 보존'}

cells = []
def add(character, form, category, buckets, note, links, art_scope):
    cells.append({'character':character,'form':form,'category':category,
      'states':[{'status':k,'label':LABELS.get(k,k),'refs':compact(v)} for k,v in buckets.items() if v],
      'note':note,'art_review':art_scope,'evidence':list(dict.fromkeys(links)),
      'all_gameplay_verified':False,'user_final_accepted':False})

sh = read(B/'shibuki_audit/fullform_ledger14.json')
n5 = read(B/'nana_audit/scope_summary_v5/manifest.json')
n7 = read(B/'nana_audit/scope_summary_v8/manifest.json')
sm = {'new_art_frozen_for_integration':'integrated_new_art','preserve_accepted_detail':'preserve_reviewed','art_rework_group_pending':'needs_redraw','preserve_effect_check_body_dependency':'effect_only','preserve_vehicle_head_pending_accessory_check':'vehicle_conditional'}
SN = {
 'idle':'수용 기준 대기를 보존한다.',
 'run':'Ultimate3..32는 새 원화 통합,1/2는 수용 세부 보존. 기본/포스1..32 새 원화·목표160층은 현재 미패킹 후보다.',
 'air':'33..54 새 공중/사격 원화 통합. 93/94는 대시 범주에 한 번만 집계한다.',
 'wall':'55..66 두 의상 별도 원화/사격 접점 통합.',
 'dash':'67..84+93/94 새 원화 통합. 예전 장부의 미완료 서술은 현재 참조 상태로 대체한다.',
 'hurt':'120..125는 네 폼 새 저체력. 피격106..114/233..236의 본체 상세와 기존 번개 분리를 후속으로 유지.',
 'ladder':'기본/포스14는 새 원화 통합. Ultimate14는 별도 미착수이며 기본형 제작으로 완료 처리하지 않는다.',
 'special':'98/99와100..104/231/232는 네 폼 새 원화·오른손 교정 통합. 나머지 정지/특수·호버와208..230의 실제 사용/효과 구분은 남음. 기본형에 표가 있다는 이유로 능력 사용 가능으로 보지 않는다.',
 'ride':'체이서162..174 상세화 미착수. 184..203은 작은 머리 자원으로 조건부 보존; Ultimate 장식 생략 검토가 남는다.',
 'ceremony':'기본/포스 등장/정면/귀환/승리 새 원화 통합. Ultimate는 별도 후속. 독립 광선은 몸체 실루엣 의존 여부만 구분.'}
NN = {
 'idle':'수용 대기·대기 연결을 보존한다.',
 'run':'1..32 네 폼 새 원화 통합. 최신 Ultimate32는49da 동결 및 대표 실기 근거를 연결.',
 'air':'33..54 네 폼 새 원화 통합. 총구·팔·부분 의상 기술검사와 실제 미술 기록을 분리.',
 'wall':'55..66 네 폼 새 원화 통합.',
 'dash':'67..84+93/94 네 폼 새 원화 통합. 낮은 두 발/소매 경계 국소 교정 포함.',
 'hurt':'기본/포스 피격·저체력은 재작화 잔여. Ultimate120..125는 기존 상세 보존 판단이며 새 제작 완료로 세지 않는다. 나머지는 추가 판단.',
 'ladder':'기본/포스 새 전신 작업은 남음. 포스144..152/155의 작은 원화 명암 복원은 전신 재작화와 구분. Ultimate는 보존/수정 추가 판단.',
 'special':'기본/포스 라이징7은3bd156 동결·RN16 통합. 포스 새7·기본4 참조 실제 업로드 확인,20판 루트 열람. 부분 전조합 실기는 아님. Ultimate 라이징은 별도 원화·등록 단계로 ARC 미패킹.95..99·정지사격과213..230의 사용/효과 분류는 별도. Ultimate217/218/220은 머리만 복원.',
 'ride':'체이서162..174는 새 원화 미착수.184..203 작은 차량 머리는 기존 상세 보존 판단이며 전신 누락으로 세지 않는다.',
 'ceremony':'133..139 및204..207은 새 미술 잔여. 기본/포스156..158은 재작화 대상, Ultimate는 추가 판단.133..137 Ultimate 재킷층은 존재하며 최근 덮어쓰기 결함이 아니다.'}

for char in ['shibuki','nana']:
 for form in ['base','fourth','ultimate_before','ultimate_after']:
  if char == 'shibuki':
   records = {r['ref']:sm.get(r['status'],r['status']) for r in sh['references'] if r['form']==form}
  else:
   records = {r['ref']:r['decision'] for r in n5['frames'][form]}
   for ref in n7['summary'][form]['frozen_full_new_art_refs']: records[ref]='integrated_new_art'
  for cat, refs in XREFS.items():
   buckets=collections.defaultdict(list)
   for ref in refs:
    state=records[ref]
    if char=='shibuki' and form in ['base','fourth'] and cat=='run': state='candidate_unpacked'
    if char=='nana' and ref in [100,101,102,103,104,231,232] and form in ['base','fourth']: state='integrated_new_art'
    if char=='nana' and ref in [100,101,102,103,104,231] and form.startswith('ultimate'): state='source_only'
    buckets[state].append(ref)
   links=[char+'_ledger',char+('_ultimate' if form.startswith('ultimate') else '_base'),'br14' if char=='shibuki' else 'rn16']
   if char=='shibuki' and cat=='run' and form in ['base','fourth']:links.append('shibuki_run_candidate')
   if char=='nana':links += ['nana_decisions','nana_old_views']
   if char=='nana' and cat=='special':links += ['nana_rising','nana_rising_frozen','nana_rising_reader','nana_rising_art','nana_rising_runtime','nana_rising_runtime_views','nana_ultimate_rising_source','nana_ultimate_rising_registered']
   if char=='nana' and cat=='ceremony':links.append('nana_arrival')
   if cat in ['run','dash']:links.append(char+'_runtime')
   add(char,form,cat,buckets,(SN if char=='shibuki' else NN)[cat],links,
       '기존 주요 시트의 실제 열람은 담당 장부에 기록. 새 동결 재독출은 누적 FROZEN의 루트/제작자 기록을 따른다. 이번 집계에서 그림을 다시 전수 열람하지 않았다.')
  if char=='shibuki':
   add(char,form,'ui',{},'선택18..21 새몸 동기화 및23 빛기둥 후속 통합. 저장34조합은 수용 대기 사본 보존. 새 이동32 이후 별도 선택 사본 의존성을 다시 확인해야 한다.', ['shibuki_ledger','br14','shibuki_selection'],'이전 선택/저장 시트 실제 열람 + 최신 선택23 실기. 모든 UI표시의 새 실기를 뜻하지 않는다.')
  else:
   add(char,form,'ui',{},'현재 선택 X영역은 보존. 향후156/157/158 등 새몸 제작 때 RN 원래 좌표변환으로 별도 동기화. 저장 대기 사본은 보존, 이번 집계의 새 전수 미술 검토 아님.', ['nana_ledger','rn15'],'담당 장부의 기존 보존·사본 의존 기록. 새 선택/저장 전수판은 이 집계에서 확인하지 않음.')
  add(char,form,'hq',{},'BR14/RN15에서 HQ12·대화8(조립12은행 별칭)·잔기양PL각10·pause양PL을 별도 추출. 큰 일러스트/독립 전신/작은 잔기의 용도를 구분해 루트가 수용 디자인 보존으로 판단했다. RN16에서 이 별도 사본은 불변. 폼별로 독립 그림이 있다고 가정하지 않는다.',[char+'_ledger','x_endpoints','x_endpoint_views'],'캐릭터별4판, 총8판 hud_checkpoint 및 root 실제 열람. 새 확정 절단 없음. 모든 반복 스테이지 대사 사본/실사용·타이틀·무기획득은 미검토.')

ZM = {'idle':['idle'],'run':['run'],'air':['jump'],'wall':['wall'],'dash':['dash'],
 'hurt':['hurt','low_hp'],'ladder':['ladder'],
 'special':['ground_saber','air_saber','air_spin','wall_saber','shippuuga','ryuenjin','hyouretsuzan','raijingeki_shared','rakuhouha','rakuhouha_static_body'],
 'ride':['ride_chaser','ride_armor_head','ride_partial_unknown'],
 'ceremony':['arrival_body','arrival_light','victory_return_body','return_light']}
zg=read(D/'group_map.json')
rl=read(D/'rin_extension/progress_ledger.json')
newrin=set(rl['new_art_prepared_refs'])
for char in ['riko','rin']:
 for form in ['normal','black']:
  for cat, groups in ZM.items():
   buckets=collections.defaultdict(list)
   for group in groups:
    data=zg[char][group]
    for ref in data['body_or_head_refs']:
     state='preserve_reviewed' if (char=='rin' and ref not in newrin) or cat=='idle' else 'integrated_new_art'
     if char=='riko' and cat!='idle':state='latest_source_reviewed' # Riko includes preserved fine head/body; never imply 313 redrawn.
     buckets[state].append(ref)
    buckets['effect_only'].extend(data.get('effect_or_blank_refs',[]))
   links=[char+'_views',char+'_patch','zero_groups','br14' if char=='riko' else 'rn15']
   if char=='rin': links += ['rin_ledger','rin_red_runtime' if form=='black' else 'rin_normal_runtime']
   else:links += ['riko_black_runtime' if form=='black' else 'riko_normal_runtime']
   note='최신 실제 자원의 전체 몸체/머리 미술 재검토에서 추가 확정 수정 후보 없음. 새 그림과 기존 수용 세부의 보존을 함께 포함한다.'
   if cat=='ride':note+=' b1_42..49는 이전 VRAM을 남기는 부분 업로드로 단독 PNG 완전복원 불가; 미사용/누락아트로 단정하지 않는다. 실제 탑승 전수는 남음.'
   if cat=='special':note+=' 원검기/불꽃/무기객체는 별도 보존하고 정적23/24 몸체 사본도 동기화. 모든 기술·좌우·색상 실기를 뜻하지 않는다.'
   art='Rin 최신436표시를 일반29·레드29 총58판으로 실제 열람한 기존 기록 연결.' if char=='rin' else 'Riko 최신313몸체/머리·216형태24판 루트 실제 열람. 블랙은 같은 비트맵+기존 대상별 색상판/대표 실기이며 최신24판의 전색상 재열람으로 확대하지 않음.'
   add(char,form,cat,buckets,note,links,art)
  add(char,form,'ui',{},'선택32개·저장43을 최신 몸체와 원점/색인 대조. 일반/블랙 팔레트10/29와 PL01 0/13 일치. UI38→b1_11은 가는 워프빛이며 idle 별칭이 아니다.', ['zero_endpoints','zero_selection','zero_endpoint_views'],'끝점 비교판과 루트 선택화면 대표 실기.32개 모든 표시의 실기 완료 아님.')
  add(char,form,'hq',{},'HQ14·잔기9·대사3은 별도 크기/용도의 수용 디자인으로 보존 판단. 플레이어4510표시에 합산하지 않음. 새 실사용/모든 스테이지 대사 사본 전수는 미검증.', ['zero_endpoints','zero_endpoint_views'],'각 캐릭터 끝점/HQ/잔기/대사4판, 합계8판 제작자·루트 실제 열람. 블랙 전용 그림이라고 가정하지 않음.')

LABELS['latest_source_reviewed']='최신 수정·보존 혼합 / 전체 미술 재검토'
for c in cells:
 for s in c['states']:s['label']=LABELS.get(s['status'],s['status'])
assert len(cells)==144 and len({(c['character'],c['form'],c['category']) for c in cells})==144
priorities = [
 {'owner':'overhaul_ui','character':'shibuki','scope':'기본/포스 이동1..32','stage':'새 원화·등록 목표 고정, 압축 용량 해결 전; 실제 후보 ARC 미출력','evidence':['shibuki_run_candidate']},
 {'owner':'overhaul_audio','character':'nana','scope':'Ultimate Rising100..104/231/232','stage':'새 원화·의상/접점 등록, 미패킹. 기본/포스7은 RN16 통합·대표 실기 근거 확보','evidence':['nana_rising_frozen','nana_rising_runtime','nana_ledger']},
 {'owner':'overhaul_ui','character':'shibuki','scope':'Ultimate 사다리143..155/183, 등장133..139+실루엣,156..158/204..207','stage':'새 세부 미술 별도 미착수','evidence':['shibuki_ledger']},
 {'owner':'overhaul_audio','character':'nana','scope':'기본/포스 피격·저체력, 사다리,등장/승리; Ultimate등장/98·99/204..207','stage':'재작화 대상과 추가 보존판단을 참조별 분리','evidence':['nana_ledger','nana_arrival']},
 {'owner':'overhaul_ui + overhaul_audio','character':'shibuki,nana','scope':'체이서162..174 및213..230/208..212 사용·몸체/효과 분류','stage':'전폼 미지정·별도 효과를 빠뜨리지 않도록 후속. 능력 없는 기본/획득전은 실제 사용 경로 별도','evidence':['shibuki_ledger','nana_ledger']},
 {'owner':'root','character':'shibuki,nana','scope':'HQ/대사/잔기 별도 사본','stage':'별도 보충판8장 루트 실제 열람·수용 디자인 보존 판단. 새로운 전장면 실기 완료 아님','evidence':['x_endpoints','x_endpoint_views','br14','rn16']},
 {'owner':'root','character':'riko,rin','scope':'차량/사다리/색상별 특수·전환 미확정 사건','stage':'현재 추가 확정 새 미술 결함 없음. 기존 미술 근거 보존, 대표 실기와 전수 실기 구분','evidence':['riko_views','rin_views','rin_normal_runtime','rin_red_runtime']}]
plans={m:read(B/f'staging_{m}.json') for m in ['br_v14','rn_v16']}
result = {
 'scope':'네 캐릭터12전신폼×12범주 읽기 집계. 새 전수 미술 검사나 완료율 보고가 아니다.',
 'integration':{m:{'resources':p['resources'],'output':p['output']} for m,p in plans.items()},
 'unit_policy':'폼/동작/별도사본 상태를 나눈다. 수정표시 수·비율·동결 수를 미술 완료율로 사용하지 않는다.',
 'evidence':evidence,'categories':CATEGORIES,'forms':FORMS,'cells':cells,'next_work':priorities,
 'coverage_limits':[
  'X 각237표의9예약/빈 참조105/175..182는 별도 제외; 228나머지 참조는 정확히 한 모션 범주에 분류했다.',
  'Zero444압축참조 중436단독표시와8이력의존 부분VRAM을 구분. 별도 정적몸체23/24·UI/HQ는 별도 증거.',
  '부분아머16마스크×arm1/2 기술 exact와 사람이 모든 조합을 본 것은 다르다. 실제 부분판 열람은 각 후보 기록 범위만.',
  '캡슐 그래픽10..13의48참조/의상 실루엣은 별도 의존자원. 이번 전신표와 새 전수열람 수에 넣지 않는다. 대기 보존에 따라 기존 정합근거를 계승하되 실기 장면별 한계를 유지.',
  'X HQ/대사/잔기/pause 별도그림은 새 보충판8장으로 실제 열람했다. 반복스테이지 대사사본 전체와 타이틀/무기획득은 이번 열람 범위 밖이다.',
  '이 집계는 기존 실제 열람을 링크한 읽기 조사. 모든144칸을 이번에 새로 보거나 실제게임 전수검증한 것은 아님.',
  'Shibuki ledger14의 용량 대기63고유키는64폼참조와 단위가 다르다.1은 수용 대기 재사용이며64장의 새 생성 원화를 뜻하지 않는다.',
  'Nana v5의 구RGBA hash는 새 이동32의 최신 그림 hash가 아니다. v8동결 및 RN16 자원 결속으로 제작 상태를 갱신하고 이후 제작 중 원화는 별도로 기록한다.'
 ],'all_art_complete':False,'all_gameplay_verified':False,'user_final_accepted':False,
 'game_or_art_modified':False,'source_read_errors':[]}
(OUT/'coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def link(key):
    e=evidence[key];p=ROOT/e['path'];href=os.path.relpath(p,OUT).replace('\\','/')
    return f'<a href="{html.escape(href)}">{html.escape(key)}</a>'
body=['<!doctype html><meta charset="utf-8"><title>전체 폼·모션 작업 범위</title><style>body{font:15px system-ui,sans-serif;background:#111820;color:#e9edf2;margin:24px}a{color:#9dcfff}table{border-collapse:collapse;width:100%;margin:18px 0 32px}th,td{padding:10px;border:1px solid #405164;text-align:left;vertical-align:top}th{background:#233547;position:sticky;top:0}td:first-child{width:110px}small{color:#b7c5d4}summary{cursor:pointer}h2{margin-top:40px}.warn{background:#3c2d19;padding:14px}ul{padding-left:20px}</style>',
 '<h1>네 캐릭터 · 폼별 모션 범위</h1><p>현재 통합: BR14 / RN16. 12전신폼 × 12범주. <b>수정 수는 완료율이 아닙니다.</b> 기존 실제 미술 열람과 기술/대표 실기를 연결한 읽기 집계입니다.</p>',
 '<p class="warn">시부키 기본/포스 이동32는 새 원화·등록 단계로 용량 미패킹. 나나 기본/포스 라이징7은 RN16 통합·대표 실기 근거를 확보했습니다. X 별도 HQ·대사·잔기 보충판8장은 루트 직접 열람 후 용도별 디자인 보존으로 판단했습니다.</p>',
 '<p><a href="coverage.json">전체 JSON</a> · <a href="../final_endpoint_audit01/ZERO_UI_HQ_SUPPLEMENT.html">Zero 별도 UI/HQ 보충판</a> · <a href="../x_endpoint_supplement01/X_UI_HQ_SUPPLEMENT.html">X 별도 UI/HQ 보충판</a></p><h2>다음 작업</h2><table><tr><th>담당</th><th>범위</th><th>상태</th></tr>']
for p in priorities:body.append('<tr>'+''.join('<td>'+html.escape(str(p[k]))+'</td>' for k in ['owner','scope','stage'])+'</tr>')
body.append('</table>')
for char,label in [('shibuki','시부키'),('nana','나나'),('riko','리코'),('rin','린')]:
 for form in ['base','fourth','ultimate_before','ultimate_after','normal','black']:
  rows=[c for c in cells if c['character']==char and c['form']==form]
  if not rows:continue
  body.append(f'<h2 id="{char}-{form}">{label} · {FORMS[form]}</h2><table><tr><th>범주</th><th>상태·참조</th><th>현재 판단 / 남은 범위</th><th>실제 열람·근거</th></tr>')
  for c in rows:
   states='<br>'.join(html.escape(s['label']+': '+s['refs']) for s in c['states']) or '별도 사본 범위'
   body.append('<tr><td>'+CATEGORIES[c['category']]+'</td><td>'+states+'</td><td>'+html.escape(c['note'])+'</td><td><small>'+html.escape(c['art_review'])+'</small><details><summary>근거</summary>'+'<br>'.join(link(k) for k in c['evidence'])+'</details></td></tr>')
  body.append('</table>')
body.append('<h2>한계</h2><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in result['coverage_limits'])+'</ul>')
(OUT/'COVERAGE.html').write_text('\n'.join(body),encoding='utf-8')
verification={'passed':True,'cells':len(cells),'characters':4,'full_forms':12,'categories':12,'x_reference_partition':237,'evidence_files':len(evidence),'broken_evidence_links':0,'all_art_complete':False,'no_new_gameplay_or_art_tests':True}
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verification,ensure_ascii=False))
