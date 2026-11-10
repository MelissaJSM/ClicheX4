"""새 국소 원화의71 하체만 원등록 좌표로 읽어 고정된 상체에 잇는다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
from prepare_inputs import SRC,EXPECTED
ART=D/'dash71_legs_v1/generated.png'
ART_SHA='eaab95456fe7d274ef98c104aca5bec123ba6e198cc7fcee748e9b15dc6195eb'

def main():
 need(digest(SRC)==EXPECTED and digest(ART)==ART_SHA,'Input SHA')
 out=D/'dash71_legs_registered_v1';out.mkdir(exist_ok=False)
 a=Archive(SRC.read_bytes());rec=next(x for x in json.loads((D/'before_first_registered_v2/registration.json').read_text('utf8'))['frames']if x['ref']==71)
 crop=Image.open(ART).convert('RGBA').crop(rec['source_crop']);rgba=np.array(crop)
 labs,_=label(rgba[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;rgba[labs!=counts.argmax(),3]=0;crop=Image.fromarray(rgba)
 crop.save(out/'new_source_crop.png')
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
 split=rec['split'];width=rec['native_width'];hu=rec['upper_height'];hl=rec['lower_height']
 lo=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),pal,'area_vote')
 full=np.zeros((384,384),np.uint8);ox,oy=rec['native_position'];full[160+oy+hu:160+oy+hu+hl,160+ox:160+ox+width]=lo
 src=D/'first_cases_probe_v2/before_071.png';old=np.array(Image.open(src));Y,X=np.indices(old.shape);Y-=160;X-=160
 region=(Y>=17)&(Y<23)&(X>=-10)&(X<9)
 new=old.copy();new[region]=full[region]
 need(np.array_equal(old[~region],new[~region]),'Protected upper body')
 need(np.nonzero(new)[0].max()==np.nonzero(old)[0].max(),'Sole Y')
 need(label(new>0,np.ones((3,3)))[1]==label(old>0,np.ones((3,3)))[1],'New detached component')
 Image.fromarray(new).save(out/'before_071.png');Image.fromarray(region.astype(np.uint8)*255).save(out/'semantic_mask.png');a.rgba(new,16).save(out/'before_071_rgba.png')
 helper.grid([('71 / local authored lower legs only',[('idle',a.composite(0,15)[0]),('old game',a.composite(71,15)[0]),('previous new body',a.rgba(old,16)),('new lower-leg source registered',a.rgba(new,16))])],out/'comparison.png',8)
 write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'source_art':str(ART.relative_to(ROOT)),'source_art_sha256':ART_SHA,'source_body':str(src.relative_to(ROOT)),'source_body_sha256':digest(src),'fixed_mapping':rec,'semantic_mask_sha256':digest(out/'semantic_mask.png'),'changed_texels':int((new!=old).sum()),'outside_semantic_mask_exact':True,'lowest_sole_world_y':int(np.nonzero(new)[0].max()-160),'indexed_sha256':sha(new.tobytes()),'old_game_pixels_used':0,'arbitrary_color_fill':False,'native_packed':False,'runtime_verified':False,'scope':'원생성 보완의 하체만 원래 상하등록 변환으로 읽는다. 전신크기/원점/발바닥은 동일하며 머리·재킷·손·권총은 직전 새등록본을 정확 보존한다.'})
 print(out)
if __name__=='__main__':main()
