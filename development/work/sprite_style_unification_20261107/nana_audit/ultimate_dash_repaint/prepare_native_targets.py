"""새 대시20의 양의상 및 원효과를 출처에 묶어 네이티브 목표로 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from inspect_joint_sources import paths,REFS,SRC,EXPECTED
from preview_restore import Archive,sha,digest,write,need,helper
PBS=(0,5,6,7,8)
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'joint_native_targets_v1';out.mkdir(exist_ok=False)
 audit=json.loads((D/'joint_source_audit_v1/report.json').read_text('utf8'));need(audit['source_arc_sha256']==EXPECTED and audit['total_outside']==36,'Reviewed source boundary inventory');byref={q['ref']:q for q in audit['frames']};alllayers={};frames=[];rows=[];bounds=[]
 for n in REFS:
  bp,ap=paths(n);q=byref[n];need(digest(bp)==q['before_sha256']and digest(ap)==q['after_sha256'],'Reviewed source unchanged');b=np.array(Image.open(bp));f=np.array(Image.open(ap));original=f.copy();outside=(f>0)&(b==0);points=[{'world':[int(x-160),int(y-160)],'after_index':int(f[y,x])}for y,x in np.argwhere(outside)];need(points==q['after_outside_before'],'Exact boundary coordinates')
  f[outside]=0;need(label(b>0,np.ones((3,3)))[1]==1 and label(f>0,np.ones((3,3)))[1]==1,f'Connected new forms {n}')
  delta=(b!=f)|(b==15);layers={0:f,5:np.where(delta,b,0).astype(np.uint8),6:np.zeros_like(f),7:np.zeros_like(f),8:np.zeros_like(f)};need(np.array_equal(np.where(layers[5],layers[5],layers[0]),b),'Exact new jacket display');alllayers[n]=layers
  for pb in(6,7,8):need(not a.layer(n,pb)[0].any(),'Existing empty layer')
  frames.append({'ref':n,'before_source':bp.relative_to(ROOT).as_posix(),'before_source_sha256':digest(bp),'after_source':ap.relative_to(ROOT).as_posix(),'after_source_sha256':digest(ap),'source_boundary_corrections':points,'reason':'새 맨팔의 외곽36셀만 새 재킷 외곽으로 제한. 옛 게임 알파/몸체는 사용하지 않음.','both_connected':True})
  if points:bounds.append((str(n),[('new jacket',a.rgba(b,16)),('bare source',a.rgba(original)),('common edge candidate',a.rgba(f))]))
 # 원 스파크9조립의54texel을 기본층 위에 그린 뒤 기존과 같은 순서로 의상층을 그린다.
 effect_meta=json.loads((D/'structure_v3/manifest.json').read_text('utf8'));need(effect_meta['parent_sha256']==EXPECTED,'Effect source');effects=[]
 for n,body in((73,71),(74,72)):
  source=D/f'structure_v3/effect_{n:03}.png';fx=np.array(Image.open(source));q=next(q for q in effect_meta['effects']if q['ref']==n);need(sha(fx.tobytes())==q['effect_sha256']and np.count_nonzero(fx)==54,'Original effect texels');layers={pb:z.copy()for pb,z in alllayers[body].items()}
  if n==74:
   need(layers[0][164,125]==0 and layers[5][164,125]==1,'72 original weapon variant');layers[0][164,125]=1
  layers[0]=np.where(fx,fx,layers[0]).astype(np.uint8);alllayers[n]=layers;effects.append({'ref':n,'body_ref':body,'source':source.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'effect_sha256':sha(fx.tobytes()),'effect_texels':54,'parts':q['effect_parts'],'base_draw_order':'effect after body, before armor layers','weapon74_exception':[[-35,4,1]]if n==74 else[]});frames.append({'ref':n,'source_body_ref':body,'source_effect_ref':n})
 for q in frames:
  n=q['ref'];layers=alllayers[n];b=np.where(layers[5],layers[5],layers[0]).astype(np.uint8);q.update(base_sha256=sha(layers[0].tobytes()),before_sha256=sha(b.tobytes()),after_sha256=sha(layers[0].tobytes()),layers={str(pb):sha(ar.tobytes())for pb,ar in layers.items()})
  for pb,ar in layers.items():Image.fromarray(ar).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(b).save(out/f'before_{n:03}.png');Image.fromarray(layers[0]).save(out/f'after_{n:03}.png')
 # 실제 원총구의32개 마스크/팔 조합과 비교한다.72 한 점의 마스크 차이도 포함한다.
 checks=0;fire=json.loads((D/'fire_constraints_v2/manifest.json').read_text('utf8'))
 for q in fire['frames']:
  n=q['ref'];x0,y0,x1,y1=q['window_world'];sl=np.s_[y0+160:y1+160,x0+160:x1+160];layers=alllayers[n]
  for mask in range(16):
   for arm in(1,2):
    im=a.rgba(layers[0]);
    if mask&1:im.alpha_composite(a.rgba(layers[5],16))
    need(np.array_equal(np.array(im)[sl],np.array(a.composite(n,mask,arm)[0])[sl]),f'Original muzzle {n}/{mask}/{arm}');checks+=1
 for i in range(0,len(bounds),4):helper.grid(bounds[i:i+4],out/f'boundary_comparison_{i//4+1}.png',5)
 for n in(67,69,71,73,75,77,79,81,83,93):
  imgs=[]
  for mask in(15,0):
   imgs.append(('before idle'if mask else'after idle',a.composite(0,mask)[0]))
   for r in(n,n+1):
    z=alllayers[r];im=a.rgba(z[0]);
    if mask:im.alpha_composite(a.rgba(z[5],16))
    imgs.append((f'new {r}',im))
  rows.append((f'{n}/{n+1}',imgs))
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',5)
 write(out/'manifest.json',{'source_arc_sha256':EXPECTED,'frames':sorted(frames,key=lambda q:q['ref']),'selected_refs':sorted(alllayers),'layer_semantics':{'0':'획득후 새 맨팔 몸체 및 원효과','5':'획득전 새 재킷 차분 및 palette15 보정','6/7/8':'기존 빈 층 유지'},'effects':effects,'source_boundary_corrections':36,'original_muzzle_rgba_checks':checks,'native_packed':False,'runtime_verified':False,'art_review_pending':True});print(out)
if __name__=='__main__':main()
