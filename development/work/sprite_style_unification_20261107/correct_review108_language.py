from pathlib import Path
import json, hashlib
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
p=W/'root_review_checkpoint108.json'; old=sha(p); r=read(p)
assert r['findings']==['新BR17を起動']
r['findings']=r.pop('findings_ko')
write(p,r)
s=W/'runtime/shibuki_fourth_hurt17_summary.json'; summary=read(s)
assert summary['root_review']['sha256']==old
summary['root_review']['sha256']=sha(p);write(s,summary)
write(W/'root_review_checkpoint108_language_correction.json',{'original_sha256':old,'corrected_sha256':sha(p),'reason':'미완성 일본어 임시문구를 삭제하고 기존 한국어 검토 내용만 findings에 유지했다. 출력 잘림으로 재확인이 필요했던 마지막3판도 루트가 이번 재개 시 실제 열람했다. 그림/관측/검증 범위는 변경하지 않았다.','summary_sha256':sha(s)})
print(sha(p),sha(s));print('107',sha(W/'root_review_checkpoint107.json'))
