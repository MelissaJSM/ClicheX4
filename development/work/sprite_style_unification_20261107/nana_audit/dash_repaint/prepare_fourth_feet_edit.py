from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,write,digest
from prepare_next_guides import page,body_path
def main():
 p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'fourth_folded_feet_inputs';out.mkdir(exist_ok=True);target=Image.new('RGBA',(1536,768));draw=ImageDraw.Draw(target)
 for k,n in enumerate((71,75)):
  im=Image.open(D/'fourth_a_registered_v1'/f'source_{n:03}.png').convert('RGBA');scale=min(660/im.width,620/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);target.alpha_composite(im,(k*768+(768-im.width)//2,100+(620-im.height)//2));draw.text((k*768+20,20),f'EDIT ONLY LOWER LEGS {n}',fill=(90,100,110,255))
 target.save(out/'edit_target.png');page([(f'EXACT TWO BOOTS POSE {n}',a.rgba(np.array(Image.open(body_path(n)))))for n in(71,75)],out/'pose_guide.png')
 write(out/'manifest.json',{'files':{p.name:digest(p)for p in out.glob('*.png')},'purpose':'포스71/75의 숨겨진 두 번째 발을 실제 기본형 접점에 맞춘 국소 재작화 입력. 상체/베일 보존.'})
if __name__=='__main__':main()
