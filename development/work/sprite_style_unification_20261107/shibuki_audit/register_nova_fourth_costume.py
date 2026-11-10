"""국소 포스 원화의 전체 캔버스 고정 등록. 실제 알파 후광은 수치로 남긴다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
    s=H/'nova_fourth_costume_inputs01';d=H/'nova_fourth_costume_native01';need(not d.exists(),'새 출력만')
    g=s/'generated.png';src=Path('<LOCAL_PATH>')
    need(not g.exists(),'원화 보존');g.write_bytes(src.read_bytes());im=Image.open(g).convert('RGBA');need(im.size==(1536,1024),'원비율 확인')
    m=json.loads((s/'input.json').read_text('utf8'))
    for n,v in m['files'].items():need(sha((s/n).read_bytes())==v,'입력 변경')
    p=ROOT/m['parent']['path'];need(sha(p.read_bytes())==m['parent']['sha256'],'부모 변경');a=Archive(p.read_bytes())
    write(s/'generation_receipt.json',{'tool':'builtin image_gen','source_default_path':str(src),'sha256':sha(g.read_bytes()),'actual_size':list(im.size),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'accepted':False,'policy':'전체 새몸체 교체가 아닌 포스 의상 국소 donor. 알파/의미영역 검토 전.'})
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[16:32]],np.int32)
    sm=np.array(im.resize((192,128),Image.Resampling.NEAREST));d.mkdir();pics=[];rows=[]
    for col,n in enumerate((213,215)):
        cell=sm[:,col*96:(col+1)*96];ind=(1+((cell[:,:,:3].astype('int32')[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');ind[cell[:,:,3]<128]=0
        z=np.zeros((384,384),np.uint8);z[96:224,112:208]=ind;out=a.rgba(z,16);old=Image.open(H/f'nova_base_native01/fourth_{n:03}.png').convert('RGBA');labs,_=label(ind>0,np.ones((3,3)))
        Image.fromarray(z).save(d/f'fourth_{n:03}_indices.png');out.save(d/f'fourth_{n:03}.png');Image.fromarray(cell).save(d/f'fourth_{n:03}_sample_rgba.png')
        rows.append({'ref':n,'source_metrics':metrics(old),'donor_metrics':metrics(out),'components':sorted(map(int,np.bincount(labs.flat)[1:]),reverse=True),'low_alpha_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'opaque_edge_samples':int((cell[0,:,3]>=128).sum()+(cell[-1,:,3]>=128).sum()+(cell[:,0,3]>=128).sum()+(cell[:,-1,3]>=128).sum()),'rgba_sha256':sha(out.tobytes())});pics.extend([(f'{n} 기존 새몸',old),(f'{n} 국소 donor',out)])
    page(pics,a.composite(0,15)[0],d/'comparison.png',cols=2,scale=5)
    write(d/'report.json',{'source_sha256':sha(g.read_bytes()),'actual_size':list(im.size),'global_scale':1/8,'logical_canvas':[192,128],'cell':[96,128],'origin':[48,64],'alpha_cutoff':128,'rows':rows,'local_composition_pending':True,'arc_written':False});print(json.dumps(rows))
if __name__=='__main__':main()
