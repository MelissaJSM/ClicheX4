"""원발사점 팔 보완 원화 보존/고정격자 등록. 아직 전신 채택하지 않는다."""
from pathlib import Path
import sys,json,shutil,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
s=importlib.util.spec_from_file_location('hover_muzzle_quantizer',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(s);s.loader.exec_module(reg)
def main():
 page,src=sys.argv[1],Path(sys.argv[2]);m=json.loads((D/f'muzzle_arm_{page}_inputs_v1/manifest.json').read_text('utf8'));a=Archive((N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC').read_bytes());out=D/f'muzzle_arm_{page}_v1';out.mkdir(exist_ok=False);art=out/'generated.png';shutil.copyfile(src,art);need(digest(src)==digest(art),'원화복사');im=Image.open(art).convert('RGBA');need(im.width==im.height,'정사각 전체캔버스');side=im.width//2 if len(m['frames'])>1 else im.width;dest=D/f'muzzle_arm_{page}_registered_v1';dest.mkdir(exist_ok=False);pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32);rows=[];frames=[]
 for q in m['frames']:
  n,i=q['ref'],q['cell'];crop=[i%2*side,i//2*side,(i%2+1)*side,(i//2+1)*side]if len(m['frames'])>1 else[0,0,side,side];z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(im.crop(crop),(96,96),pal,'area_vote');Image.fromarray(z).save(dest/f'body_{n:03}_indices.png');old=np.array(Image.open(ROOT/q['source']));frames.append({'ref':n,'crop':crop,'source_native_scale':[96,side],'indexed_sha256':sha(z.tobytes()),'components8':int(label(z>0,np.ones((3,3)))[1]),'engine_projectile_origin':q['engine_projectile_origin'],'canonical_translation':q['canonical_translation'],'local_adopted':False});rows.append((str(n),[('old arm candidate',a.rgba(old)),('new arm donor',a.rgba(z)),('target module',a.rgba(np.array(Image.open(D/f'muzzle_arm_{page}_inputs_v1/target_gun_{n}.png'))))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],dest/f'comparison_{i//2+1}.png',7)
 write(out/'generation.json',{'source_path':str(src),'workspace_path':art.relative_to(ROOT).as_posix(),'sha256':digest(art),'size':list(im.size),'input_manifest_sha256':digest(D/f'muzzle_arm_{page}_inputs_v1/manifest.json'),'tool':'builtin_imagegen'});write(dest/'manifest.json',{'source_art':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'frames':frames,'native_packed':False,'runtime_verified':False,'scope':'원발사점에 맞춘 새팔 donor. 전체몸·총을 그대로 채택하지 않고 새 팔/실제손만 의미등록 후 정본총을 강체정합한다.'});print(json.dumps({'sha256':digest(art),'size':list(im.size),'refs':[q['ref']for q in frames]}))
if __name__=='__main__':main()
