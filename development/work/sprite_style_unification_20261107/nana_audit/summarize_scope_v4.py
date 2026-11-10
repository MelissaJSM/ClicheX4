"""대시20 기술동결과 다음이동4 미술후보를 구분한 표시키 장부."""
from pathlib import Path
import sys,json,collections
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path[:0]=[str(ROOT),str(D/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
def main():
 out=D/'scope_summary_v4';out.mkdir(exist_ok=False);old=json.loads((D/'scope_summary_v3/manifest.json').read_text('utf8'))
 paths={'PL00':D/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC','PL02':D/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'};expected={'PL00':'cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','PL02':'d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'}
 for k,p in paths.items():need(digest(p)==expected[k],'Frozen asset hash');need(json.loads((p.parent/'FROZEN.json').read_text('utf8'))['asset_sha256']==expected[k],'Freeze binding')
 arcs={k:Archive(p.read_bytes())for k,p in paths.items()};summary={};unique={}
 for form,key,mask in(('base','PL00',0),('fourth','PL00',15),('ultimate_before','PL02',15),('ultimate_after','PL02',0)):
  items=old['frames'][form];groups=collections.defaultdict(list)
  for q in items:
   n=q['ref'];effective=15 if form=='ultimate_after'and 217<=n<=230 else mask;im=Image.new('RGBA',(384,384))if n in{105,*range(175,183)}else arcs[key].composite(n,effective,2)[0];q['rgba_sha256']=sha(im.tobytes());q['opaque_bbox']=im.getbbox()
   if form.startswith('ultimate'):
    if n in(*range(67,85),93,94):q.update(decision='repaint_frozen',production_stage='full_new_art_native_frozen_root_final_review_pending',evidence='ultimate_dash_repaint/packed_dash_candidate_v1/FROZEN.json',reviewed='ultimate_dash_repaint/packed_dash_candidate_v1/readback_1..4.png + timeline_16/17/18/19/128/129.png')
    if n in(217,218,220):q.update(production_stage='head_only_sync_frozen_full_body_not_redrawn',evidence='ultimate_dash_repaint/nova_head_registered_v1/registration.json',reviewed='ultimate_dash_repaint/packed_dash_candidate_v1/nova_readback.png')
    if form=='ultimate_before'and n in(1,7,15,25):q.update(production_stage='first_new_art_candidate_registered_not_packed',evidence='ultimate_run_repaint/before_first_registered_v1/registration.json',reviewed='ultimate_run_repaint/before_first_registered_v1/comparison.png')
   if im.getbbox():groups[q['rgba_sha256']].append(n)
  summary[form]={'physical_reference_count':237,'nonempty_distinct_rgba_keys':len(groups),'decision_reference_counts':dict(collections.Counter(q['decision']for q in items)),'stage_reference_counts':dict(collections.Counter(q['production_stage']for q in items))};unique[form]=[{'rgba_sha256':h,'refs':refs,'decisions':sorted({items[n]['decision']for n in refs}),'stage':sorted({items[n]['production_stage']for n in refs})}for h,refs in groups.items()]
 old.update(sources={k:{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for k,p in paths.items()},summary=summary,unique_render_keys=unique,full_new_art_frozen_reference_form_pairs=280,full_style_complete=False,gameplay_by_this_agent=False,update_scope='기본/포스 각86, Ultimate 공중22+벽12+대시20 각54. 총280참조×폼은 원화수/완료율이 아니다. 대시40표시는 이번준비자원 기술동결, 루트 최종미술/실기 미수용. Nova3×2는머리부분동기화로280에추가하지 않는다. 새이동4는미패킹후보.')
 write(out/'manifest.json',old)
 lines=['# 나나 표시키별 미술 장부 v4','','현재 준비자원의 실제 표시키를 집계했다. 기본/포스 각86, Ultimate 각54참조가 새 전신 원화를 포함한 자원으로 동결됐다. 총280참조×폼은 고유 원화 수·게임 적용 수·최종 완료율이 아니다. 이번 Ultimate 대시40표시는 **루트 최종 미술 검토와 게임 적용 전**이다.','','| 폼 | 새원화 자원 동결 | 수정 필요 | 현재 보존 | 판단 전 재검토 | 도달성 분리 | 효과 | 예약 |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for form,q in summary.items():c=q['decision_reference_counts'];lines.append('|'+form+'|'+'|'.join(str(c.get(k,0))for k in('repaint_frozen','needs_redraw','preserve_reviewed','review_before_decision','reachability_review_required','effect_only','placeholder'))+'|')
 lines+=['','Ultimate 대시67..84,93/94는 새 몸체10·새 사격팔8·기존효과73/74로 완결했다. Nova217/218/220은 같은머리의(+3,-6) 동기화이며 몸/효과는 그대로다. 새 Nova 전신 완료로 집계하지 않는다.','', '다음 Ultimate 이동1..32는 모든 전후가 여전히 수정 필요다. 첫1/7/15/25 새 재킷 원화를 생성해 고정96셀로 등록했으며 기존머리 덮기 없이 새 머리·소매 명암을 보존했다.7/25 발바닥+1px 및 권총/신발 접점은 미정합이라 아직 원화후보이고 현재집계의실제ARC에는들어가지않았다.','', '기본/포스 특수·사다리·피격/저체력·등장승리, Ultimate 나머지특수/탑승/호버, 선택/저장·부분파츠까지 전체범위는 유지한다. Rising103/104는 원래 오른쪽 불꽃발생점에 사랑이 권총·손을 맞추는 별도필수후속이다.','', '이번 실제 열람: 대시 최종readback4, Nova1, 원표순서6판, 브라우저71/94 두판, 다음이동입력2판 및 새4키등록1판. 이전948표시 전체를 이번에 다시본것처럼 기록하지 않는다. 해당 원본 시트별 열람 기록·의상/사격·한계는각작업 PLAN.md/registration.json에있다.','', '상세 `manifest.json`의고유RGBA키는같은모양의중복참조를묶은기술목록이다. 동일알파/숫자검사통과를미술일치나실기사용자수용으로해석하지않는다.']
 (out/'REPORT.md').write_text('\n'.join(lines)+'\n','utf8');print(json.dumps(summary))
if __name__=='__main__':main()
