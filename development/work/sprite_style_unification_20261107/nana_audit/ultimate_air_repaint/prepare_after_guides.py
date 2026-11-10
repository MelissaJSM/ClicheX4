"""현재 수용 몸체와 캡슐 후 의상 기준을 후속 생성 입력으로 준비."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from make_body_cycle import source
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'after_guides_first_v1';out.mkdir(exist_ok=False);keys=[33,39,47,51];board=Image.new('RGBA',(1280,1280));records=[]
 for i,n in enumerate(keys):
  idx=np.array(Image.open(source(n)));im=a.rgba(idx,16).crop((120,120,200,200)).resize((640,640),Image.Resampling.NEAREST);board.alpha_composite(im,(i%2*640,i//2*640));records.append({'ref':n,'accepted_before_body':source(n).relative_to(ROOT).as_posix(),'indexed_file_sha256':digest(source(n)),'cell':[i%2,i//2]})
 board.save(out/'new_before_native_pose_guides.png');refs=Image.new('RGBA',(1280,640))
 for i,(n,mask)in enumerate([(0,15),(0,0),(85,15),(85,0)]):
  im=a.composite(n,mask)[0].crop((128,120,192,184)).resize((320,320),Image.Resampling.NEAREST);refs.alpha_composite(im,(i*320,150))
 refs.save(out/'current_two_costume_masters.png');write(out/'manifest.json',{'parent_arc_sha256':sha(a.data),'frames':records,'images':{p.name:digest(p)for p in out.glob('*.png')},'scope':'Only existing sources extracted. After costume art not yet generated. Keep accepted new head/face/legs/shoes as common source; obtain actual costume/arm drawing.','new_art':False});print(str(out))
if __name__=='__main__':main()
