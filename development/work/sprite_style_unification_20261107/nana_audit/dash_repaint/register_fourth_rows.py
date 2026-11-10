"""Compare per-leg same-row authored RGBA at fixed knee and shoe heights."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent; ROOT=D.parents[3]
sys.path[:0]=[str(D),str(D.parent/'native_restore'),str(D.parent/'air_repaint')]
from preview_restore import Archive,sha,write,need,helper
from prepare_air_joint_layers import spans,quantize_rgba_row
sys.path.insert(0,str(D))
from prepare_next_guides import body_path
START={67:10,69:13,77:12,79:12,81:7,83:8,93:9,94:3}
def main():
 p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());o=D/'fourth_row_rgba_probe_v1';need(not o.exists(),'Fresh');o.mkdir();pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],float);rows=[];proof=[]
 for n,start in START.items():
  b=np.array(Image.open(body_path(n)));f=np.array(Image.open(D/'fourth_contacts_probe_v2'/f'fourth_{n:03}.png'));new=f.copy();rgba=Image.open(D/'fourth_contacts_probe_v2'/f'source_rgba8_{n:03}.png').convert('RGBA');links=[];miss=[]
  for y in range(160+start,200):
   bs=spans(b[y]>0);fs=spans(f[y]>0)
   if not bs and not fs:continue
   if len(bs)!=len(fs):miss.append({'y':y-160,'base':len(bs),'fourth':len(fs)});continue
   for src,dst in zip(fs,bs):
    box=((int(src[0])-120)*8,(y-120)*8,(int(src[-1])+1-120)*8,(y+1-120)*8)
    vals,cov=quantize_rgba_row(rgba.crop(box),len(dst),pal);new[y,src]=0;new[y,dst]=vals;links.append({'y':y-160,'source':(src[[0,-1]]-160).tolist(),'target':(dst[[0,-1]]-160).tolist(),'source_rgba_box':box})
  full=np.where(new,new,b).astype(np.uint8);Image.fromarray(new).save(o/f'fourth_{n:03}.png');Image.fromarray(b).save(o/f'base_{n:03}.png');rows.append((str(n),[('새 기본 그대로',a.rgba(b)),('새 포스 원화',a.rgba(f,16)),('같은 행 원화 등록',a.rgba(full,16))]));proof.append({'ref':n,'unmatched':miss,'source_links':links,'base_exact':True})
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],o/f'comparison_{i//3+1}.png',7)
 write(o/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':proof,'candidate_only':True,'native_packed':False});print(json.dumps({r['ref']:r['unmatched']for r in proof}))
if __name__=='__main__':main()
