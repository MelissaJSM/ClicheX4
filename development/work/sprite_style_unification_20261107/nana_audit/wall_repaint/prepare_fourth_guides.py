"""새 기본형 벽 자세를 좌표 그대로 포스 의상 생성 입력으로 구성한다."""
from pathlib import Path
import sys, json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parent/'native_restore'))
from preview_restore import Archive
A=Archive((D.parent/'base_run_repaint/packed_joint_v2/PL00_U.ARC').read_bytes())
def source(n):
    return D/('basic_contacts_probe_v3' if n in (55,57,61,65) else 'basic_remaining_contacts_v1')/f'base_{n:03d}.png'
def page(refs, dest):
    cols=2; rows=(len(refs)+1)//2; cell=768; label=48
    out=Image.new('RGBA',(cols*cell,rows*(cell+label)))
    draw=ImageDraw.Draw(out);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    for k,n in enumerate(refs):
        ar=np.asarray(Image.open(source(n)),dtype=np.uint8)
        im=A.rgba(ar).crop((112,112,208,208)).resize((cell,cell),Image.Resampling.NEAREST)
        x=k%2*cell;y=k//2*(cell+label)
        out.alpha_composite(im,(x,y+label));draw.text((x+18,y+8),f'POSE {n} - SAME BODY / CONTACTS',font=font,fill=(90,100,110,255))
    out.save(dest)
def main():
    page([55,57,61,65],D/'fourth_new_geometry_keys.png')
    page([59,63],D/'fourth_new_geometry_remaining.png')
    records={str(n):{'path':str(source(n).relative_to(D)), 'sha256':hashlib.sha256(source(n).read_bytes()).hexdigest()}for n in (55,57,59,61,63,65)}
    (D/'fourth_new_geometry_inputs.json').write_text(json.dumps({'scope':'새 기본형의 같은 원점·머리·벽손·발 접점. 포스 의상은 별도 새 원화 생성.','sources':records},ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
