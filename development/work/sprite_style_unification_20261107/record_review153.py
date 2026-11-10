from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_base_effect_audit01';p=W/'root_review_checkpoint153.json';assert not p.exists()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();m=json.loads((D/'report.json').read_text('utf8'))
files=[D/f'comparison_{i}.png'for i in(1,2,3)]
r={'checkpoint':153,'candidate_sha256':m['candidate_sha256'],'source_report':{'path':(D/'report.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'report.json')},'actually_viewed_files':[{'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f),'actually_viewed':True}for f in files],'observations':['PL00基本/포스140·208..212의3판을 직접 비교했다. 140은기본idle603셀+외부46셀 흰섬광,208/209는기본idle603셀의분홍단색과exact다.','포스는같은실루엣을공유해현재포스idle752셀과149셀 차이가있다. 베일·다리옷 실루엣의 정적차이를 확인했으며실제caller/아머층참여를확인할보완후보로남긴다.','210은같은45px높이의12px폭전환이나현재idle전체를고정가로축소한값과exact하지않다. 출처/기준점추가조사가필요하다.','211/212는수직빛줄기와끝조각이며인물표현없음. 원US전체alpha/파트의미를따로확인한효과로보존검토한다.'],'decisions':{'140_208_209':'기본형은확인된파생. 포스149셀차이의실제사용/부분레이어지원확인후보완검토','210':'기존가로축소실루엣의출처/변환/위치추가읽기','211_212':'기존색과좌표유지. 새원화로세지않음'},'limits':['인게임효과관측이나호출함수실행은이번읽기에서수행하지않았다.','PL02Ultimate효과분류의결과를PL00로확대하지않았다.','이읽기에서게임자산이나이미지내용은수정하지않았다.'],'new_art_created':False,'runtime_verified':False,'whole_project_complete':False}
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
