"""새 몸체/총구와 포스 스타일 참조를 같은 원점의 생성 입력으로 구성한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write

def page(items,dest):
    cell=768;line=48;out=Image.new('RGBA',(cell*2,(cell+line)*2));draw=ImageDraw.Draw(out);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    for k,(title,im) in enumerate(items):
        sprite=im.crop((112,112,208,208)).resize((cell,cell),Image.Resampling.NEAREST);x=k%2*cell;y=k//2*(cell+line)
        out.alpha_composite(sprite,(x,y+line));draw.text((x+18,y+8),title,font=font,fill=(90,100,110,255))
    out.save(dest)
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent');out=D/'next_guides';out.mkdir(exist_ok=True)
    refs=tuple(range(33,55,2))
    def base(n):
        folder='basic_registered_v2'if n in(33,39,47,51)else('basic_landing_registered_v5'if n in(45,49,53)else'basic_middle_registered_v2')
        return Image.open(D/folder/f'base_{n:03}_rgba.png').convert('RGBA')
    page([(f'NEW BODY {n}',base(n))for n in(33,39,47,51)],out/'new_air_keys.png')
    page([(f'NEW BODY {n}',base(n))for n in(35,37,41,43)],out/'new_air_middle.png')
    page([(f'NEW BODY {n}',base(n))for n in(33,35,37,39)],out/'new_air_a.png')
    page([(f'NEW BODY {n}',base(n))for n in(41,43,45,47)],out/'new_air_b.png')
    page([(f'NEW BODY {n}',base(n))for n in(49,51,53)],out/'new_air_c.png')
    page([(f'FOURTH STYLE {n}',a.composite(n,15)[0])for n in(0,85,7,63)],out/'fourth_style_master.png')
    page([(f'FIRING TARGET {n}',a.composite(n)[0])for n in(34,36,38,40)],out/'firing_target_a.png')
    page([(f'FIRING TARGET {n}',a.composite(n)[0])for n in(42,44,46,48)],out/'firing_target_b.png')
    page([(f'FIRING TARGET {n}',a.composite(n)[0])for n in(50,52,54)],out/'firing_target_c.png')
    for name,rs in [('fourth_keys',(33,39,47,51)),('fourth_middle',(35,37,41,43)),('fourth_landing',(45,49,53))]:
        page([(f'FOURTH POSE {n}',a.composite(n,15)[0])for n in rs],out/(name+'.png'))
    write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'files':{f.name:digest(f)for f in sorted(out.glob('*.png'))},
       'generation_complete':False,'scope':'기존 실제 자세와 새 기본 몸체를 같은 원점에 배치한 입력. 새 포스·사격 그림 자체는 아직 생성하지 않음.',
       'fire_guides':'기존 팔 띠의 질감은 복사 대상이 아니며 실제 총구 위치와 겨드랑이/손목 도달 거리만 입력으로 사용한다.'})
if __name__=='__main__':main()
