from pathlib import Path
import sys,json,hashlib,copy
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts import build_sprite_style_selection_v5 as v5
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from src.psx_ui_atlas import aliased_composition
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def main():
 out=W/'selection_standing_v5_checks.json';assert not out.exists()
 p=read(W/'staging_rn_v37.json');candidate=W/'root_nana_selection8/sync_spares02/ST0E_U1.ARC';new=candidate.read_bytes();assert sha(new)=='55b5d04d9a3452f2f12fe5ab21024de58c61f43eaa8b078f873ce4c7d2182f52'
 source=ROOT/p['source_bin'];assert sha(source.read_bytes())==p['source_sha256'];old=read_disc(source,('ST0E_U1.ARC',))[0]['ST0E_U1.ARC']
 v5.check_selection(old,new,True,False,False,True)
 p['resources']['ST0E_U1.ARC'].update(path=candidate.relative_to(ROOT).as_posix(),after=sha(new));p['sync_x_selection_standing']=True
 v5.check_selection_body(p);v5.check_zero_selection_body(p)
 br=read(W/'staging_br_v24.json');v5.check_selection_body(br);v5.check_zero_selection_body(br)
 refused=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,AssertionError,RuntimeError)as e:refused.append({'case':name,'reason':str(e)})
  else:raise AssertionError('Unexpected acceptance: '+name)
 reject('missing_standing_scope',lambda:v5.check_selection(old,new,True,False,False,False))
 reject('non_boolean_scope',lambda:v5.check_selection(old,new,True,False,False,1))
 reject('conflicting_preservation',lambda:v5.check_selection(old,new,True,True,False,True))
 texture=bytearray(entry(new,0x10102));texture[50000]^=1;bad=replace_entry(new,0x10102,bytes(texture));reject('non_target_portrait_pixel',lambda:v5.check_selection(old,bad,True,False,False,True))
 texture=bytearray(entry(new,0x10102));texture[90112]^=1;bad=replace_entry(new,0x10102,bytes(texture));reject('shared_tile0',lambda:v5.check_selection(old,bad,True,False,False,True))
 q=copy.deepcopy(p);q['resources']['ST0E_U1.ARC']['after']='0'*64;reject('wrong_selection_hash',lambda:v5.check_selection_body(q))
 parts=bytearray(entry(new,10));frame=aliased_composition(parts,2,1)
 for part in frame['parts']:parts[part['record_offset']+3]=(parts[part['record_offset']+3]+1)%256
 bad=replace_entry(new,10,bytes(parts));wrong=W/'root_nana_selection8/wrong_y1_refusal.ARC';assert not wrong.exists();wrong.write_bytes(bad)
 q=copy.deepcopy(p);q['resources']['ST0E_U1.ARC'].update(path=wrong.relative_to(ROOT).as_posix(),after=sha(bad));reject('BR_like_wrong_y1_on_Nana',lambda:v5.check_selection_body(q))
 r={'passed':True,'builder_sha256':sha((ROOT/'scripts/build_sprite_style_selection_v5.py').read_bytes()),'parent_selection_sha256':sha(old),'candidate_sha256':sha(new),'checked_standing_refs':list(range(1,9)),'standing_y_offsets':[0]*8,'BR24_measured_origins_regression':True,'RN_ceremony_origins_preserved':True,'zero32_body_exact_both_versions':True,'refusals':refused,'BIN_written':False,'runtime_verified':False}
 out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'refusals':len(refused),'sha256':sha(out.read_bytes())}))
if __name__=='__main__':main()
