"""94 새 앞다리만 원좌표에 등록하고 긴 뒷다리·상체·권총 보존."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
from prepare_inputs import SRC,EXPECTED
def main():
 need(digest(SRC)==EXPECTED,'Parent');p=D/'fold94_v1/generated.png';need(digest(p)=='a15f0f8a676b495df595f8c4f48305f616d129aa278ada57a56c8a2bdd7c4a3b','Art');a=Archive(SRC.read_bytes());out=D/'fold94_registered_v1';out.mkdir(exist_ok=False);im=Image.open(p).convert('RGBA');need(im.size==(1254,1254),'Actual dimensions')
 rec=next(q for q in json.loads((D/'before_last_registered_v1/registration.json').read_text('utf8'))['frames']if q['ref']==94);box=rec['source_crop'].copy();box[0]-=627;box[2]-=627;crop=im.crop(box);ar=np.array(crop);lab,_=label(ar[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(lab.flat);counts[0]=0;ar[lab!=counts.argmax(),3]=0;crop=Image.fromarray(ar);crop.save(out/'source_crop.png')
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);split=rec['split'];lower=register(crop.crop((0,split,crop.width,crop.height)),(rec['native_width'],rec['lower_height']),pal,'area_vote');donor=np.zeros((384,384),np.uint8);ox,oy=rec['native_position'];y0=160+oy+rec['upper_height'];donor[y0:y0+len(lower),160+ox:160+ox+lower.shape[1]]=lower
 source=D/'more_cases_probe_v2/before_094.png';old=np.array(Image.open(source));poly=[(-5,-3),(5,-3),(9,-1),(12,1),(11,4),(7,6),(7,10),(0,10),(-5,4)];m=Image.new('L',(384,384));ImageDraw.Draw(m).polygon([(x+160,y+160)for x,y in poly],fill=255);mask=np.array(m)>0;new=old.copy();new[mask]=donor[mask]
 need(np.array_equal(new[~mask],old[~mask]),'Outside front leg');Y,X=np.indices(old.shape);Y-=160;X-=160;rear=(X>=13)&(Y>=0);need(np.array_equal(new[rear],old[rear]),'Long rear leg');need(np.nonzero(new)[0].max()==np.nonzero(old)[0].max(),'Back sole height');need(label(new>0,np.ones((3,3)))[1]==label(old>0,np.ones((3,3)))[1],'Detached')
 Image.fromarray(new).save(out/'before_094.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/'semantic_mask.png');a.rgba(new,16).save(out/'before_094_rgba.png');green=(new==14)&(Y>=-3)&(X<13);yy,xx=np.nonzero(green)
 helper.grid([('94 / front folded leg only',[('idle',a.composite(0,15)[0]),('old game pose',a.composite(94,15)[0]),('previous new body',a.rgba(old,16)),('new folded leg',a.rgba(new,16))])],out/'comparison.png',8)
 write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'source_art_sha256':digest(p),'source_body':str(source.relative_to(ROOT)),'source_body_sha256':digest(source),'source_crop':box,'native_mapping':rec,'semantic_polygon_world':poly,'mask_sha256':digest(out/'semantic_mask.png'),'changed_texels':int((old!=new).sum()),'outside_mask_exact':True,'long_rear_leg_exact':True,'lowest_sole_y':int(np.nonzero(new)[0].max()-160),'front_ankle_accent_xy':[[int(x-160),int(y-160)]for y,x in zip(yy,xx)],'new_index_sha256':sha(new.tobytes()),'old_game_pixels_used':0,'color_fill':False,'native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
