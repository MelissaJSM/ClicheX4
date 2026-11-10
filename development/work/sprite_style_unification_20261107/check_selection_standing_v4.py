"""Exercise the new selection scope on actual resources before any BIN build."""
from pathlib import Path
import sys,json,hashlib,copy
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts import build_sprite_style_selection_v4 as v4
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def main():
 out=W/'selection_standing_v4_checks.json';assert not out.exists();p=read(W/'staging_br_v23.json');candidate=W/'shibuki_audit/prepared_selection_standing01/ST0E_U1.ARC';new=candidate.read_bytes();assert sha(new)=='47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'
 source=ROOT/p['source_bin'];assert sha(source.read_bytes())==p['source_sha256'];old=read_disc(source,('ST0E_U1.ARC',))[0]['ST0E_U1.ARC']
 v4.check_selection(old,new,True,False,True,True)
 p['resources']['ST0E_U1.ARC'].update(path=candidate.relative_to(ROOT).as_posix(),after=sha(new));p['sync_x_selection_standing']=True
 v4.check_selection_body(p);v4.check_zero_selection_body(p)
 refused=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,AssertionError,RuntimeError)as e:refused.append({'case':name,'reason':str(e)})
  else:raise AssertionError('Unexpected acceptance: '+name)
 reject('missing_standing_scope',lambda:v4.check_selection(old,new,True,False,True,False))
 reject('non_boolean_scope',lambda:v4.check_selection(old,new,True,False,True,1))
 reject('conflicting_preservation',lambda:v4.check_selection(old,new,True,True,False,True))
 texture=bytearray(entry(new,0x10102));texture[50000]^=1;bad=replace_entry(new,0x10102,bytes(texture));reject('non_target_portrait_pixel',lambda:v4.check_selection(old,bad,True,False,True,True))
 texture=bytearray(entry(new,0x10102));texture[90112+4*8]^=1;bad=replace_entry(new,0x10102,bytes(texture));reject('shared_empty_tile4',lambda:v4.check_selection(old,bad,True,False,True,True))
 q=copy.deepcopy(p);q['resources']['ST0E_U1.ARC']['after']='0'*64;reject('wrong_selection_hash',lambda:v4.check_selection_body(q))
 report={'passed':True,'builder_sha256':sha((ROOT/'scripts/build_sprite_style_selection_v4.py').read_bytes()),'parent_selection_sha256':sha(old),'candidate_sha256':sha(new),'checked_standing_refs':list(range(1,9)),'standing_y_offsets':[-1,0,0,0,0,-1,-2,0],'br_ceremony_and_beam_preserved':True,'zero32_body_exact':True,'refusals':refused,'BIN_written':False,'runtime_verified':False}
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'refusals':len(refused),'report_sha256':sha(out.read_bytes())}))
if __name__=='__main__':main()
