"""100 목/맨팔 의미 경계의 원화 및 색인 읽기 비교."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,digest

def main():
    out=D/'ultimate_neck_audit_v1';out.mkdir(exist_ok=False)
    u=Archive((N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC').read_bytes())
    paths=[D/'ultimate_weapon_probe_v1/before_100_indices.png',D/'ultimate_weapon_probe_v1/after_100_indices.png',D/'ultimate_costume_pair_probe_v5/after_100.png']
    arrays=[np.array(Image.open(p))for p in paths]
    x0,y0,x1,y1=-5,-16,12,-4;scale=28
    canvas=Image.new('RGB',((x1-x0)*scale*3,(y1-y0)*scale+40),(180,190,195));dr=ImageDraw.Draw(canvas)
    for k,(name,a)in enumerate(zip(('before','after donor','v5 result'),arrays)):
        rgba=u.rgba(a,16 if k==0 else 0)
        crop=rgba.crop((160+x0,160+y0,160+x1,160+y1)).resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST)
        canvas.paste(crop,(k*(x1-x0)*scale,40),crop)
        dr.text((k*(x1-x0)*scale+4,5),name,fill='black')
        for y in range(y0,y1):
            for x in range(x0,x1):
                px=k*(x1-x0)*scale+(x-x0)*scale;py=40+(y-y0)*scale
                dr.rectangle((px,py,px+scale-1,py+scale-1),outline=(90,100,100))
                dr.text((px+2,py+2),str(a[160+y,160+x]),fill='white'if a[160+y,160+x]<8 else 'black')
    canvas.save(out/'indexed_comparison.png')
    rows=[]
    for y in range(y0,y1):
        for x in range(x0,x1):
            vals=[int(a[160+y,160+x])for a in arrays]
            if vals[0]!=vals[1]:rows.append({'world':[x,y],'before_donor_final':vals})
    write(out/'report.json',{'sources':[{str(p.relative_to(ROOT)):digest(p)}for p in paths],'box':[x0,y0,x1,y1],'different_cells':rows,'scope':'색상차만으로 의미를 정하지 않고 원화와 함께 검토하는 읽기 자료.'})
    print(json.dumps(rows))
if __name__=='__main__':main()
