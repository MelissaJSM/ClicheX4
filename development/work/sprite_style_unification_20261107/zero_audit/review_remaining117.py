"""Current remaining-body ledger and native comparison sheets; no game writes."""
from pathlib import Path
import sys,json,struct,hashlib,collections
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'remaining117_review';assert not(O/'manifest.json').exists();O.mkdir(exist_ok=True)
P=D/'prepared_hurt_lowhp_v1/PL01_U.ARC';arc=P.read_bytes();assert hashlib.sha256(arc).hexdigest()=='4e18b1cda6731f97272eba361a2ac19df3606f75a19b5352f6025d403196e769'
lp=D/'progress_ledger.json';l=json.loads(lp.read_text('utf8'));done=set(l['new_art_prepared_refs']);assert len(done)==117
pal=struct.unpack_from('<64H',entry(arc,9));idle=rgba(render(arc,0,0,147)[0],pal)
groups=[]
for group in l['groups']:
 body=group['body_or_head_refs'];group['new_art_prepared']=sorted(set(body)&done);group['remaining']=sorted(set(body)-done)
 if not group['remaining']:continue
 uniq={}
 for key in group['remaining']:
  if not (key.startswith('b0_') or key.startswith('b1_')):continue
  b,n=int(key[1]),int(key[3:]);a=render(arc,b,b*5,n)[0];h=hashlib.sha256(a.tobytes()).hexdigest()
  if h not in uniq:uniq[h]={'master':key,'aliases':[],'image':rgba(a,pal)}
  uniq[h]['aliases'].append(key)
 variants=list(uniq.values());sheets=[]
 for k in range(0,len(variants),6):
  p=O/f"{group['group']}_{k//6:02}.png"
  items=[(v['master']+' '+','.join(v['aliases'][1:]),v['image'])for v in variants[k:k+6]]
  page(items,idle,p,cols=3,scale=5)
  sheets.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actually_viewed':False,'master_refs':[v['master']for v in variants[k:k+6]]})
 groups.append({'group':group['group'],'remaining_body_or_head_refs':group['remaining'],'non_main_refs_not_rendered':[k for k in group['remaining'] if not(k.startswith('b0_')or k.startswith('b1_'))],'exact_display_unique':len(variants),'exact_alias_groups':[{'master':v['master'],'aliases':v['aliases']}for v in variants],'sheets':sheets})
jsonout={'source_arc':str(P.relative_to(ROOT)),'source_sha256':hashlib.sha256(arc).hexdigest(),'prepared_refs_including_derived':117,'original_body_or_head_classification':315,'groups':groups,'full_visual_review_complete':False,'game_changed':False}
jsonout['scope']='기존 전수 표시 분류의 남은 자세를 최신 ARC에서 재추출한 작업용 색인. 동일 그림만 묶으며 미열람은 미열람으로 남긴다.'
(O/'manifest.json').write_text(json.dumps(jsonout,ensure_ascii=False,indent=2)+'\n','utf8')
lp.write_text(json.dumps(l,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps([{'group':g['group'],'remaining':len(g['remaining_body_or_head_refs']),'unique':g['exact_display_unique'],'sheets':len(g['sheets'])}for g in groups]))
