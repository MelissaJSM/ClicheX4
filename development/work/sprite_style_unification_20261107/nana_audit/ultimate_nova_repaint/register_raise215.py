"""215 팔 보완 내장 원화를 원본 보존 후 고정 셀로 읽는다."""
from pathlib import Path
import sys,json,shutil,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,helper,need
s=importlib.util.spec_from_file_location('nova_raise_quantizer',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(s);s.loader.exec_module(reg)
def main():
 path=Path(sys.argv[1]);out=D/'raise215_v1';out.mkdir(exist_ok=False);art=out/'generated.png';shutil.copyfile(path,art);need(digest(path)==digest(art),'생성물 보존');im=Image.open(art).convert('RGBA');need(im.width==im.height and im.width%2==0,'전체 2x2 고정 셀');size=im.width//2;dest=D/'raise215_fixed_v1';dest.mkdir(exist_ok=False);meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());rows=[];frames=[]
 for row,(form,start,mask)in enumerate((('before',16,15),('after',0,0))):
  crop=(size,row*size,size*2,(row+1)*size);cell=im.crop(crop);pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[start:start+16]],np.float32);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pal,'area_vote');Image.fromarray(z).save(dest/f'{form}_215_indices.png');old=np.array(Image.open(D/f'semantic_samples_v1/{form}_215_indices.png'));yy,xx=np.nonzero(z);frames.append({'ref':215,'form':form,'crop':crop,'source_native_scale':[96,size],'bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)],'components':int(label(z>0,np.ones((3,3)))[1]),'target_sha256':sha(z.tobytes())});rows.append((form,[('old pose',a.composite(215,mask)[0]),('first source',a.rgba(old,start)),('new raised source',a.rgba(z,start))]))
 helper.grid(rows,dest/'comparison.png',7);write(out/'generation.json',{'original_path':str(path),'workspace_path':art.relative_to(ROOT).as_posix(),'sha256':digest(art),'size':list(im.size),'input_manifest_sha256':digest(D/'raise215_inputs_v1/manifest.json'),'tool':'builtin_imagegen'});write(dest/'manifest.json',{'source_sha256':digest(art),'frames':frames,'scope':'고정 전체캔버스 비율 등록만 완료. 다른 부위는 채택하지 않으며 팔 의미영역/원손 접점 등록은 다음 단계.','native_packed':False});print(json.dumps({'sha256':digest(art),'size':im.size,'frames':frames}))
if __name__=='__main__':main()
