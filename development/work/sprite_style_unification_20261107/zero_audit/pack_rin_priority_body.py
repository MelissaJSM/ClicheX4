"""Add accepted ground/rear/burst poses; victory5 remains a separate art candidate."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_riko_cloth as engine
from fit_rin_windows import fit_windows
P=D/'rin_extension/prepared_air_continuation2_v2/PL01_U.ARC';SHA='ffca3087c17c883e6383b0ff38417b003138d1614c8add8edb1b99199bf322df'
ART=D/'rin_extension/detail_priority_singles/registered_v3';OUT=D/'rin_extension/prepared_priority_body_v1'
EXPECTED_SHA={'b0_061':'715e54cda61f3864744bbaa542a9188443f7c3fb789cb72f8a5478e7b741c416','b0_174':'3767f840b951727c58d69435a322f80726d8ecf09bc9833b1971c1e2f22b3b2e','b1_183':'090e6406e338eb03417c2988e74e9addfa5ed7a0cb9354adeee39033cfb2b17e'}
MAP={(0,61):('b0_061',False),(0,174):('b0_174',False),(0,175):('b0_174',False),(0,176):('b0_174',True),(0,177):('b0_174',True),(1,182):('b1_183',False),(1,183):('b1_183',False)}
def mirror(a):
 z=np.zeros_like(a);y,x=np.nonzero(a);assert np.all((319-x>=0)&(319-x<384));z[y,319-x]=a[y,x];return z
def targets(arc):
 engine.native.need(engine.native.sha(arc)==SHA,'Wrong Rin42 source')
 masters={}
 for k,h in EXPECTED_SHA.items():
  p=ART/f'{k}_indices.png';engine.native.need(engine.native.sha(p.read_bytes())==h,'Changed accepted native art')
  a=np.array(Image.open(p));engine.native.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Invalid indices');masters[k]=a
 result={}
 for key,(k,flip)in MAP.items():
  b,n=key;mb,mn=int(k[1]),int(k[3:]);original=engine.native.render(arc,mb,mb*5,mn)[0];want=mirror(original)if flip else original
  engine.native.need(np.array_equal(engine.native.render(arc,b,b*5,n)[0],want),'Original alias/reflection differs')
  result[key]=mirror(masters[k])if flip else masters[k]
 g=engine.native.entry(arc,2)
 for b,n in list(result):
  bank=engine.native.graphics_bank(g,b);offset=bank['frames'][n]['offset']
  for f in bank['frames']:
   key=b,f['index']
   if f['offset']==offset and key not in result:
    engine.native.need(not(b==1 and 42<=key[1]<=49),'Partial alias group prohibited');result[key]=engine.native.render(arc,b,b*5,key[1])[0].copy()
 return result
def pack(c,b,n,raw,count,target):
 if(b,n)not in MAP:return raw,engine.records(c,b*5,n),{'type':'preserved_shared_support'}
 local,edits=fit_windows(c,n,raw,count,target,engine.native.packer.edit_visible_set,b*5)
 cp=engine.native.composition_frame(local,b*5,n);_,size,bb,_=engine.native.compose_indices(raw,count,cp)
 crop=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
 nr=engine.native.packer.edit_visible_set(raw,count,[(cp,crop.tobytes(),size)])
 return nr,engine.records(local,b*5,n),{'type':'visible_texel_edit','window_edits':edits,'hidden_global_cleanup':False}
def main():
 arc=P.read_bytes();tt=targets(arc);engine.PARENT=P;engine.PARENT_SHA=SHA;engine.OUT=OUT;engine.KEYS={k:(0,0,0)for k in tt};engine.get_targets=targets;engine.pack_frame=pack
 out,proof=engine.build(arc,tt);again,_=engine.build(arc,tt);engine.native.need(out==again,'Reproduction differs')
 proof.pop('heads_preserved_pixels_per_reference',None);proof.pop('source_3rd_saber9_and_rear28_preserved',None)
 for r in proof['changes']:r.pop('head_preserved',None)
 proof['previous42_exact']=True;proof['hidden_global_cleanup']=False
 OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:(0,0,0)for k in MAP};engine.boards(arc,out)
 proposal={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in MAP],'shared_support_refs':[f'b{b}_{n:03}'for b,n in tt if(b,n)not in MAP],'cumulative_main_refs':49,'verification':proof,'reproducible':True,'static_burst24_sync_required':True,'victory5_included':False,'game_changed':False,'gameplay_runtime_verified':False}
 (OUT/'proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha':proposal['after_sha256'],'layouts':proof['layouts']}))
if __name__=='__main__':main()
