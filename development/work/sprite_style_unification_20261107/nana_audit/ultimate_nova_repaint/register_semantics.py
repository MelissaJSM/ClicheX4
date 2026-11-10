"""고정 생성셀의 실제 피부/외곽 표본과 홍채 한행을 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
def main():
 out=D/'semantic_samples_v1';out.mkdir(exist_ok=False);audit=json.loads((D/'source_semantics_audit_v2/report.json').read_text('utf8'));inp=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/inp['parent_arc']).read_bytes());frames=[];rows=[]
 for q in audit['frames']:
  n,form=q['ref'],q['form'];start=16 if form=='before'else 0;src=D/f'a_registered_v1/{form}_{n:03}_indices.png';old=np.array(Image.open(src));z=old.copy();eye=[]
  for e in q['iris_candidates']:
   x,y=e['world']
   if y>=-12:continue
   need(z[y+160,x+160]==14,'홍채 원값');z[y+160,x+160]=e['nearest_noniris'];eye.append(e)
  keep=(-5,-12)if n==213 else(-2,-12);need(z[keep[1]+160,keep[0]+160]==14,'실제강한홍채 유지')
  for e in q['lower_material_candidates']:
   x,y=e['world'];need(z[y+160,x+160]==e['old'],'피부 의미원값');z[y+160,x+160]=e['nearest_skin_or_outline']
  for e in q['palette15_candidates']:
   x,y=e['world'];need(z[y+160,x+160]==15,'15원값');z[y+160,x+160]=e['value']
  need(np.array_equal(z>0,old>0),'알파형상보존');need(label(z>0,np.ones((3,3)))[1]==1,'1몸체');Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');frames.append({'ref':n,'form':form,'source':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'source_indexed_sha256':sha(old.tobytes()),'target_sha256':sha(z.tobytes()),'iris_removed_upper_samples':eye,'retained_green_eye':list(keep),'original_eye':q['old_eye'],'head_translation':[0,0],'skin_rgb_samples':q['lower_material_candidates'],'palette15_actual_samples':q['palette15_candidates'],'alpha_exact':True});rows.append((f'{form}{n}',[('idle',a.composite(0,15 if start else 0)[0]),('new fixed',a.rgba(old,start)),('actual source material candidate',a.rgba(z,start))]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'source_art_sha256':audit['source_sha256'],'audit_sha256':digest(D/'source_semantics_audit_v2/report.json'),'frames':frames,'scope':'몸체/알파/머리·손발 원점 불변. 새 생성원화의 실제RGB로 하체 y>=5 피부·그늘/15색 표본만 재양자화했다. 홍채 윗행은 실제비홍채표본으로 정리,215의 강한눈표본은 원눈보다1px왼쪽임을 남기며 전체머리를 이동하지 않았다. 공통층/접점 최종미완료.','native_packed':False,'runtime_verified':False});print(json.dumps({'skin':sum(len(q['skin_rgb_samples'])for q in frames),'iris':sum(len(q['iris_removed_upper_samples'])for q in frames),'p15':sum(len(q['palette15_actual_samples'])for q in frames)}))
if __name__=='__main__':main()
