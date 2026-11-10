"""원홍채 좌표와 새 원화 피부 표본의 의미팔레트만 등록한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
s=importlib.util.spec_from_file_location('hover_source_vote',N/'ultimate_standing_repaint/prepare_common.py');sem=importlib.util.module_from_spec(s);s.loader.exec_module(sem)
def main():
 out=D/'semantic_samples_v1';out.mkdir(exist_ok=False);meta=json.loads((D/'first_registered_v1/manifest.json').read_text('utf8'));audit=json.loads((D/'source_semantics_audit_v1/report.json').read_text('utf8'));inp=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/inp['parent_arc']).read_bytes());im=Image.open(D/'a_v1/generated.png').convert('RGBA');pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32);rows=[];proof=[]
 for q in meta['frames']:
  n=q['ref'];z=np.array(Image.open(D/f'first_registered_v1/body_{n:03}_indices.png'));old=z.copy();cell=im.crop(q['crop']);au=next(v for v in audit['frames']if v['ref']==n);ex,ey=q['old_eye'];eye=[];skin=[]
  for y,x in np.argwhere(z==14):
   if y>=155 or (x-160,y-160)==(ex,ey):continue
   world=(int(x-160),int(y-160));value,votes=sem.source_vote(cell,pal,world,{14,15});eye.append({'world':list(world),'old':14,'new':value,'votes':votes,'method':'같은 고정셀의 비홍채 실제표본'});z[y,x]=value
  sample=next(v for v in au['eye_samples']if v['world']==[ex,ey]);need(sample['green_fraction']>=.2,'원홍채 위치 실제green source 존재')
  if z[ey+160,ex+160]!=14:
   eye.append({'world':[ex,ey],'old':int(z[ey+160,ex+160]),'new':14,'green_fraction':sample['green_fraction'],'votes':sample['votes'],'method':'같은 새고정셀의 green 표본을 기존 눈 한셀좌표에 등록. 전체머리 이동 없음.'});z[ey+160,ex+160]=14
  for r in au['lower_pink_candidates']:
   x,y=r['world'];need(z[y+160,x+160]==r['current_index'],'피부표본 원색');z[y+160,x+160]=r['nearest_nonpink_index'];skin.append({**r,'meaning':'실제열람한 정강이/발목피부 또는 해당 그늘외곽. 분홍머리·허리띠 범위는 제외.','method':'동일 생성RGB 평균의 기존 피부10..13/중성그늘1..4 최근접 의미양자화. 알파/형상변경 없음.'})
  need(np.array_equal(z>0,old>0),'알파 불변');need(label(z>0,np.ones((3,3)))[1]==1,'전신연결');Image.fromarray(z).save(out/f'body_{n:03}_indices.png');proof.append({'ref':n,'source_sha256':sha(old.tobytes()),'target_sha256':sha(z.tobytes()),'iris_source_registration':eye,'skin_source_registration':skin,'alpha_exact':True,'components8':1});rows.append((str(n),[('old hover',a.composite(n,15)[0]),('new fixed',a.rgba(old)),('source semantic sample',a.rgba(z)),('accepted idle',a.composite(0)[0])]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'source_art_sha256':digest(D/'a_v1/generated.png'),'audit_sha256':digest(D/'source_semantics_audit_v1/report.json'),'frames':proof,'scope':'새 원화 고정격자의 실제표본 의미양자화. 피부 표본을 원래구형 그림 복원으로 부르지 않는다. 손/총·추진발 접점·층/패킹은 미완료.','native_packed':False,'runtime_verified':False});print(json.dumps({'iris_changed':sum(len(q['iris_source_registration'])for q in proof),'skin_changed':sum(len(q['skin_source_registration'])for q in proof)}))
if __name__=='__main__':main()
