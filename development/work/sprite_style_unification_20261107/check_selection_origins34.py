from pathlib import Path
import sys,json,hashlib,copy
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_sprite_style_selection_v3 import check_selection_body
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
out=W/'nana_selection_sync34_03';rn=read(out/'proposal_plan.json');br=read(W/'staging_br_v22.json')
check_selection_body(rn);check_selection_body(br)
wrong=copy.deepcopy(rn);wrong['project']='ver_buki_riko'
try:check_selection_body(wrong)
except ValueError as e:reason=str(e);assert 'Selection 19 differs' in reason
else:raise AssertionError('Wrong BR y+1 mapping accepted for RN')
report={'passed':True,'correct_RN_y0_all_four_exact':True,'correct_BR_y1_all_four_and_beam_exact':True,'wrong_BR_mapping_on_RN_refused':reason,'RN_plan_sha256':sha(out/'proposal_plan.json'),'BR_plan_sha256':sha(W/'staging_br_v22.json'),'validator_sha256':sha(ROOT/'scripts/build_sprite_style_selection_v3.py'),'runtime_verified':False}
p=out/'origin_regression.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
paths=[out/f'copy_{n}.png'for n in (18,19,20,21)];p=W/'root_review_checkpoint134.json';assert not p.exists()
p.write_text(json.dumps({'reviewer':'root','candidate_sha256':read(out/'report.json')['after'],'actually_viewed_files':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q),'actually_viewed':True}for q in paths],'findings':['선택18 승리·19/20 귀환 반전·21상승이 새 게임몸체의 세부와 원래표시좌표로 연결된다.','표시판에서 추가 확정 잘림·이질적 크기변화를 찾지 못했다. 배경/테두리/린 UI는 검사상 보존됐다.'],'runtime_verified':False,'whole_project_complete':False},ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
