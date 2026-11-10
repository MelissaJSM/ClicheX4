"""Hash-bound positive and corruption checks for character-select copy packing."""
from pathlib import Path
import sys,json,hashlib,copy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.build_sprite_style_unification import check_selection,check_selection_body,check_zero_selection_body
from scripts.prepare_riko_ui import entry,replace_entry,SELECTION_MAPPING
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
from src.psx_ui_atlas import tile_pixels,write_tile
W=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def once(path,data):
 if path.exists():
  if path.suffix=='.json':assert json.loads(path.read_text('utf8'))==json.loads(data)
  else:assert path.read_bytes()==data
 else:path.write_bytes(data)
def reject(label,fn):
 try:fn()
 except (ValueError,AssertionError):return label
 raise AssertionError('Corruption accepted: '+label)
rows=[]
for mode,char in [('br','riko'),('rn','rin')]:
 plan=json.loads((W/f'staging_{mode}_v12.json').read_text('utf8'))
 source=ROOT/plan['source_bin'];assert sha(source.read_bytes())==plan['source_sha256']
 original=read_disc(source,('ST0E_U1.ARC',))[0]['ST0E_U1.ARC']
 folder=W/'selection_sync01'/char;new=(folder/'ST0E_U1.ARC').read_bytes()
 plan['resources']['ST0E_U1.ARC']={'path':(folder/'ST0E_U1.ARC').relative_to(ROOT).as_posix(),'before':sha(original),'after':sha(new)}
 if char=='rin':
  p=W/'zero_audit/rin_extension/prepared_bank1_recovery128/PL01_U.ARC';plan['resources']['PL01_U.ARC']['path']=p.relative_to(ROOT).as_posix();plan['resources']['PL01_U.ARC']['after']=sha(p.read_bytes())
 plan['sync_zero_selection_body']=True
 preserve_x=char=='rin'
 if preserve_x:plan['preserve_x_selection']=True
 check_selection(original,new,True,preserve_x)
 if not preserve_x:check_selection_body(plan)
 bodyproof=check_zero_selection_body(plan)
 failures=[reject('default scope refuses Zero mutation',lambda:check_selection(original,new))]
 tx=entry(new,0x10102);parts=entry(new,10)
 for label,index in [('portrait alteration',40960),('unknown non-target texture alteration',50000)]:
  b=bytearray(tx);b[index]^=1;bad=replace_entry(new,0x10102,bytes(b))
  failures.append(reject(label,lambda bad=bad:check_selection(original,bad,True,preserve_x)))
 oldparts=entry(original,10);owned={q['page']*256+q['tile']for n in SELECTION_MAPPING for q in composition_frame(oldparts,0,n)['parts']}
 tile=min(set(range(320))-owned);b=bytearray(tx);px=bytearray(tile_pixels(tx[:40960],tile));px[0]^=1;write_tile(b,tile,px)
 bad=replace_entry(new,0x10102,bytes(b));failures.append(reject('unowned Zero tile alteration',lambda:check_selection(original,bad,True,preserve_x)))
 p0=composition_frame(parts,0,1)['parts'][0];b=bytearray(parts);b[p0['record_offset']]^=0x20
 bad=replace_entry(new,10,bytes(b));failures.append(reject('unknown part flag',lambda:check_selection(original,bad,True,preserve_x)))
 # Structurally legal but visibly displaced body must fail the independent
 # whole-frame equality check, even when its resource hash is declared.
 b=bytearray(parts);at=p0['record_offset']+2;b[at]=(b[at]+1)&255
 bad=replace_entry(new,10,bytes(b));badpath=folder/'negative_body_offset.arc';once(badpath,bad)
 badplan=copy.deepcopy(plan);badplan['resources']['ST0E_U1.ARC'].update(path=badpath.relative_to(ROOT).as_posix(),after=sha(bad))
 failures.append(reject('declared but displaced body',lambda:check_zero_selection_body(badplan)))
 if preserve_x:
  b=bytearray(tx);b[90112]^=1;bad=replace_entry(new,0x10102,bytes(b))
  failures.append(reject('protected entire X bank mutation',lambda:check_selection(original,bad,True,True)))
 saved=folder/'integration_candidate.json';once(saved,(json.dumps(plan,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 rows.append({'character':char,'candidate_sha256':sha(new),'body_proof':bodyproof,'negative_cases_rejected':failures,'plan':saved.relative_to(ROOT).as_posix()})
dest=W/'selection_sync01/guard_checks.json';assert not dest.exists();dest.write_text(json.dumps({'passed':True,'rows':rows,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'characters':len(rows),'negative_cases':sum(len(r['negative_cases_rejected']) for r in rows)}))
