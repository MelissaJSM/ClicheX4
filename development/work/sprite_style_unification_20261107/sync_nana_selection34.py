"""Update four existing selection copies from the reviewed native body poses."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ultimate_production import repack_parts
from src.psx_player import composition_frame
from src.psx_ui_atlas import aliased_composition,local_composition,repack_frames,tile_pixels
from src.psx_static_effect import compose_static
from scripts.discover_inputs import psx_arc
from scripts.build_sprite_style_selection_v2 import check_selection
from scripts.build_sprite_style_selection_v3 import check_selection_body
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
MAP={18:207,19:156,20:157,21:158}
def decode(texture,parts,n):
 c=aliased_composition(parts,2,n);px,size,bb,_=compose_static(texture,local_composition(c));z=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);out=np.zeros((384,384),np.uint8);yy,xx=np.nonzero(z);out[yy+bb[1]+160,xx+bb[0]+160]=z[yy,xx];return out,c,(size,bb)
def orient(v,n):
 out=np.zeros_like(v);yy,xx=np.nonzero(v)
 if n==18:out[yy-1,xx]=v[yy,xx]
 elif n in(19,20):out[yy,319-xx]=v[yy,xx]
 else:out=v.copy()
 return out
def main(out_name='nana_selection_sync34_03'):
 out=(W/out_name).resolve();assert out.is_relative_to(W)and not out.exists();out.mkdir();plan=read(W/'staging_rn_v34.json');src=ROOT/plan['source_bin'];assert sha(src.read_bytes())==plan['source_sha256']
 originals=read_disc(src,('PL00_U.ARC','COL0E_U1.ARC'))[0];before=Archive(originals['PL00_U.ARC']);after=Archive((ROOT/plan['resources']['PL00_U.ARC']['path']).read_bytes());assert sha(after.data)==plan['resources']['PL00_U.ARC']['after']
 path=ROOT/plan['resources']['ST0E_U1.ARC']['path'];ui=path.read_bytes();assert sha(ui)==plan['resources']['ST0E_U1.ARC']['after']=='3c1234593444c0be72413f2e6e81b0c049509eedcbb40bf4e4d6413613b16e11'
 assert entry(originals['COL0E_U1.ARC'],5)[512:544]==before.p[:32]==after.p[:32]
 g=entry(ui,0x10102);p=entry(ui,10);texture=g[90112:]
 offsets=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',p)[0]//4),p);lo=offsets[2];hi=min((v for v in offsets if v>lo),default=len(p));one=struct.pack('<I',4)+p[lo:hi]
 changes={};targets={};previous={}
 for n,body in MAP.items():
  previous[n]=decode(texture,p,n)[0];assert np.array_equal(previous[n],orient(before.layer(body)[0],n)),('Original copy not exact',n)
  targets[n]=orient(after.layer(body)[0],n);rr=[]
  for q in composition_frame(after.c,0,body)['parts']:
   fl,t,x,y=q['flags'],q['tile'],q['x'],q['y']
   if n==18:y-=1
   elif n in(19,20):fl^=64;x=-x-16
   rr.append(struct.pack('<BBbb',fl,t,x,y))
  changes[n]=b''.join(rr)
 positioned,slack=repack_parts(one,0,changes);small={}
 for n,z in targets.items():
  _,size,bb,covered=compose_static(texture,local_composition(composition_frame(positioned,0,n)))
  cut=z[bb[1]+160:bb[3]+160,bb[0]+160:bb[2]+160];assert np.count_nonzero(cut)==np.count_nonzero(z)
  small[n]=(cut.tobytes(),size)
 ng,np_,packing=repack_frames(texture,positioned,0,small,guard_uv_zero=True)
 newp=p[:lo]+np_[4:]+p[hi:];result=replace_entry(replace_entry(ui,0x10102,g[:90112]+ng),10,newp)
 assert len(result)==len(ui)and entry(result,0x10102)[:90112]==g[:90112]
 assert p[:lo]==newp[:lo]and p[hi:]==newp[hi:]
 preserved=[]
 for n in range(aliased_composition(p,2,0)['bank_frame_count']):
  old,oc,meta=decode(texture,p,n);new,nc,newmeta=decode(ng,newp,n)
  if n in targets:assert np.array_equal(new,targets[n]),('Target differs',n)
  else:
   assert meta==newmeta and np.array_equal(old,new),('Other display',n)
   assert len(oc['parts'])==len(nc['parts'])
   for a,b in zip(oc['parts'],nc['parts']):assert p[a['record_offset']:a['record_offset']+4]==newp[b['record_offset']:b['record_offset']+4]
   preserved.append(n)
 for e in psx_arc(ui):
  typ=int(e['type'],16)
  if typ not in(0x10102,10):assert entry(ui,typ)==entry(result,typ)
 check_selection(ui,result,False,False,False)
 dest=out/'ST0E_U1.ARC';dest.write_bytes(result)
 proposal=json.loads(json.dumps(plan));proposal['preserve_x_selection']=False;proposal['resources']['ST0E_U1.ARC'].update(path=dest.relative_to(ROOT).as_posix(),after=sha(result));check_selection_body(proposal)
 (out/'proposal_plan.json').write_text(json.dumps(proposal,indent=2)+'\n','utf8')
 for n,body in MAP.items():page([('old UI',before.rgba(previous[n])),('new UI',after.rgba(targets[n])),('new game '+str(body),after.composite(body)[0])],after.composite(0)[0],out/f'copy_{n}.png',cols=3,scale=5)
 report={'passed':True,'before':sha(ui),'after':sha(result),'parent_game':sha(before.data),'new_game':sha(after.data),'mapping':MAP,'transforms':{'18':'x,y-1','19/20':'319-x,y','21':'identity'},'all_four_rgba_and_original_origins_exact':True,'nonselected_ui_frames_preserved':preserved,'nonselected_record_bytes_preserved':True,'other_ui_banks_and_entries_exact':True,'portrait_and_background_bytes_preserved':90112,'composition_slack':slack,'packing':packing,'runtime_verified':False}
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({k:report[k]for k in ('passed','after','composition_slack')}))
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--out',default='nana_selection_sync34_03');args=parser.parse_args();main(args.out)
