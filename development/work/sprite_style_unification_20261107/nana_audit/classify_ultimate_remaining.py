"""잔여140·208..212의 실제층과 원표 참조를 읽기 전용으로 분류한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
from scripts.export_sprite_playback import read_disc,at
def full(a,n,mask):
 z=a.layer(n)[0].copy()
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:
   b=a.layer(n,pb)[0];z[b>0]=b[b>0]
 return z
def main():
 out=N/'ultimate_remaining_classification01';out.mkdir(exist_ok=False);p=N/'ultimate_hover_repaint/packed_hover_candidate_v1/PL02_U.ARC';need(digest(p)=='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff','고정부모');a=Archive(p.read_bytes());refs=[140,208,209,210,211,212];m=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));plan=json.loads((N/'ultimate_nova_repaint/native_components_v1.json').read_text('utf8'));src=ROOT/plan['source_bin'];need(digest(src)==plan['source_sha256'],'원표source');exe=read_disc(src,['SLUS_005.61'])['SLUS_005.61'];rows=[];frames=[]
 for n in refs:
  forms=[]
  for name,mask in(('before',15),('after',0)):
   z=full(a,n,mask);idle=full(a,0,mask);yy,xx=np.nonzero(z);vals,cnt=np.unique(z[z>0],return_counts=True);colors={str(int(v)):int(c)for v,c in zip(vals,cnt)};samealpha=np.array_equal(z>0,idle>0);rec={'form':name,'mask':mask,'opaque':int((z>0).sum()),'colors':colors,'bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)]if len(xx)else None,'idle_alpha_exact':samealpha}
   if n in(208,209):rec['flat_idle_reproduction_exact']=samealpha and len(vals)==1
   if n==210 and len(xx):
    iy,ix=np.nonzero(idle);w=int(xx.max()-xx.min()+1);h=int(iy.max()-iy.min()+1);small=np.array(Image.fromarray((idle[iy.min():iy.max()+1,ix.min():ix.max()+1]>0).astype(np.uint8)).resize((w,h),Image.Resampling.NEAREST));v=np.zeros_like(z);top=int(yy.max()+1-h);left=int(xx.min());v[top:top+h,left:left+w]=np.where(small,int(vals[cnt.argmax()]),0);rec['idle_horizontal_squeeze_reproduction_exact']=np.array_equal(v,z);rec['original_current_width']=w;rec['kept_idle_height']=h
   Image.fromarray(z).save(out/f'{name}_{n:03}_indices.png');forms.append(rec)
  anim=[]
  for q in m['characters']['nana']['forms']['ultimate_after']['animations']:
   if any(s['frame_ref']==n for s in q['steps']):
    need(at(exe,int(q['table_address'],16)+4*q['id'],4).hex()==q['pointer_bytes'],'원표포인터');need(all(at(exe,int(s['address'],16),4).hex()==s['bytes']for s in q['steps']),'원스텝');anim.append({'id':q['id'],'steps':[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']]})
  frames.append({'ref':n,'forms':forms,'layers':{str(pb):{'opaque':int((a.layer(n,pb)[0]>0).sum()),'sha256':sha(a.layer(n,pb)[0].tobytes())}for pb in(0,5,6,7,8)},'native_animations':anim});rows.append((str(n),[('idle before',a.composite(0,15)[0]),('current before',a.composite(n,15)[0]),('current after',a.composite(n,0)[0]),('layer5',a.rgba(a.layer(n,5)[0],16))]))
 for i in range(0,6,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',5)
 write(out/'report.json',{'read_only':True,'source_arc':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'source_bin_sha256':plan['source_sha256'],'frames':frames,'historical_rule_source':{'path':'scripts/overhaul_sprites_state_layers.py','sha256':digest(ROOT/'scripts/overhaul_sprites_state_layers.py'),'function':'complete_effects: Flat departure silhouettes'},'native_table_bytes_exact':True,'new_game_execution':False,'new_art_created':False,'classification_pending_actual_visual_review':True,'scope':'현재층과idle 실루엣/가로압축 exact 및 실제 EXE 표 참조를 읽었다. 원US의고유그림·caller도달성·실제화면검증을 완료했다고 주장하지 않는다.'});print(json.dumps(frames,ensure_ascii=False))
if __name__=='__main__':main()
