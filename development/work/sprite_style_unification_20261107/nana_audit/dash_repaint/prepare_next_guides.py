"""대시 사격과 포스 원화용 새 몸체·원 총구·의상 기준 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
def body_path(n):
    folder='basic_contacts_v2'if n in(67,71,79,93)else'basic_last_registered_v2'if n==94 else'basic_second_contacts_v4'
    return D/folder/f'base_{n:03}.png'
def page(items,dest):
    cell=768;line=48;rows=(len(items)+1)//2;out=Image.new('RGBA',(cell*2,(cell+line)*rows));draw=ImageDraw.Draw(out);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    for k,(title,im)in enumerate(items):
        sprite=im.crop((112,112,208,208)).resize((cell,cell),Image.Resampling.NEAREST);x=k%2*cell;y=k//2*(cell+line);out.alpha_composite(sprite,(x,y+line));draw.text((x+18,y+8),title,font=font,fill=(90,100,110,255))
    out.save(dest)
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent');out=D/'next_guides_v1';need(not out.exists(),'Fresh output');out.mkdir();bodies={n:np.array(Image.open(body_path(n)))for n in(67,69,71,75,77,79,81,83,93,94)}
    for suffix,refs in [('a',(68,70,72,76)),('b',(78,80,82,84))]:
        page([(f'ORIGINAL MUZZLE + POSE {n}',a.composite(n)[0])for n in refs],out/f'firing_target_{suffix}.png')
        page([(f'NEW DETAILED BODY {n-1}',a.rgba(bodies[n-1]))for n in refs],out/f'firing_body_{suffix}.png')
    for suffix,refs in [('a',(67,69,71,75)),('b',(77,79,81,83)),('c',(93,94))]:
        page([(f'NEW BODY {n}',a.rgba(bodies[n]))for n in refs],out/f'fourth_body_{suffix}.png')
        page([(f'FOURTH POSE {n}',a.composite(n,15)[0])for n in refs],out/f'fourth_pose_{suffix}.png')
    page([(f'FOURTH DETAIL MASTER {n}',a.composite(n,15)[0])for n in(0,85,7,63)],out/'fourth_style_master.png')
    # An ordered static strip is an art comparison, not an executed animation.
    rows=[]
    for refs in [(67,69,71,75),(77,79,81,83),(93,94)]:
        rows.append(('새 기본 연속 자세',[(str(n),a.rgba(bodies[n]))for n in refs]))
    # The helper requires equal column counts; write the two layouts separately.
    helper.grid(rows[:2],out/'base_sequence.png',6);helper.grid(rows[2:],out/'airdash_sequence.png',8)
    write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'source_frames':{str(n):{'path':str(body_path(n).relative_to(ROOT)),'sha256':digest(body_path(n))}for n in bodies},'files':{f.name:digest(f)for f in out.glob('*.png')},'native_packed':False,'runtime_verified':False,'scope':'입력과 정적 자세순서 미리보기. 원래 시간표로 재생한 실기 증거가 아님.'})
if __name__=='__main__':main()
