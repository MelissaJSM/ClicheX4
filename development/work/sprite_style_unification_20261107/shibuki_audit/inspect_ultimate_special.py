"""새 두 의상의 같은 원점 좌표와 색인을 확대하여 공통부 마스크를 검토."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive

def main():
    out=H/'ultimate_special_inspection01';need(not out.exists(),'Fresh inspection');out.mkdir()
    arc=Archive((H/'prepared_ultimate_return01/PL02_U.ARC').read_bytes());rows=[]
    for ref in (95,97):
        plate=Image.new('RGB',(1720,1060),(25,31,40));d=ImageDraw.Draw(plate)
        for col,(form,pal) in enumerate((('before',16),('after',0))):
            source=H/f'ultimate_special_native01/{form}_{ref:03}_indices.png';a=np.array(Image.open(source));im=arc.rgba(a,pal)
            crop=im.crop((139,133,181,184)).resize((840,1020),Image.Resampling.NEAREST)
            left=col*860+20;plate.paste(crop,(left,30),crop)
            for i in range(43):
                x=left+i*20;d.line((x,30,x,1050),fill=(58,64,73))
                if i<42 and i%2==0:d.text((x,15),str(i-21),fill='white')
            for j in range(52):
                y=30+j*20;d.line((left,y,left+840,y),fill=(58,64,73))
                if j<51 and j%2==0:d.text((left-20,y),str(j-27),fill='white')
            for y,x in zip(*np.nonzero(a[133:184,139:181])):
                v=int(a[y+133,x+139]);d.text((left+x*20+4,30+y*20+4),hex(v)[2:].upper(),fill=(20,20,20) if v in (4,5,6,10,11) else (200,240,220))
            d.text((left+350,2),f'{form} {ref}',fill='white')
            rows.append({'form':form,'ref':ref,'source':source.relative_to(ROOT).as_posix(),'sha256':sha(source.read_bytes())})
        plate.save(out/f'{ref:03}_grid.png')
    write(out/'report.json',{'rows':rows,'scope':'읽기 전용 색인/원점 확대. 원화 또는 후보 수정 없음.'})

if __name__=='__main__':main()
