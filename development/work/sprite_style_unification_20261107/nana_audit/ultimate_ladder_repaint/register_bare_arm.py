"""새 맨팔 국소원화의 높은팔만첫 사다리전신에등록한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
spec=importlib.util.spec_from_file_location('arm_quantizer',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
POLYS={143:[(-15,-24),(-9,-24),(-6,-20),(-2,-17),(-1,-12),(-5,-10),(-11,-16),(-15,-21)],144:[(-11,-27),(-5,-27),(-4,-23),(-2,-20),(1,-15),(0,-10),(-4,-10),(-7,-17),(-10,-22)],146:[(-11,-28),(-5,-28),(-5,-23),(-2,-19),(1,-15),(0,-9),(-4,-9),(-7,-16),(-10,-24)]}
def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def main():
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());art=D/'a_arm_v1/generated.png';need(digest(art)=='63e74beea1bccb9ba4714a455f9c36284c6770125da980b269c86d4d4de2e8ed','국소원화');im=Image.open(art).convert('RGBA');out=D/'a_arm_registered_v1';out.mkdir(exist_ok=False)
 write(art.parent/'generation.json',{'tool':'builtin image_gen','source_path':'<LOCAL_PATH>','sha256':digest(art),'size':list(im.size),'prompt':'../a_arm_inputs_v1/prompt.txt','scope':'후폼3 높은팔의분홍소매를맨팔로교정한국소원화.다른부위는첫원화에서보존.','native_packed':False})
 pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);records=[];rows=[]
 for col,n in enumerate(meta['refs']):
  crop=tuple(round(v)for v in(col*im.width/3,im.height/2,(col+1)*im.width/3,im.height));fixed=np.zeros((384,384),np.uint8);fixed[124:188,128:192]=reg.register(im.crop(crop),(64,64),pal,'area_vote');old=np.array(Image.open(D/f'a_registered_v1/after_{n:03}_indices.png'));before=np.array(Image.open(D/f'a_registered_v1/before_{n:03}_indices.png'));mask=poly(POLYS[n]);new=np.where(mask,fixed,old).astype(np.uint8);need(np.array_equal(new[~mask],old[~mask]),'다른새전신보존')
  for tag,z in(('after',new),('after_donor',fixed),('before',before)):Image.fromarray(z).save(out/f'{tag}_{n:03}_indices.png')
  Image.fromarray(mask.astype(np.uint8)*255).save(out/f'mask_{n:03}.png');records.append({'ref':n,'source_crop':list(crop),'native_polygon':POLYS[n],'changed_pixels':int((new!=old).sum()),'components8':int(label(new>0,np.ones((3,3)))[1]),'outside_polygon_exact':True,'before_exact':True,'body_sha256':sha(new.tobytes()),'source_links':[{'destination':[int(x-160),int(y-160)],'source':[int(x-160),int(y-160)],'index':int(fixed[y,x])}for y,x in np.argwhere(mask&(new!=old))]})
  rows.append((str(n),[('new jacket',a.rgba(before,16)),('held pink sleeve',a.rgba(old)),('new bare donor',a.rgba(fixed)),('local arm only',a.rgba(new))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'manifest.json',{'art_path':art.relative_to(ROOT).as_posix(),'art_sha256':digest(art),'parent_sha256':sha(a.data),'frames':records,'scope':'후폼3 높은팔만고정전체캔버스비율/동일좌표새표본등록.원손발접점·양폼공통층은다음단계.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'changed':q['changed_pixels'],'components':q['components8']}for q in records]))
if __name__=='__main__':main()
