"""내장217 고유몸체 원화를 보존하고 고정96격자로 등록한다."""
from pathlib import Path
import sys,json,shutil,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,helper,need
s=importlib.util.spec_from_file_location('nova217_quantizer',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(s);s.loader.exec_module(reg)
def main():
 original=Path(sys.argv[1]);out=D/'dash217_v1';out.mkdir(exist_ok=False);art=out/'generated.png';shutil.copyfile(original,art);need(digest(original)==digest(art),'원화 복사');im=Image.open(art).convert('RGBA');need(im.width==im.height,'단일 정사각 캔버스');meta=json.loads((D/'dash217_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/meta['parent_arc'];need(digest(p)==meta['parent_sha256'],'부모');a=Archive(p.read_bytes());pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(im,(96,96),pal,'area_vote');dest=D/'dash217_registered_v1';dest.mkdir(exist_ok=False);Image.fromarray(z).save(dest/'body_217_indices.png');old=a.layer(217)[0];yy,xx=np.nonzero(z);row=[('idle',a.composite(0)[0]),('current217',a.composite(217,15)[0]),('new fixed217',a.rgba(z)),('new215',a.rgba(np.array(Image.open(D/'common_probe_v5/after_215_indices.png'))))];helper.grid([('217',row)],dest/'comparison.png',7)
 ey,ex=np.nonzero((z==14)&(np.indices(z.shape)[0]<165));oy,ox=np.nonzero((old==14)&(np.indices(old.shape)[0]<165));record={'source_art_sha256':digest(art),'source_size':list(im.size),'fixed_native':[96,96],'old_bbox':meta['source_bbox'],'new_bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)],'old_green':[[int(x-160),int(y-160)]for y,x in zip(oy,ox)],'new_green':[[int(x-160),int(y-160)]for y,x in zip(ey,ex)],'components':int(label(z>0,np.ones((3,3)))[1]),'target_sha256':sha(z.tobytes()),'translation':[0,0],'native_packed':False,'scope':'전체 캔버스 고정 등록만 완료. 몸체/눈/손발/효과 가림 및219 파생은 후속 검토. 전체바디 이동·확대·옛머리 덮기 없음.'};write(dest/'manifest.json',record);write(out/'generation.json',{'original_path':str(original),'workspace_path':art.relative_to(ROOT).as_posix(),'sha256':digest(art),'size':list(im.size),'tool':'builtin_imagegen','input_manifest_sha256':digest(D/'dash217_inputs_v1/manifest.json')});print(json.dumps(record))
if __name__=='__main__':main()
