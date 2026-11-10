"""새 팔 원화의 고정셀 전체등록. 루트 몸체/자원에는 쓰지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
def main():
 out=D/'registered_sources01';out.mkdir(exist_ok=False);frames=[]
 for page in ('a','b'):
  inp=D/f'inputs_{page}01';m=json.loads((inp/'manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());im=Image.open(inp/'generated.png').convert('RGBA');rows=[]
  for q in m['frames']:
   n,form,i,start=q['ref'],q['form'],q['cell'],q['palette_start'];box=(round(i%2*im.width/2),round(i//2*im.height/2),round((i%2+1)*im.width/2),round((i//2+1)*im.height/2));pal=np.array([[((int(w)>>s)&31)*255//31 for s in (0,5,10)]for w in a.words[start:start+16]],np.float32);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(im.crop(box),(96,96),pal,'area_vote');src=np.array(Image.open(ROOT/q['body_source']));Image.fromarray(z).save(out/f'{form}_{n}_indices.png');a.rgba(z,start).save(out/f'{form}_{n}_rgba.png');rows.append((f'{form} {n}',[('idle 85',a.composite(85,0 if start==0 else 15)[0]),('root fixed body',a.rgba(src,start)),('new arm donor - whole not adopted',a.rgba(z,start))]));frames.append(dict(q,source_image=str((inp/'generated.png').relative_to(ROOT)).replace('\\','/'),source_sha256=digest(inp/'generated.png'),source_size=list(im.size),source_crop=box,registered_indices_sha256=sha(z.tobytes())))
  for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{page}_{i//2+1}.png',7)
 write(out/'manifest.json',{'frames':frames,'method':'전체캔버스 고정96셀 면적투표. bbox 확대/이동 없음. 새 팔 원화 donor만 등록하며 전신은 미채택.','root_sources_unchanged':all(digest(ROOT/q['body_source'])==q['body_source_sha256']for q in frames),'native_packed':False,'runtime_verified':False})
 print('8 고정셀 등록 저장')
if __name__=='__main__':main()
