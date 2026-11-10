"""내장 생성 결과를 보존하고 전체캔버스 고정격자로 등록한다."""
from pathlib import Path
import sys,json,shutil,argparse,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
reg=load('nova_quantizer',N/'base_run_repaint/register_page.py');metric=load('nova_metric',N/'ultimate_victory_repaint/register_page.py')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('page',choices=['a','b']);ap.add_argument('generated',type=Path);args=ap.parse_args();inp=D/f'{args.page}_inputs_v1';meta=json.loads((inp/'manifest.json').read_text('utf8'));p=ROOT/meta['parent_arc'];need(digest(p)==meta['parent_sha256'],'부모');a=Archive(p.read_bytes());out=D/f'{args.page}_v1';out.mkdir(exist_ok=True);art=out/'generated.png';need(not art.exists() or digest(art)==digest(args.generated),'existing generation differs');shutil.copyfile(args.generated,art);need(digest(art)==digest(args.generated),'원본복사');im=Image.open(art).convert('RGBA');cols,nrows=meta.get('layout',[2,2]);need(im.width*nrows==im.height*cols and im.width%cols==0,'fixed grid aspect');size=im.width//cols;dest=D/f'{args.page}_registered_v1';dest.mkdir(exist_ok=False);rows=[];proof=[]
 for q in meta['frames']:
  form,n,i,mask=q['form'],q['ref'],q['cell'],q['mask'];start=16 if mask else 0;crop=(i%cols*size,i//cols*size,(i%cols+1)*size,(i//cols+1)*size);cell=im.crop(crop);arr=np.array(cell);lab,c=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(lab.flat);sizes[0]=0;need(sum(sizes>1000)==1,'단일큰몸');pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pal,'area_vote');Image.fromarray(z).save(dest/f'{form}_{n:03}_indices.png');old=np.array(Image.open(inp/f'{form}_217_body_indices.png')) if args.page=='b' else metric.full(a,n,mask);red=(arr[:,:,0]>180)&(arr[:,:,1]<60)&(arr[:,:,2]<70);aa,cc=np.unique(arr[:,:,3][red],return_counts=True);proof.append({'ref':n,'form':form,'source_crop':crop,'source_native_scale':[96,size],'old_bbox':metric.bbox(old),'new_bbox':metric.bbox(z),'old_eye':metric.eye(old),'new_eye':metric.eye(z),'translation':[0,0],'components8':int(label(z>0,np.ones((3,3)))[1]),'red_fringe_alpha_histogram':{str(int(k)):int(v)for k,v in zip(aa,cc)},'target_sha256':sha(z.tobytes())});rows.append((f'{form}{n}',[('idle',a.composite(0,mask)[0]),('old preparation',a.composite(n,mask)[0]),('new fixed',a.rgba(z,start))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],dest/f'comparison_{i//2+1}.png',7)
 write(out/'generation.json',{'generated_path':str(args.generated),'workspace_path':art.relative_to(ROOT).as_posix(),'sha256':digest(art),'size':list(im.size),'input_manifest_sha256':digest(inp/'manifest.json'),'tool':'builtin_imagegen','native_packed':False,'runtime_verified':False});write(dest/'manifest.json',{'parent_sha256':digest(p),'source_art_sha256':digest(art),'source_art':art.relative_to(ROOT).as_posix(),'frames':proof,'scope':'전체 출력 고정셀 등록. 자동bbox변형·옛몸덮기 없음. 관절/의상/부분소유는 후속검토이며 아직 미채택.','native_packed':False,'runtime_verified':False});print(json.dumps({'sha256':digest(art),'size':list(im.size),'frames':[{k:q[k]for k in('ref','form','old_bbox','new_bbox','old_eye','new_eye','components8')}for q in proof]}))
if __name__=='__main__':main()
