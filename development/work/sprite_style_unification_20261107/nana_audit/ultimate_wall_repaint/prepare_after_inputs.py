"""정합된 새 벽몸체를 고정하고 기존 후폼 의상만 편집할 전신 입력을 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,digest,sha,need
WINDOW=(120,120,200,200)
def main():
 a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());out=D/'after_inputs_v1';out.mkdir(exist_ok=False)
 for page,keys in[('a',(55,57,59)),('b',(61,63,65))]:
  board=Image.new('RGBA',(1280,1280));frames=[]
  for i,n in enumerate(keys):
   p=D/'canonical_cases_probe_v2'/f'before_{n:03}.png';ar=np.array(Image.open(p));im=a.rgba(ar,16);board.alpha_composite(im.crop(WINDOW).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640));yy,xx=np.nonzero(ar);Y,X=np.indices(ar.shape);gy,gx=np.nonzero((ar==14)&(Y<160));frames.append({'ref':n,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'eye_world':[float(np.median(gx)-160),float(np.median(gy)-160)],'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)]})
  board.alpha_composite(a.composite(0,0)[0].crop(WINDOW).resize((640,640),Image.Resampling.NEAREST),(640,640));board.save(out/f'{page}_fixed_bodies.png');write(out/f'{page}_poses.json',frames)
 master=Image.new('RGBA',(1280,1280))
 for i,n in enumerate((0,33,37,53)):master.alpha_composite(a.composite(n,0)[0].crop(WINDOW).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640))
 master.save(out/'after_style_master.png');write(out/'manifest.json',{'parent_arc_sha256':sha(a.data),'target_refs':[55,57,59,61,63,65],'scale':8,'cell':[640,640],'window':WINDOW,'fourth_cell':'accepted after idle, reference only; never reuse generated idle','images':{p.name:digest(p)for p in out.glob('*.png')},'native_packed':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
