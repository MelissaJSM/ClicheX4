"""Ultimate86/87/92 여섯셀 원화를 전체 캔버스 고정배율로 등록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    s=H/'ultimate_standing_recovery_inputs01';d=H/'ultimate_standing_recovery_native01'
    need(not d.exists(),'새 출력 필요')
    m=json.loads((s/'input.json').read_text('utf8'));receipt=json.loads((s/'generation_receipt.json').read_text('utf8'));g=s/'generated.png'
    need(sha(g.read_bytes())==receipt['generated_sha256'],'원화 변경')
    for name,digest in m['files'].items():need(sha((s/name).read_bytes())==digest,'입력 변경')
    p=ROOT/m['parent']['path'];need(sha(p.read_bytes())==m['parent']['sha256'],'부모 변경');a=Archive(p.read_bytes())
    original=Image.open(g).convert('RGBA');need(original.width==original.height,'정사각 전체 원화 필요')
    samples=np.array(original.resize((192,192),Image.Resampling.NEAREST));d.mkdir();rows=[]
    for col,(form,mask,pal) in enumerate((('before',15,16),('after',0,0))):
        rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for row,n in enumerate((86,87,92)):
            cell=samples[row*64:(row+1)*64,col*96:(col+1)*96]
            ind=(1+((cell[:,:,:3].astype('int32')[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');ind[cell[:,:,3]<128]=0
            need(not(ind[0].any() or ind[-1].any() or ind[:,0].any() or ind[:,-1].any()),'셀 경계 침범')
            z=np.zeros((384,384),np.uint8);z[128:192,112:208]=ind;im=a.rgba(z,pal)
            Image.fromarray(z).save(d/f'{form}_{n:03}_indices.png');im.save(d/f'{form}_{n:03}.png');Image.fromarray(cell).save(d/f'{form}_{n:03}_sample_rgba.png')
            labs,_=label(ind>0,np.ones((3,3)));old=a.composite(n,mask)[0]
            pics.extend([(f'{n} 기존',old),(f'{n} 새 원화',im)])
            rows.append({'ref':n,'form':form,'palette':pal,'old_metrics':metrics(old),'new_metrics':metrics(im),'components':sorted(map(int,np.bincount(labs.flat)[1:]),reverse=True),'rgba_sha256':sha(im.tobytes()),'indices_sha256':sha(z.tobytes()),'low_alpha_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'body_translation':[0,0],'contacts_pending':True})
        page(pics,a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'source_sha256':sha(g.read_bytes()),'parent_sha256':sha(a.data),'actual_size':list(original.size),'logical_canvas':[192,192],'global_scale':192/original.width,'cell':[96,64],'origin':[48,32],'alpha_cutoff':128,'rows':rows,'arc_written':False,'costume_acceptance':False,'pending':'각기 다른 반동/복귀3자세의 손발·의상·총열·공통부 검토 전.87/92 대기별칭 아님.'})
    print(json.dumps(rows))
if __name__=='__main__':main()
