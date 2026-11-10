"""Refresh residual authored-body inventory from the candidate200 ARC; reader only."""
from pathlib import Path
import sys,json,struct,hashlib
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'remaining200_review';assert not(O/'manifest.json').exists();O.mkdir(exist_ok=True)
P=D/'prepared_spin01/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a'
l=json.loads((D/'progress_ledger.json').read_text('utf8'));done=set(l['new_art_prepared_refs'])|set(json.loads((P.parent/'proposal.json').read_text('utf8'))['new_art_refs']);assert len(done)==200
pal=struct.unpack_from('<64H',entry(arc,9));idle=rgba(render(arc,0,0,147)[0],pal);groups=[]
for original in l['groups']:
 remaining=sorted(set(original['body_or_head_refs'])-done)
 if not remaining:continue
 uniq={}
 for key in remaining:
  if not(key.startswith('b0_')or key.startswith('b1_')):continue
  b,n=int(key[1]),int(key[3:]);a=render(arc,b,b*5,n)[0];h=sha(a.tobytes())
  if h not in uniq:uniq[h]={'master':key,'aliases':[],'image':rgba(a,pal)}
  uniq[h]['aliases'].append(key)
 variants=list(uniq.values());sheets=[]
 for start in range(0,len(variants),6):
  p=O/f"{original['group']}_{start//6:02}.png";sub=variants[start:start+6]
  page([(v['master']+' '+','.join(v['aliases'][1:]),v['image'])for v in sub],idle,p,cols=3,scale=5)
  sheets.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes()),'actually_viewed':False,'master_refs':[v['master']for v in sub]})
 groups.append({'group':original['group'],'remaining_body_or_head_refs':remaining,'non_main_refs_not_rendered':[k for k in remaining if not(k.startswith('b0_')or k.startswith('b1_'))],'exact_display_unique':len(variants),'exact_alias_groups':[{'master':v['master'],'aliases':v['aliases']}for v in variants],'sheets':sheets})
report={'source_arc':str(P.relative_to(ROOT)),'source_sha256':sha(arc),'prepared_refs_including_derived':200,'original_body_or_head_classification':315,'groups':groups,'full_visual_review_complete':False,'game_changed':False,'scope':'최신200에서 잔여 본체·머리를 정확 같은 표시만 묶었다. 대기와 기존효과는 보존대상이며 원화 생성 필요 개수와 잔여참조 개수는 다르다. 정적 몸체23/24는 별도 동기화되어 있어 새 원화 미작업으로 세지 않는다.'}
(O/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps([{'group':g['group'],'remaining':len(g['remaining_body_or_head_refs']),'unique':g['exact_display_unique'],'sheets':[Path(s['path']).name for s in g['sheets']]}for g in groups]))
