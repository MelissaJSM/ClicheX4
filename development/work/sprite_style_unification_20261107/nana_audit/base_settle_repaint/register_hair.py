"""새 머릿결 원화의 내부 색 표본만 고정 좌표에 등록한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
spec=importlib.util.spec_from_file_location('hair_quantizer',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
# 세계좌표의 뒷머리 내부. 손·목·옷·검은 베일은 범위와 기존 색 의미로 제외한다.
SPANS={
 'base':{-14:(0,2),-13:(0,3),-12:(0,4),-11:(1,5),-10:(2,5),-9:(5,6),-8:(6,7),-7:(7,9),-6:(7,9),-5:(7,10),-4:(5,10),-3:(1,10),-2:(2,11),-1:(3,11),0:(4,11),1:(4,11),2:(3,11),3:(3,8),4:(7,7)},
 'fourth':{-14:(0,1),-13:(0,2),-12:(0,2),-11:(2,3),-10:(2,4),-9:(3,4),-8:(4,5),-7:(4,5),-6:(5,5),-5:(5,6),-4:(6,7),-3:(6,7),-2:(7,7),-1:(7,8),0:(7,11),1:(7,11),2:(6,10),3:(7,7),4:(7,8)}
}
def main():
 meta=json.loads((D/'hair_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['style_arc'];need(digest(p)==meta['style_arc_sha256'],'스타일 부모');a=Archive(p.read_bytes())
 art=D/'hair_v1/generated.png';need(digest(art)=='f889f6feabe92db02f10b15996e60340fd5709feb86dd6f3b963bb17cf1396b0','머리 원화');im=Image.open(art).convert('RGBA');need(im.size==(1536,1024),'고정 원화 크기')
 write(art.parent/'generation.json',{'tool':'builtin image_gen','sha256':digest(art),'source_path':'<LOCAL_PATH>','prompt':'../hair_inputs_v1/prompt.txt','size':list(im.size),'scope':'기본/포스138 뒷머리 내부 명암 국소 편집. 생성된 다른 부위는 미채택.','native_packed':False})
 out=D/'hair_registered_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 for col,form in enumerate(('base','fourth')):
  start=16 if col else 0;src=D/'contacts_probe_v1'/f'{form}_138_indices.png';old=np.array(Image.open(src));pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  donor=np.zeros_like(old);crop=[col*768,0,(col+1)*768,1024];donor[96:224,112:208]=reg.register(im.crop(crop),(96,128),pal,'area_vote')
  mask=np.zeros_like(old,dtype=bool)
  for y,(lo,hi) in SPANS[form].items():mask[y+160,lo+160:hi+161]=True
  mask &= np.isin(old,(5,6,7,8,9))
  valid=mask & np.isin(donor,range(1,10));new=old.copy();new[valid]=donor[valid]
  need(np.array_equal(new>0,old>0),'전체 윤곽 보존');need(np.array_equal(new[~mask],old[~mask]),'머리 밖 exact')
  links=[{'world':[int(x-160),int(y-160)],'before':int(old[y,x]),'source':int(donor[y,x])}for y,x in np.argwhere(new!=old)]
  for name,z in((form,new),(form+'_donor',donor),(form+'_mask',mask.astype(np.uint8))):Image.fromarray(z).save(out/f'{name}_138_indices.png')
  a.rgba(new,start).save(out/f'{form}_138_rgba.png')
  rows.append((form,[('idle',a.composite(0,15 if col else 0)[0]),('standing89',a.composite(89,15 if col else 0)[0]),('previous138',a.rgba(old,start)),('hair only',a.rgba(new,start)),('full donor / unused',a.rgba(donor,start))]))
  records.append({'form':form,'source_crop':crop,'source_indices_sha256':sha(donor.tobytes()),'previous_path':src.relative_to(ROOT).as_posix(),'previous_sha256':digest(src),'mask_sha256':sha(mask.tobytes()),'spans':SPANS[form],'hair_cells':int(mask.sum()),'changed_cells':len(links),'source_links':links,'ignored_zero_or_nonhair_donor':[[int(x-160),int(y-160),int(donor[y,x])]for y,x in np.argwhere(mask&~valid)],'alpha_exact':True,'outside_hair_exact':True,'output_sha256':sha(new.tobytes())})
 helper.grid(rows,out/'comparison.png',7)
 write(out/'manifest.json',{'generated_path':art.relative_to(ROOT).as_posix(),'generated_sha256':digest(art),'source_size':list(im.size),'method':'전체 고정96×128 면적투표 후 기존 뒷머리 색 의미영역 안의 같은 좌표 원화 표본만 등록. 윤곽·눈·몸·권총·손발 불변.','frames':records,'native_packed':False,'runtime_verified':False})
 print(json.dumps([{'form':q['form'],'hair':q['hair_cells'],'changed':q['changed_cells'],'ignored':q['ignored_zero_or_nonhair_donor']}for q in records]))
if __name__=='__main__':main()
