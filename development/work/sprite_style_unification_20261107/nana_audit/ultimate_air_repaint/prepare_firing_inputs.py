"""11짝의 기존 실제 총구와 새 몸체를 같은 좌표로 제시하는 생성 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from check_first_geometry import full
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());need(sha(a.data)=='bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45','Parent changed')
 allq=json.loads((D/'weapon_constraints_v1/manifest.json').read_text('utf8'))['frames']
 for page,refs in [('a',[34,36,38,40]),('b',[42,44,46,48]),('c',[50,52,54])]:
  out=D/f'firing_{page}_inputs_v1';out.mkdir(exist_ok=False);boards={k:Image.new('RGBA',(1280,1280))for k in('before_original_shot','before_new_body','after_new_body','original_barrel_only')};recs=[]
  for i,n in enumerate(refs):
   before=np.array(Image.open(D/'canonical_cases_probe_v1'/f'before_{n-1:03}.png'));after=np.array(Image.open(D/'costume_pair_probe_v2'/f'after_{n-1:03}.png'));orig=a.composite(n,15)[0];bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'));q=next(q for q in allq if q['ref']==n)
   ims={'before_original_shot':orig,'before_new_body':a.rgba(before,16),'after_new_body':a.rgba(after,0),'original_barrel_only':a.rgba(bar,16)}
   for k,im in ims.items():boards[k].alpha_composite(im.crop((112,112,208,208)).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640))
   recs.append({'ref':n,'paired_ref':n-1,'original_muzzle_x':q['muzzle_x'],'original_gun_window':q['window_world'],'cell':[i%2,i//2],'before_body_sha256':sha(before.tobytes()),'after_body_sha256':sha(after.tobytes()),'source_arc_sha256':sha(a.data)})
  for k,im in boards.items():im.save(out/f'{k}.png')
  master=Image.new('RGBA',(1280,640));master.alpha_composite(a.composite(0,15)[0].crop((120,120,200,200)).resize((640,640),Image.Resampling.NEAREST),(0,0));master.alpha_composite(a.composite(85,15)[0].crop((112,120,192,200)).resize((640,640),Image.Resampling.NEAREST),(640,0));master.save(out/'accepted_idle_and_shot85.png')
  write(out/'inputs.json',{'frames':recs,'window_world':[-48,-48,48,48],'cell':[640,640],'source_images':{p.name:digest(p)for p in out.glob('*.png')},'art_created':False,'source_scope':'Read-only extracted graphics; originals are muzzle constraints, new body is style/geometry master. After garment composition is still a candidate.'})
 print('Prepared a/b/c 4+4+3 input sheets')
if __name__=='__main__':main()
