"""Compare locally registered authored folded-leg shading; no new art."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,need,write,helper,digest
from register_page import register
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());td=D/'joint_layers_probe_v6';out=D/'fold39_detail_probe_v1';need(not out.exists(),'Fresh');out.mkdir();old=np.array(Image.open(td/'full_039.png'));source=D/'fourth_a_registered_v1/source_039.png';art=Image.open(source).convert('RGBA');pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);yy,xx=np.indices(old.shape);x=xx-160;y=yy-160;allowed=np.isin(old,[10,11,12])&(y>=1)&(y<=10)&(x>=-7)&(x<=7);rows=[];report=[]
    specs=[('fold_a',(32,278,176,396),(-7,0,7,11)),('fold_b',(32,282,166,393),(-7,0,6,11)),('fold_c',(32,288,166,393),(-7,1,6,11))]
    for name,box,dest in specs:
        x0,y0,x1,y1=dest;sample=register(art.crop(box),(x1-x0,y1-y0),pal,'area_vote');idx=np.zeros_like(old);idx[160+y0:160+y1,160+x0:160+x1]=sample;mask=allowed&(idx>0);candidate=old.copy();candidate[mask]=idx[mask];need(np.array_equal(candidate>0,old>0),'Alpha');Image.fromarray(candidate).save(out/f'{name}.png');Image.fromarray(mask).save(out/f'{name}_mask.png');a.rgba(candidate,16).save(out/f'{name}_rgba.png');report.append({'name':name,'source_crop':box,'target_world_box':dest,'source_sha256':digest(source),'changed_pixels':int(np.count_nonzero(candidate!=old)),'mask_sha256':sha(mask.tobytes()),'output_indexed_sha256':sha(candidate.tobytes()),'alpha_exact':True,'base_untouched':True});rows.append((name,[('새 기본 그대로',a.rgba(np.array(Image.open(td/'layer0_039.png')))),('이전 포스',a.rgba(old,16)),('같은 포즈 원화의 접힌 다리 명암',a.rgba(candidate,16))]))
    helper.grid(rows,out/'comparison.png',9);write(out/'manifest.json',{'source':source.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'candidates':report,'scope':'39 국소 원화 등록 미술 비교. 기존 알파/기본층을 바꾸지 않음. 후보 수용 전, 패킹 미실행.'})
if __name__=='__main__':main()
