"""원화 피부 RGB의 셀 면적 평균으로 최빈색에서 손실된 중간 명암만 비교한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper

def box(v):
 return np.array(Image.fromarray(v.astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))

def main():
 out=D/'arm_source_shading_probe_v1';out.mkdir(exist_ok=False)
 arc=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'
 need(digest(arc)=='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0','Parent')
 a=Archive(arc.read_bytes());pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
 report=json.loads((D/'arm_shading_audit_v2/report.json').read_text('utf8'));meta=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'))
 rows=[];recs=[]
 for r in report['frames']:
  n=r['ref'];src=ROOT/r['source_art'];need(digest(src)==r['source_sha256'],'Source')
  oldpath=D/f'firing_after_cleanup_v1/after_{n:03}.png'
  if n in(4,8):oldpath=D/f'arm48_registered_v1/after_{n:03}.png'
  old=np.array(Image.open(oldpath));new=old.copy();cells=[]
  if n not in(4,8):
   im=Image.open(src).convert('RGBA').crop(r['crop']);p=np.array(im);rgb=p[:,:,:3].astype(np.float32);alpha=p[:,:,3].astype(np.float32)/255
   labels=np.empty(alpha.shape,np.uint8)
   for y in range(im.height):labels[y]=1+((rgb[y,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
   # 피부로 이미 분류된 원화 표본만 사용한다. 검정 윤곽/분홍 옷이 평균에 섞이지 않는다.
   skin=np.isin(labels,[10,11,12,13])*alpha;cov=box(skin)
   mean=np.stack([box(rgb[:,:,c]*skin)/np.maximum(cov,.001)for c in range(3)],2)
   native=10+((mean[:,:,None,:]-pal[None,None,10:14,:])**2).sum(3).argmin(2)
   dx,dy=r['native_translation'];x0,y0,x1,y1=r['arm_roi_world']
   for sy in range(96):
    for sx in range(96):
     x,y=sx-48+dx,sy-48+dy
     if not(x0<=x<x1 and y0<=y<y1):continue
     if old[y+160,x+160]!=12 or native[sy,sx]!=11 or cov[sy,sx]<.5:continue
     new[y+160,x+160]=11
     cells.append({'xy_world':[x,y],'before':12,'after':11,'source_native_cell':[sx,sy],
      'source_footprint_relative_crop':[sx*im.width/96,sy*im.height/96,(sx+1)*im.width/96,(sy+1)*im.height/96],
      'skin_coverage':float(cov[sy,sx]),'source_skin_rgb_mean':mean[sy,sx].tolist(),
      'distance_squared_to_skin_palette':((mean[sy,sx]-pal[10:14])**2).sum(1).tolist()})
  q=next(z for z in meta['frames']if z['ref']==n);x0,y0,x1,y1=q['window_world']
  need(np.array_equal(new>0,old>0),'Alpha changed')
  need(np.array_equal(new[y0+160:y1+160,x0+160:x1+160],old[y0+160:y1+160,x0+160:x1+160]),'Gun changed')
  delta=new!=old;need(int(delta.sum())==len(cells),'Unexpected changes')
  Image.fromarray(new).save(out/f'after_{n:03}.png')
  recs.append({'ref':n,'base_path':oldpath.relative_to(ROOT).as_posix(),'base_sha256':digest(oldpath),
   'source_art':r['source_art'],'source_sha256':r['source_sha256'],'crop':r['crop'],'translation':r['native_translation'],
   'changed_cells':cells,'target_indices_sha256':sha(new.tobytes()),'alpha_and_original_case_exact':True,
   'new4_8_accepted_source_preserved':n in(4,8)})
  rows.append((f'run firing {n}',[('accepted idle',a.composite(0,0)[0]),('current / unclipped',a.rgba(old)),('source skin mean / unclipped',a.rgba(new))]))
 for i in range(0,16,4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
 write(out/'registration.json',{'scope':'원화 피부 표본을 같은 고정 셀에서 면적 평균한 별도 등록 후보. 새 색/외곽/알파 생성 없음. 원색 복원이 아닌 양자화 방법 변경이며 미술 수용 전 후보이다.',
  'rule':'current=12, source skin coverage>=0.5, nearest original skin RGB mean palette=11만 변경. source nearest labels10..13만 평균; source outline/pink 제외. 4/8 새 원화 후보는 그대로.',
  'parent_arc_sha256':digest(arc),'frames':recs,'changed_pixels':sum(len(r['changed_cells'])for r in recs),
  'native_packed':False,'runtime_verified':False})
 print(json.dumps({'output':str(out),'changed_pixels':sum(len(r['changed_cells'])for r in recs)}))

if __name__=='__main__':main()
