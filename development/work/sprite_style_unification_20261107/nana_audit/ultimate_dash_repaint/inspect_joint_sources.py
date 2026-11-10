"""두 의상의 원화 알파와 파츠 공유 제약을 읽기 대조한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
SRC=N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC'
EXPECTED='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'
BODIES={67:'first_cases_probe_v2',69:'more_cases_probe_v2',71:'local_legs_registered_v4',75:'more_cases_probe_v2',77:'more_cases_probe_v2',79:'first_cases_probe_v2',81:'more_cases_probe_v2',83:'more_cases_probe_v2',93:'first_cases_probe_v2',94:'fold94_registered_v1'}
AFTER={**{n:'after_a_costume_probe_v4'for n in(67,71,79,93)},**{n:'after_b_costume_probe_v3'for n in(69,75,77,81)},83:'after_c_costume_probe_v4',94:'after_c_costume_probe_v4'}
REFS=sorted(set(BODIES)|{68,70,72,76,78,80,82,84})
def paths(n):
 if n in BODIES:return D/BODIES[n]/f'before_{n:03}.png',D/AFTER[n]/f'after_{n:03}.png'
 p='a'if n<78 else'b'
 return D/f'firing_{p}_before_joint_probe_v2/before_{n:03}.png',D/f'firing_{p}_after_joint_probe_v3/after_{n:03}.png'
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'joint_source_audit_v1';out.mkdir(exist_ok=False);reports=[];rows=[]
 for n in REFS:
  bp,ap=paths(n);b=np.array(Image.open(bp));f=np.array(Image.open(ap));outside=(f>0)&(b==0);points=[{'world':[int(x-160),int(y-160)],'after_index':int(f[y,x])}for y,x in np.argwhere(outside)];layers={str(pb):int(np.count_nonzero(a.layer(n,pb)[0]))for pb in(5,6,7,8)}
  reports.append({'ref':n,'before_path':bp.relative_to(ROOT).as_posix(),'before_sha256':digest(bp),'after_path':ap.relative_to(ROOT).as_posix(),'after_sha256':digest(ap),'after_outside_before':points,'before_components':int(label(b>0,np.ones((3,3)))[1]),'after_components':int(label(f>0,np.ones((3,3)))[1]),'old_layer_pixels':layers})
  if points:rows.append((str(n),[('before source',a.rgba(b,16)),('after source',a.rgba(f)),('after outside before',a.rgba(np.where(outside,f,0)))]))
 for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
 write(out/'report.json',{'source_arc_sha256':EXPECTED,'frames':reports,'total_outside':sum(len(q['after_outside_before'])for q in reports),'no_asset_modified':True});print(json.dumps({'outside':{q['ref']:q['after_outside_before']for q in reports if q['after_outside_before']},'layers':{q['ref']:q['old_layer_pixels']for q in reports},'components':{q['ref']:[q['before_components'],q['after_components']]for q in reports}}))
if __name__=='__main__':main()
