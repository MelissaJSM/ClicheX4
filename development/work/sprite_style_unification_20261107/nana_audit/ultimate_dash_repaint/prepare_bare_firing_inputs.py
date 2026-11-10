"""새 사격8의 팔 위치를 보존하는 맨팔 의상 편집 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
def main():
 src=N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';need(digest(src)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031','Parent');a=Archive(src.read_bytes());out=D/'bare_firing_inputs_v1';out.mkdir(exist_ok=False);inp=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));recs=[]
 for page,refs in [('a',(68,70,72,76)),('b',(78,80,82,84))]:
  boards={k:Image.new('RGBA',(1536,1536))for k in('exact_firing_targets','same_pose_after_body','after_style')}
  for i,n in enumerate(refs):
   p=D/f'firing_{page}_before_joint_probe_v2/before_{n:03}.png';q=next(x for x in inp['frames']if x['ref']==n);ap=ROOT/q['sources']['after']['body_path'];need(digest(ap)==q['sources']['after']['body_sha256'],'After provenance');v=np.array(Image.open(p));z=np.array(Image.open(ap));im=a.rgba(v,16);after=a.rgba(z)
   for key,img in(('exact_firing_targets',im),('same_pose_after_body',after),('after_style',a.composite((0,85,34,58)[i],0)[0])):boards[key].alpha_composite(img.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
   recs.append({'ref':n,'before_firing_path':p.relative_to(ROOT).as_posix(),'before_firing_sha256':digest(p),'after_body_path':ap.relative_to(ROOT).as_posix(),'after_body_sha256':digest(ap),'muzzle_world':q['muzzle_world'],'window_world':q['window_world']})
  for key,im in boards.items():im.save(out/f'{page}_{key}.png')
 write(out/'manifest.json',{'frames':recs,'input_window_world':[-48,-48,48,48],'cell':[768,768],'integer_scale':8,'scope':'새 사격의 굽힌 팔/총구/머리/몸체 위치를 고정한 채 재킷만 기존후폼 의상으로 편집. 전체 생성물 대신 실제 맨팔 의미영역만 채택 예정.','images':{p.name:digest(p)for p in out.glob('*.png')},'native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
