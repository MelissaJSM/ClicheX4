from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write
from prepare_next_guides import body_path
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());out=D/'fourth_contact_grids_v1';out.mkdir(exist_ok=True);reports=[]
    for n in(67,69,71,75,77,79,81,83):
        fdir=D/('fourth_a_registered_v1'if n<77 else'fourth_b_registered_v1');b=np.array(Image.open(body_path(n)));f=np.array(Image.open(fdir/f'fourth_{n:03}.png'));sheet=Image.new('RGB',(960,576),(181,194,204));d=ImageDraw.Draw(sheet)
        for k,ar in enumerate((b,f)):
            rgba=a.rgba(ar,0 if k==0 else 16).crop((132,134,192,200)).resize((480,528),Image.Resampling.NEAREST);sheet.paste(rgba,(480*k,24),rgba);d.text((480*k+8,6),f'{n} '+('base'if k==0 else'fourth'),fill='black')
            for x in range(-28,33,4):
                xx=(x+28)*8+480*k;d.line((xx,24,xx,552),fill=(150,170,185));d.text((xx+1,554),str(x),fill='black')
            for y in range(-26,41,4):
                yy=(y+26)*8+24;d.line((480*k,yy,480*k+479,yy),fill=(150,170,185));d.text((480*k+2,yy+1),str(y),fill='black')
        sheet.save(out/f'contact_{n:03}.png')
        reports.append({'ref':n,'base_sha256':sha(b.tobytes()),'fourth_sha256':sha(f.tobytes())})
    write(out/'manifest.json',{'frames':reports,'scope':'직접등록 눈/관절/발 접점 읽기 전용 확대'});print(str(out))
if __name__=='__main__':main()
