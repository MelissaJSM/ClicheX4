"""Ultimate85/89 첫 의상 원화 고정 전체캔버스 등록. 의상 오류는 별도 검토."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
    s=H/'ultimate_standing_fire_inputs01';d=H/'ultimate_standing_fire_native01';need(not d.exists(),'새 폴더 필요');m=json.loads((s/'input.json').read_text('utf8'));g=s/'generated.png'
    need(sha(g.read_bytes())=='1d643d9184681197ada2a8267b98f438a743bbc4a0df5a8b9cd9c534e4330382','원화 변경')
    for name,digest in m['files'].items():need(sha((s/name).read_bytes())==digest,'입력 변경')
    p=ROOT/m['parent']['path'];need(sha(p.read_bytes())==m['parent']['sha256'],'부모 변경');a=Archive(p.read_bytes());original=Image.open(g).convert('RGBA');need(original.size==(1254,1254),'캔버스 불일치');samples=np.array(original.resize((192,192),Image.Resampling.NEAREST));rows=[];d.mkdir()
    for col,(form,mask,pal)in enumerate((('before',15,16),('after',0,0))):
        rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for row,n in enumerate((85,89)):
            cell=samples[row*96:(row+1)*96,col*96:(col+1)*96];ind=(1+((cell[:,:,:3].astype('int32')[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');ind[cell[:,:,3]<128]=0
            need(not(ind[0].any()or ind[-1].any()or ind[:,0].any()or ind[:,-1].any()),'셀 경계 침범');canvas=np.zeros((384,384),np.uint8);canvas[112:208,112:208]=ind;im=a.rgba(canvas,pal)
            Image.fromarray(canvas).save(d/f'{form}_{n:03}_indices.png');im.save(d/f'{form}_{n:03}.png');Image.fromarray(cell).save(d/f'{form}_{n:03}_sample_rgba.png');labs,_=label(ind>0,np.ones((3,3)));old=a.composite(n,mask)[0];pics.extend([(f'{n} old',old),(f'{n} new source',im)])
            rows.append({'ref':n,'form':form,'palette':pal,'old_metrics':metrics(old),'new_metrics':metrics(im),'components':sorted(map(int,np.bincount(labs.flat)[1:]),reverse=True),'rgba_sha256':sha(im.tobytes()),'indices_sha256':sha(canvas.tobytes()),'low_alpha_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'body_translation':[0,0],'contacts_pending':True})
        page(pics,a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'source_sha256':sha(g.read_bytes()),'parent_sha256':sha(a.data),'actual_size':list(original.size),'logical_canvas':[192,192],'global_scale':192/1254,'cell':[96,96],'origin':[48,48],'alpha_cutoff':128,'rows':rows,'arc_written':False,'costume_acceptance':False,'pending':'후폼 들린팔의 흰 소매 잔재 여부 실제 열람 필요. 공통머리·사지 및 정본총 등록 전.'})
    write(s/'generation_receipt.json',{'tool':'builtin imagegen','generated_sha256':sha(g.read_bytes()),'generated_source_path':'<LOCAL_PATH>','prompt_sha256':sha((s/'prompt.txt').read_bytes()),'actual_size':list(original.size),'inputs_actually_viewed':['edit_target.png','accepted_style.png','old_pose_context.png'],'original_preserved':True});print(json.dumps(rows))
if __name__=='__main__':main()
