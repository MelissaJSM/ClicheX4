"""Derive scoped native tools without editing the frozen low-HP sources."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;W=D.parent;old=W/'root_nana_lowhp';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=old/'pack_lowhp.py';text=src.read_text('utf8')
for before,after in [('low-HP','special-pose'),('509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce','ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16'),('tuple(range(120,126))','(95,96,98,99)'),("'target_layers_exact':30","'target_layers_exact':len(refs)*5"),('packed_lowhp01','packed_special01'),("f'low HP {n}'","f'special {n}'")]:
 assert before in text,before;text=text.replace(before,after)
start=text.index('  if ns==[155]:');end=text.index('  for n in ns:\n   raws[n]=nr',start)
block=text[start:end];keep=block[block.index('  else:\n')+8:];text=text[:start]+''.join(line[1:]if line.startswith(' ')else line for line in keep.splitlines(True))+text[end:]
text=text.replace('  if ns==[155]:changes[5][155]=pin\n','')
p=D/'pack_special.py';assert not p.exists();p.write_text(text,'utf8')
v=(old/'verify_candidate.py').read_text('utf8')
for a,b in [('low-HP','special-pose'),('pack_lowhp','pack_special'),('packed_lowhp01','packed_special01'),('layer0_120','layer0_095'),('verify_lowhp_','verify_special_')]:v=v.replace(a,b)
p=D/'verify_candidate.py';assert not p.exists();p.write_text(v,'utf8')
(D/'tooling_provenance.json').write_text(json.dumps({'sources':[{'path':str(p.relative_to(W.parents[1])).replace('\\','/'),'sha256':sha(p)}for p in(src,old/'verify_candidate.py')],'scope':'고정 입력SHA·참조4·출력경로를 분리하고155 사다리 전용 분기를 제거한 네이티브 패커. 동결된 기존 스크립트는 수정하지 않는다.'},ensure_ascii=False,indent=2)+'\n','utf8')
print('prepared special packer and checks')
