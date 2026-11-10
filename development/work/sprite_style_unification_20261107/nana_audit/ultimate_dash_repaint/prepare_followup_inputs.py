"""다음4대시 키와71발목 국소 보완용 원화/참조를 별도 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
from prepare_inputs import SRC,EXPECTED,WINDOW
def board(images):
 out=Image.new('RGBA',(1536,1536))
 for i,im in enumerate(images):out.alpha_composite(im.crop(WINDOW).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
 return out
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'followup_inputs_v1';out.mkdir(exist_ok=False);keys=(69,75,77,81)
 board([a.composite(n,15)[0]for n in keys]).save(out/'before_next4_targets.png')
 new=D/'before_first_registered_v2'
 board([a.composite(0,15)[0],a.rgba(np.array(Image.open(new/'before_067.png')),16),a.rgba(np.array(Image.open(new/'before_079.png')),16),a.composite(55,15)[0]]).save(out/'detail_master.png')
 basepath=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';need(digest(basepath)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','Base frozen');b=Archive(basepath.read_bytes())
 board([b.composite(n,0)[0]for n in keys]).save(out/'base_joint_reference.png')
 records=[]
 for n in keys:
  raw=np.array(Image.open(D/f'inputs_v1/before_{n:03}.png'));yy,xx=np.nonzero(raw==14);y=int(yy.min());x=int(np.median(xx[yy==y]));records.append({'ref':n,'native_eye_world':[x-160,y-160],'eye_rule':'topmost native green group, lower shoe accents excluded'})
 write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'refs':list(keys),'positions':records,'native_world_window':[-48,-48,48,48],'source_new_art':{'path':str((D/'before_first_v1/generated.png').relative_to(ROOT)),'sha256':digest(D/'before_first_v1/generated.png')},'source_base_arc_sha256':digest(basepath),'images':{p.name:digest(p)for p in out.glob('*.png')},'input_preparation_only':True})
 print(out)
if __name__=='__main__':main()
