"""벽12 동결과 Ultimate 이동 재검토를 반영한 표시키 장부. 완료% 아님."""
from pathlib import Path
import sys,json,collections
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
sys.path[:0]=[str(ROOT),str(D/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
def main():
 out=D/'scope_summary_v3';out.mkdir(exist_ok=False)
 old=json.loads((D/'scope_summary_v2/manifest.json').read_text('utf8'))
 paths={'PL00':D/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC','PL02':D/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC'}
 expected={'PL00':'cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','PL02':'e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'}
 for k,p in paths.items():need(digest(p)==expected[k],'Frozen hash')
 arcs={k:Archive(p.read_bytes())for k,p in paths.items()};summary={};unique={}
 for form,key,mask in(('base','PL00',0),('fourth','PL00',15),('ultimate_before','PL02',15),('ultimate_after','PL02',0)):
  items=old['frames'][form];groups=collections.defaultdict(list)
  for q in items:
   n=q['ref'];effective=15 if form=='ultimate_after'and 217<=n<=230 else mask
   im=Image.new('RGBA',(384,384))if n in{105,*range(175,183)}else arcs[key].composite(n,effective,2)[0]
   q['rgba_sha256']=sha(im.tobytes());q['opaque_bbox']=im.getbbox()
   if form.startswith('ultimate'):
    if 55<=n<=66:q.update(decision='repaint_frozen',production_stage='full_new_art_native_frozen',evidence='ultimate_wall_repaint/packed_wall_candidate_v1/FROZEN.json',reviewed='ultimate_wall_repaint/packed_wall_candidate_v1/readback_1.png + readback_2.png')
    if 1<=n<=32:q.update(decision='needs_redraw',production_stage='reviewed_new_art_pending',evidence='ultimate_dash_repaint/ground_run_review_v1/REPORT.md',reviewed='ultimate_dash_repaint/ground_run_review_v1 before_1..6 + after_1..6')
    if n in(*range(67,85),93,94):
     q['production_stage']='first_body_candidate_registered'if form=='ultimate_before'and n in(67,71,79,93)else'full_repaint_planned'
     q['evidence']='ultimate_dash_repaint/PLAN.md'
   if im.getbbox():groups[q['rgba_sha256']].append(n)
  summary[form]={'physical_reference_count':237,'nonempty_distinct_rgba_keys':len(groups),'decision_reference_counts':dict(collections.Counter(q['decision']for q in items)),'stage_reference_counts':dict(collections.Counter(q['production_stage']for q in items))}
  unique[form]=[{'rgba_sha256':h,'refs':refs,'decisions':sorted({items[n]['decision']for n in refs}),'stage':sorted({items[n]['production_stage']for n in refs})}for h,refs in groups.items()]
 old.update(sources={k:{'path':str(p.relative_to(ROOT)),'sha256':digest(p)}for k,p in paths.items()},summary=summary,unique_render_keys=unique,full_new_art_frozen_reference_form_pairs=240,full_style_complete=False,gameplay_by_this_agent=False)
 old['update_scope']='기본/포스 각86, Ultimate 공중22+벽12 각34. 총240은 고유원화 수·사용자수용 수·완료율이 아니다. 이번 전수 재열람은 Ultimate 이동32×2폼 12시트뿐이며948표시 전수를 다시본것이 아니다.'
 write(out/'manifest.json',old)
 lines=['# 나나 표시키별 미술 장부 v3','','벽12 동결과 Ultimate 이동 전후32 재검토를 반영했다. 기본/포스 각86, Ultimate 각34참조가 전신 새원화로 동결됐다. 총240참조×폼이며 고유 원화 수나 전체 미술 완료율이 아니다.','','| 폼 | 새원화 동결 | 수정 필요 | 현재 보존 | 판단 전 재검토 | 도달성 분리 | 효과 | 예약 |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for form,q in summary.items():
  c=q['decision_reference_counts'];lines.append('|'+form+'|'+'|'.join(str(c.get(k,0))for k in('repaint_frozen','needs_redraw','preserve_reviewed','review_before_decision','reachability_review_required','effect_only','placeholder'))+'|')
 lines+=['','이번 실제 추가열람: `ultimate_dash_repaint/ground_run_review_v1/before_1..6.png`, `after_1..6.png` 12장, 이동1..32의 전후 모든 정적표시. 대기/새공중39를 같은원점으로 나란히보았다.','', '얼티밋 이동 홀수16은 기존 보존 분류를 수정 필요로 갱신했다. 앞머리 단색면과 단순한 귀 끝/권총덩어리, 짝수16의 사각 소매·맨팔 잔여 색면이 새공중/벽 기준에 미달한다. 대시20부터 마무리하고 이동32도 전체 몸체·의상·팔을 연속모션 단위로 정리한다.','', '대시 첫67/71/79/93은 새재킷 원화/네이티브 후보 단계.71 두발은국소재작화 준비,79/93 발 x 및권총 정합 미완료. 다른대시/후폼/사격/노바 연계는미완료. 새공중22·벽12의동결자원은보존한다.','', '기본/포스 특수·사다리·피격/저체력·등장승리, Ultimate 나머지특수/탑승/호버, 선택/저장과부분파츠는전체범위에유지한다. 이장부는bank0의237×4만집계하므로외부은행/UI/부분조합을분모에임의추가하지않는다.','', '루트의v9나나50참조실기와본제작자의정적검수를구분한다. 이번생성/장부는게임입력·BIN·포인터·사용자저장을변경하지않았다.']
 (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8');print(json.dumps(summary))
if __name__=='__main__':main()
