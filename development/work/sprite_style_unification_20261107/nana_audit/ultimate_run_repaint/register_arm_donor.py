"""새 맨팔 전용 원화만 기존 후보에 등록한다. 의상 몸체를 복사하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
SRC=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'
def main():
 out=D/'firing_a_after_joint_probe_v3';out.mkdir(exist_ok=False)
 a=Archive(SRC.read_bytes());inputs=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'))
 reg=json.loads((D/'firing_a_after_registered_v2/registration.json').read_text('utf8'))
 polygons={
  2:[(-40,-16),(-8,-16),(-8,-9),(-4,-9),(-3,-7),(-7,-4),(-7,4),(-40,4)],
  4:[(-40,-17),(-8,-17),(-8,-9),(-4,-9),(-3,-7),(-7,-4),(-7,6),(-40,6)],
  6:[(-40,-17),(-11,-17),(-11,-10),(-7,-10),(-5,-8),(-8,-5),(-8,3),(-40,3)],
  8:[(-40,-16),(-13,-16),(-13,-9),(-8,-9),(-7,-7),(-10,-4),(-10,4),(-40,4)]}
 Y,X=np.indices((384,384));Y-=160;X-=160;rows=[];records=[]
 for rr in reg['frames']:
  n=rr['ref'];q=next(z for z in inputs['frames']if z['ref']==n)
  bp=D/f'firing_a_after_joint_probe_v2/after_{n:03}.png';sp=D/f'firing_a_after_registered_v2/after_{n:03}.png';cp=D/f'firing_a_before_joint_probe_v2/before_{n:03}.png'
  b=np.array(Image.open(bp));s=np.array(Image.open(sp));before=np.array(Image.open(cp));need(sha(s.tobytes())==rr['index_sha256'],'Source hash')
  mi=Image.new('1',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in polygons[n]],fill=1);mask=np.array(mi).astype(bool)
  t=b.copy();t[mask]=s[mask];case=np.array(Image.open(D/f'firing_inputs_v1/after_case_{n:03}.png'));x0,y0,x1,y1=q['window_world'];window=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1);t[window]=case[window]
  need(np.array_equal(t[~(mask|window)],b[~(mask|window)]),'Outside local arm exact');need(np.array_equal(t[window],case[window]),'Original muzzle')
  # 등록 영역의 피부·음영·투명도가 원화에 존재함을 보장한다. 별도 채색 없음.
  need(np.array_equal(t[mask&~window],s[mask&~window]),'Exact donor texels')
  lab,num=label(t>0,np.ones((3,3)));sizes=np.bincount(lab.ravel());small=[int(sizes[k])for k in range(1,num+1)if sizes[k]<10]
  Image.fromarray(t).save(out/f'after_{n:03}.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/f'arm_mask_{n:03}.png')
  outside=(t>0)&(before==0);coords=[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(outside))]
  records.append({'ref':n,'base_path':bp.relative_to(ROOT).as_posix(),'base_sha256':digest(bp),'donor_path':sp.relative_to(ROOT).as_posix(),'donor_sha256':digest(sp),'polygon':polygons[n],'same_coordinate_source_exact':True,'rescale_stretch_fill':False,'outside_arm_exact':True,'original_weapon_window_exact':True,'changed_pixels':int((t!=b).sum()),'after_outside_before_alpha':coords,'components':int(num),'small_components':small,'index_sha256':sha(t.tobytes())})
  rows.append((f'run firing {n}',[('jacket arm',a.rgba(before,16)),('first bare arm candidate',a.rgba(b,0)),('same-pose new bare arm',a.rgba(t,0))]))
 for i in(0,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'registration.json',{'scope':'신규 맨팔 전용 원화의 지정 영역만 동일 좌표로 등록. 원화의 재킷 몸통·반대팔은 사용하지 않는다. 패킹/실기 전 후보.','frames':records,'native_packed':False,'runtime_verified':False})
 print(json.dumps([{k:r[k]for k in('ref','changed_pixels','components','small_components','after_outside_before_alpha')}for r in records]))
if __name__=='__main__':main()
