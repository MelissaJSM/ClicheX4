"""Classify PL00 flashes/return beams independently of the PL02 assumptions."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
from scripts.c01_audio_build import read_disc
from scripts.export_sprite_playback import at
from src.psx_player import composition_frame
sha=lambda b:hashlib.sha256(b).hexdigest()
def full(a,n,mask):
 z=a.layer(n,0)[0].copy()
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:
   q=a.layer(n,pb)[0];z[q>0]=q[q>0]
 return z
def main():
 out=W/'root_nana_base_effect_audit01';out.mkdir(exist_ok=False);cp=W/'root_nana_hover/packed_hover_final01/PL00_U.ARC';assert sha(cp.read_bytes())=='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c';a=Archive(cp.read_bytes())
 original=ROOT/'MegaMan X4.bin';assert sha(original.read_bytes())=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b';us=Archive(read_disc(original,('PL00_U.ARC',))[0]['PL00_U.ARC'])
 src=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v41/rin_nana.bin';assert sha(src.read_bytes())=='e765577ac65cff3348a76ab0d2719ea96471b2c7895a35ac5a3c428db87385b3';exe=read_disc(src,('SLUS_005.61',))[0]['SLUS_005.61']
 animations=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'))['characters']['nana']['forms']['base']['animations'];rows=[];frames=[]
 for n in(140,208,209,210,211,212):
  forms=[]
  for form,mask in(('base',0),('fourth',15)):
   z=full(a,n,mask);idle=full(a,0,mask);vals,cnt=np.unique(z[z>0],return_counts=True);yy,xx=np.nonzero(z);iy,ix=np.nonzero(idle)
   row={'form':form,'mask':mask,'pixels':int((z>0).sum()),'palette_indices':{str(int(v)):int(c)for v,c in zip(vals,cnt)},'idle_alpha_exact':bool(np.array_equal(z>0,idle>0)),'idle_missing_alpha':int(np.count_nonzero((idle>0)&(z==0))),'outside_idle_alpha':int(np.count_nonzero((idle==0)&(z>0))),'bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)]}
   if n==210:
    width=int(xx.max()-xx.min()+1);height=int(iy.max()-iy.min()+1);sm=np.array(Image.fromarray((idle[iy.min():iy.max()+1,ix.min():ix.max()+1]>0).astype(np.uint8)).resize((width,height),Image.Resampling.NEAREST));q=np.zeros_like(z);top=int(yy.max()+1-height);left=int(xx.min());q[top:top+height,left:left+width]=np.where(sm,int(vals[cnt.argmax()]),0);row.update(idle_horizontal_squeeze_exact=bool(np.array_equal(q,z)),idle_height=height,width=width)
   forms.append(row)
  tables=[]
  for q in animations:
   if not any(s['frame_ref']==n for s in q['steps']):continue
   assert at(exe,int(q['table_address'],16)+4*q['id'],4).hex()==q['pointer_bytes']
   for s in q['steps']:assert at(exe,int(s['address'],16),4).hex()==s['bytes']
   tables.append({'id':q['id'],'steps':q['steps']})
  record={'ref':n,'forms':forms,'native_tables':tables}
  if n in(211,212):
   record['original_US_world_alpha_exact']=all(np.array_equal(a.layer(n,pb)[0]>0,us.layer(n,pb)[0]>0)for pb in(0,5,6,7,8))
   record['original_US_parts_semantic_exact']=all([{k:p[k]for k in('flags','tile','x','y')}for p in composition_frame(a.c,pb,n)['parts']]==[{k:p[k]for k in('flags','tile','x','y')}for p in composition_frame(us.c,pb,n)['parts']]for pb in(0,5,6,7,8))
  frames.append(record);rows.append((str(n),[('base idle',a.composite(0,0)[0]),('base current',a.composite(n,0)[0]),('Fourth idle',a.composite(0,15)[0]),('Fourth current',a.composite(n,15)[0])]))
 for i in range(0,6,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',5)
 report={'read_only':True,'source_arc':cp.relative_to(ROOT).as_posix(),'candidate_sha256':sha(cp.read_bytes()),'original_US_PL00_sha256':sha(us.data),'source_bin_sha256':sha(src.read_bytes()),'exe_sha256':sha(exe),'native_table_bytes_exact':True,'frames':frames,'runtime_verified':False,'new_art_created':False,'visual_review_pending':True}
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps([{'ref':q['ref'],'forms':q['forms']}for q in frames],ensure_ascii=False))
if __name__=='__main__':main()
