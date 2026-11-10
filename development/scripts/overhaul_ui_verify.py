"""독립 재현, 실제 자원 범위, 병합 충돌 및 위험 입력 거부 검사."""
import json,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_inventory import D,load
from scripts.overhaul_ui_fixes import loading,life,require
from scripts.overhaul_ui_hud import artwork,patch
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import all_compositions
from scripts.discover_inputs import sha256,psx_arc

def main():
 out=D/'verification.json';require(not out.exists(),'Existing verification must not be overwritten');checks={};negative=[];resources=0
 def rejects(name,f):
  try:f()
  except (ValueError,AssertionError):negative.append(name)
  else:raise AssertionError('Failed to reject '+name)
 for project in ('ver_buki_riko','ver_rin_nana'):
  old,rr=load(project);delta={};per=[]
  for a,b in (('fixes_v1','fixes_repro_v1'),('hud_v2','hud_repro_v2')):
   first=json.loads((D/a/project/'proposal.json').read_text('utf8'));second=json.loads((D/b/project/'proposal.json').read_text('utf8'))
   require(first['baseline']==second['baseline']and first['baseline_sha256']==second['baseline_sha256'],'Wrong baseline')
   for name,r in first['files'].items():
    data=(ROOT/r['path']).read_bytes();data2=(ROOT/second['files'][name]['path']).read_bytes();require(data==data2 and sha256(data)==r['after'],'Reproduction differs');require(sha256(old[name])==r['before'] and rr[name]==r['record']and len(data)==len(old[name]),'Parent record differs');resources+=1
    offsets={i:v for i,(u,v)in enumerate(zip(old[name],data))if u!=v}
    prior=delta.setdefault(name,{})
    require(all(i not in prior or prior[i]==v for i,v in offsets.items()),'Cross-fix byte conflict');prior.update(offsets)
    if a.startswith('hud'):
     for e in psx_arc(old[name]):
      if e['type']!='0x10206':require(entry(data,int(e['type'],16))==entry(old[name],int(e['type'],16)),'HUD changed nontexture resource')
    if name.startswith('COL'):
     x,y=entry(old[name],5),entry(data,5);require(x[:352]==y[:352]and x[384:]==y[384:],'Life palette changed outside row11')
    per.append({'component':a,'resource':name,'reproduced':True,'changed_bytes':len(offsets)})
  checks[project]={'reproduction':per,'merged_resource_count':len(delta),'merged_changed_bytes':sum(map(len,delta.values())),'byte_conflicts':0}
  exe=bytearray(old['SLUS_005.61']);exe[0xded0c]^=1;rejects(project+'_wrong_loading_coords',lambda:loading(bytes(exe)))
  arc=old['PL00_U.ARC'];pal=entry(old['COL00_0X.ARC'],5)[544:576];symbols,_=artwork(pal);symbol=symbols['shibuki'if project=='ver_buki_riko'else'nana'];bad=symbol.copy();bad[0,0]=16;rejects(project+'_non_4bpp_HUD',lambda:patch(arc,bad))
  parts=bytearray(entry(arc,3));comps=all_compositions(parts);tile=comps[1,69]['parts'][0];p=comps[1,59]['parts'][0];o=p['record_offset'];parts[o:o+2]=bytes(((p['flags']&~3)|tile['page'],tile['tile']));mut=replace_entry(arc,3,bytes(parts));rejects(project+'_shared_HUD_tile',lambda:patch(mut,symbol))
 z,_=load('ver_buki_riko');raw=z['PL01_U.ARC'];parts=bytearray(entry(raw,3));p=next(p for p in all_compositions(parts)[3,89]['parts']if p['clut']==1);parts[p['record_offset']]&=~12;rejects('wrong_Riko_life_CLUT',lambda:life(replace_entry(raw,3,bytes(parts)),'riko'))
 result={'passed':True,'reproduced_resources':resources,'negative_rejections':negative,'projects':checks,'runtime_verified':False}
 out.write_text(json.dumps(result,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'reproduced_resources':resources,'negative_rejections':len(negative)}))
if __name__=='__main__':main()
