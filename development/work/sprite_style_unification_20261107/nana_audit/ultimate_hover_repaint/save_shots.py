"""호버 사격팔 원화를 원파일 유지 복사하고 고정 전체격자로 등록한다."""
from pathlib import Path
import sys,json,shutil,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
s=importlib.util.spec_from_file_location('hover_shot_quantizer',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(s);s.loader.exec_module(reg)
def main():
 page,src=sys.argv[1],Path(sys.argv[2]);m=json.loads((D/f'shot_{page}_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());need(digest(ROOT/m['parent_arc'])==m['parent_arc_sha256'],'부모');out=D/f'shot_{page}_v1';out.mkdir(exist_ok=False);art=out/'generated.png';shutil.copyfile(src,art);need(digest(src)==digest(art),'원본복사');im=Image.open(art).convert('RGBA');need(im.width==im.height,'정사각');count=len(m['frames']);size=im.width//2 if count>1 else im.width;dest=D/f'shot_{page}_registered_v1';dest.mkdir(exist_ok=False);pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32);rows=[];proof=[]
 for q in m['frames']:
  n,i=q['ref'],q['cell'];crop=[i%2*size,i//2*size,(i%2+1)*size,(i//2+1)*size]if count>1 else[0,0,size,size];cell=im.crop(crop);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pal,'area_vote');Image.fromarray(z).save(dest/f'body_{n:03}_indices.png');b=np.array(Image.open(ROOT/q['body_source']));proof.append({'ref':n,'crop':crop,'native_fixed_scale':[96,size],'indexed_sha256':sha(z.tobytes()),'components8':int(label(z>0,np.ones((3,3)))[1]),'body_source':q['body_source'],'body_source_sha256':q['body_source_sha256'],'old_muzzle_column':q['old_muzzle_column'],'old_muzzle_rows':q['old_muzzle_rows'],'semantic_arm_registration_complete':False});rows.append((str(n),[('old shot position',a.composite(n,15)[0]),('new body master',a.rgba(b)),('new firing donor',a.rgba(z))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],dest/f'comparison_{i//2+1}.png',6)
 write(out/'generation.json',{'source_path':str(src),'workspace_path':art.relative_to(ROOT).as_posix(),'sha256':digest(art),'size':list(im.size),'input_manifest_sha256':digest(D/f'shot_{page}_inputs_v1/manifest.json'),'tool':'builtin_imagegen','native_packed':False,'runtime_verified':False});write(dest/'manifest.json',{'source_art_sha256':digest(art),'source_art':art.relative_to(ROOT).as_posix(),'frames':proof,'scope':'전체격자 팔 donor. 머리/몸/다리는 비사격 원화 보존 예정, 총구/손·팔꿈치 정합 미완료.','runtime_verified':False});print(json.dumps({'sha256':digest(art),'size':list(im.size),'frames':[{k:q[k]for k in('ref','components8')}for q in proof]}))
if __name__=='__main__':main()
