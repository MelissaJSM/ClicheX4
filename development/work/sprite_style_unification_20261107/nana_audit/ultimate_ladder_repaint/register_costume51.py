"""사용자 재개로 생성된 의상 교정의 원화와 고정셀 변환을 보존한다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=N.parents[2];sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from register_page import reg
from preview_restore import Archive,digest,sha,write,need,helper
OUT=D/'b_costume_registered51'
def main():
 need(not OUT.exists(),'Fresh output');OUT.mkdir()
 gen=Path('<LOCAL_PATH>');shutil.copyfile(gen,OUT/'generated.png')
 src=json.loads((W/'staging_rn_v43.json').read_text('utf8'))['resources']['PL02_U.ARC'];p=ROOT/src['path'];need(digest(p)==src['after'],'Current parent');a=Archive(p.read_bytes());im=Image.open(OUT/'generated.png').convert('RGBA');need(im.size==(1536,1024),'Exact grid');pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);rows=[];frames=[]
 for i,n in enumerate((149,151,153)):
  cell=im.crop((i*512,512,(i+1)*512,1024));v=np.zeros((384,384),np.uint8);v[124:188,128:192]=reg.register(cell,(64,64),pal,'area_vote');b=np.array(Image.open(D/f'b_registered_v1/before_{n:03}_indices.png'))
  for tag,z in [('before',b),('after',v)]:Image.fromarray(z).save(OUT/f'{tag}_{n:03}_indices.png')
  rows.append((str(n),[('idle',a.composite(0,0)[0]),('new jacket',a.rgba(b,16)),('new corrected',a.rgba(v))]));frames.append({'ref':n,'before_source_sha256':digest(D/f'b_registered_v1/before_{n:03}_indices.png'),'after_native_sha256':sha(v.tobytes()),'wholebody_shift':[0,0]})
 helper.grid(rows,OUT/'comparison.png',6)
 write(OUT/'manifest.json',{'parent':src,'generated_source':str(gen),'generated_sha256':digest(OUT/'generated.png'),'prompt_sha256':digest(D/'b_costume_inputs_v1/prompt.txt'),'prior_failure_preserved':True,'user_requested_resume':True,'tool':'builtin image_gen','same_original_prompt':True,'fallback_used':False,'filter_bypassed':False,'frames':frames,'native_packed':False,'runtime_verified':False});print(json.dumps({'registered':3,'output':str(OUT)}))
if __name__=='__main__':main()
