"""실제 표시키/중복관계를 집계하되 미술 완성률로 환산하지 않는다."""
from pathlib import Path
import sys,json,collections
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
sys.path[:0]=[str(ROOT),str(D/'native_restore'),str(D)]
from preview_restore import Archive,sha,digest,write,need
from update_scope_ledger import group
PLACE={105,*range(175,183)};IDLE={0,115,116,117,118,119,141,142};FX={*range(126,133),159,160,161};BASE_NEW={*range(1,85),93,94};ULT_NEW=set(range(33,55))
def decision(form,n):
 if n in PLACE:return 'placeholder','not_applicable',None
 if n in IDLE:return 'preserve_reviewed','accepted_style_reference',None
 if form in('base','fourth')and n in BASE_NEW:return 'repaint_frozen','full_new_art_native_frozen','dash_repaint/packed_dash_candidate_v1/FROZEN.json'
 if form.startswith('ultimate')and n in ULT_NEW:return 'repaint_frozen','full_new_art_native_frozen','ultimate_air_repaint/packed_air_candidate_v1/FROZEN.json'
 if form.startswith('ultimate')and 55<=n<=66:return 'needs_redraw','candidate_registered'if n%2 or(form=='ultimate_before'and n<=60)else'new_arm_pending','ultimate_wall_repaint/PLAN.md'
 if n in FX:return 'effect_only','preserve_timing_and_color_effect',None
 if n in(87,92)or 184<=n<=203:return 'preserve_reviewed','accepted_existing_detail_no_new_defect_in_static_review',None
 if form in('base','fourth'):
  redo={95,96,98,99,*range(100,105),231,232,*range(106,115),*range(120,126),233,234,235,236,*range(133,140),*range(143,159),183,*range(162,175),*range(204,208)}
  if n in redo:return 'needs_redraw','limited_source_restore_only'if form=='fourth'and n in{*range(144,153),155}else'not_started',None
  if 213<=n<=230:return 'reachability_review_required'if form=='base'else'needs_redraw','pose_or_effect_classification_required',None
 else:
  if n in range(1,33,2)or n in range(120,126)or n in(95,96):return 'preserve_reviewed','existing_detail_sufficient_for_now_not_new_art',None
  redo={*range(2,33,2),*range(67,85),93,94,98,99,*range(133,140),*range(162,175),*range(204,208)}
  if n in redo:return 'needs_redraw','limited_source_hair_restore_only'if 67<=n<=84 else'not_started',None
  if 213<=n<=230:return 'reachability_review_required'if form=='ultimate_before'else'needs_redraw','limited_source_hair_sync_only'if n in(217,218,220)else'pose_or_effect_classification_required',None
 return 'review_before_decision','not_automatically_defective',None
def main():
 out=D/'scope_summary_v2';out.mkdir(exist_ok=True)
 paths={'PL00':D/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC','PL02':D/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC'};exp={'PL00':'cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','PL02':'122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18'}
 for k,p in paths.items():need(digest(p)==exp[k],'Frozen ARC')
 arcs={k:Archive(p.read_bytes())for k,p in paths.items()};forms={};summ={};uniques={}
 for form,key,mask in [('base','PL00',0),('fourth','PL00',15),('ultimate_before','PL02',15),('ultimate_after','PL02',0)]:
  items=[];keys=collections.defaultdict(list)
  for n in range(237):
   effective=15 if form=='ultimate_after'and 217<=n<=230 else mask
   if n in PLACE:im=Image.new('RGBA',(384,384))
   else:im,_=arcs[key].composite(n,effective,2)
   dec,stage,evidence=decision(form,n);h=sha(im.tobytes());q={'ref':n,'group':group(n),'rgba_sha256':h,'opaque_bbox':im.getbbox(),'decision':dec,'production_stage':stage,'evidence':evidence,'reviewed':'remaining_review_v1/review.json'if not(form.startswith('ultimate')and n in ULT_NEW)else'ultimate_air_repaint/packed_air_candidate_v1/FROZEN.json'};items.append(q)
   if im.getbbox():keys[h].append(n)
  forms[form]=items;summ[form]={'physical_reference_count':237,'nonempty_distinct_rgba_keys':len(keys),'decision_reference_counts':dict(collections.Counter(q['decision']for q in items)),'stage_reference_counts':dict(collections.Counter(q['production_stage']for q in items))};uniques[form]=[{'rgba_sha256':h,'refs':refs,'decisions':sorted(set(items[n]['decision']for n in refs)),'stage':sorted(set(items[n]['production_stage']for n in refs))}for h,refs in keys.items()]
 report={'scope':'bank0 0..236 × basic/full Fourth/Ultimate before/after only. Same raster hashes grouped within each form; not independent animation or artwork count.','sources':{k:{'path':str(p.relative_to(ROOT)),'sha256':digest(p)}for k,p in paths.items()},'summary':summ,'frames':forms,'unique_render_keys':uniques,'full_new_art_frozen_reference_form_pairs':216,'full_style_complete':False,'gameplay_by_this_agent':False,'limits':['부분16마스크·arm1/2·캡슐별도은행·선택/저장 전체를 이237분모에 더하지 않음.','needs_redraw에는 생성/등록중과원화복원만한것 포함. 동결만을 게임미술완료로 세지 않음.','효과/도달불가/예약참조가 섞이므로 완료%를 계산하지 않음.','새로재작화하지않았다는 사실만으로 불량처리하지 않음.','이 출력은 앞 실제 열람 기록의 분류를 최신동결원화에 갱신한 장부. 오늘948장을 다시열람했다는 뜻 아님.']}
 write(out/'manifest.json',report)
 lines=['# 나나 표시키별 미술 장부 — 갱신판','', '이 집계는 기본/풀포스/얼티밋 전후의 bank0 237물리참조씩을 추적한다. **완료율이 아니다.** 같은 폼 안의 RGBA가 같은 것은 `unique_render_keys`에 묶었고, 서로 다른 모션 타이밍/효과 또는 부분파츠 상태를 새 원화 수로 더하지 않았다.','', '| 폼 | 새 전신 원화 동결 참조 | 수정 필요(진행 중 포함) | 현재 세부 보존 | 판단 전 재검토 | 도달성 분리 | 효과 | 예약 |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for form,q in summ.items():
  c=q['decision_reference_counts'];lines.append('|'+form+'|'+ '|'.join(str(c.get(k,0))for k in('repaint_frozen','needs_redraw','preserve_reviewed','review_before_decision','reachability_review_required','effect_only','placeholder'))+'|')
 lines+=['','기본/포스는 이동32+공중22+벽12+대시20=각86참조, 얼티밋은 새 공중22=각22참조가 전신 새원화로 동결됐다. 합계216 참조×폼은 고유 원화216장이 아니며 사용자 실기 수용216건도 아니다.','', '얼티밋 벽12×2폼은 현재 전후6몸체 후보+재킷 앞3사격 후보 단계다. 사격 뒷3과맨팔6,공동패킹·MIPS·독립검사가남았다. 기존대시머리18/Nova3의소규모복원은새전신재작화동결에포함하지않는다.','', '남은 우선순위: 얼티밋 벽 → 네폼98/99와기본/포스특수 → 기본/포스사다리 → 피격/저체력/등장승리 → 얼티밋이동사격/대시연계 → 체이서·호버. 이미 세밀한 얼티밋 이동홀수·저체력과95/96,탑승머리는 보존후연결검토한다. 저장/선택은 이표밖별도후속이며 누락완료처리하지않는다.','', '근거: `remaining_review_v1/REPORT.md`와34시트실제열람기록, 각동결FROZEN, 현재벽 PLAN. 오늘새전수미술열람이나새게임검사는하지않았다.']
 (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8');print(json.dumps(summ))
if __name__=='__main__':main()
