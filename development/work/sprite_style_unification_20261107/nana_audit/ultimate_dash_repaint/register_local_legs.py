"""71/75 신발 분리·81 보폭 새원화만 국소등록, 기존 신규 상체 exact 보존."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from prepare_inputs import SRC,EXPECTED
from register_page import register
SPECS={
71:('low_boots_v1','05483debf18fb41f20349afe93138e517494006e49216d6c11689006283eee73','before_first_registered_v2','first_cases_probe_v2',[-627,0],0),
75:('low_boots_v1','05483debf18fb41f20349afe93138e517494006e49216d6c11689006283eee73','before_second_registered_v1','before_second_registered_v1',[0,0],1),
81:('stance81_v1','7bec05270df21c37bcf6698e007a5ba4ab2e53f544f3db87a708e3be13399bf3','before_second_registered_v1','before_second_registered_v1',[-627,-627],0)}

def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'local_legs_registered_v4';out.mkdir(exist_ok=False);rows=[];records=[]
 palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);Y,X=np.indices((384,384));Y-=160;X-=160
 for n,(folder,hs,mapped,bodyfolder,delta,cellindex)in SPECS.items():
  p=D/folder/'generated.png';need(digest(p)==hs,'Source art');im=Image.open(p).convert('RGBA');need(im.size==(1254,1254),'Actual source dimensions')
  rec=next(x for x in json.loads((D/mapped/'registration.json').read_text('utf8'))['frames']if x['ref']==n)
  cx=cellindex*627;aa=np.array(im.crop((cx,0,cx+627,627)));labs,_=label(aa[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;k=int(counts.argmax());aa[labs!=k,3]=0;yy,xx=np.nonzero(labs==k);need(len(xx)>1000,'Connected figure')
  allrgba=np.zeros((1254,1254,4),np.uint8);allrgba[0:627,cx:cx+627]=aa
  box=[rec['source_crop'][0]+delta[0],rec['source_crop'][1]+delta[1],rec['source_crop'][2]+delta[0],int(yy.max()+1)]
  crop=Image.fromarray(allrgba).crop(box);crop.save(out/f'source_crop_{n:03}.png');split=rec['split'];need(crop.height>split,'Lower source');lo=register(crop.crop((0,split,crop.width,crop.height)),(rec['native_width'],rec['lower_height']),palette,'area_vote')
  donor=np.zeros((384,384),np.uint8);ox,oy=rec['native_position'];y0=160+oy+rec['upper_height'];donor[y0:y0+len(lo),160+ox:160+ox+lo.shape[1]]=lo
  src=D/bodyfolder/f'before_{n:03}.png';old=np.array(Image.open(src));mask=(Y>=17)&(Y<23)&(X>=-12)&(X<10)
  polygons=None
  if n==81:
   polygons=[[(0,5),(10,5),(11,10),(10,14),(6,23),(-6,23),(-6,12)],[(11,7),(17,7),(24,12),(30,19),(30,23),(20,23),(17,15),(12,10)]]
   m=Image.new('L',(384,384));dr=ImageDraw.Draw(m)
   for poly in polygons:dr.polygon([(x+160,y+160)for x,y in poly],fill=255)
   mask=np.array(m)>0
  new=old.copy();new[mask]=donor[mask]
  Image.fromarray(new).save(out/f'diagnostic_{n:03}.png');a.rgba(new,16).save(out/f'diagnostic_{n:03}_rgba.png')
  labs,num=label(new>0,np.ones((3,3)));components=[]
  for i in range(1,num+1):
   yy,xx=np.nonzero(labs==i);components.append({'pixels':len(xx),'box':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)]})
  write(out/f'diagnostic_{n:03}.json',{'components':components})
  need(np.array_equal(new[~mask],old[~mask]),'Outside local lower legs')
  need(np.nonzero(new)[0].max()==np.nonzero(old)[0].max(),'Sole height')
  need(label(new>0,np.ones((3,3)))[1]==label(old>0,np.ones((3,3)))[1],f'Detached component {n}')
  Image.fromarray(new).save(out/f'before_{n:03}.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/f'semantic_mask_{n:03}.png');a.rgba(new,16).save(out/f'before_{n:03}_rgba.png')
  records.append({'ref':n,'source_art':str(p.relative_to(ROOT)),'source_art_sha256':hs,'original_mapping_file':str((D/mapped/'registration.json').relative_to(ROOT)),'original_mapping_sha256':digest(D/mapped/'registration.json'),'crop_box_actual_art':box,'original_crop_box':rec['source_crop'],'original_to_new_cell_translation':delta,'full_source_figure_bbox':[int(xx.min()+cx),int(yy.min()),int(xx.max()+cx+1),int(yy.max()+1)],'native_position':rec['native_position'],'native_lower_shape':list(lo.shape),'source_body':str(src.relative_to(ROOT)),'source_body_sha256':digest(src),'mask_sha256':digest(out/f'semantic_mask_{n:03}.png'),'polygons_world':polygons,'mask_world_rect':[-12,17,10,23]if n!=81 else None,'outside_mask_exact':True,'changed_texels':int((new!=old).sum()),'new_index_sha256':sha(new.tobytes()),'sole_world_y':int(np.nonzero(new)[0].max()-160),'arbitrary_color_fill':False,'old_game_pixels_used':0})
  rows.append((f'Ultimate local legs {n}',[('accepted idle',a.composite(0,15)[0]),('old game contacts',a.composite(n,15)[0]),('previous new body',a.rgba(old,16)),('new authored local legs',a.rgba(new,16))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'frames':records,'native_packed':False,'runtime_verified':False,'method':'원화 국소 다리를 원래 눈/귀/발바닥 변환에 등록. 그림 위쪽은 직전 신규몸 exact. 원생성 발끝 전체를 포함하도록 하단 crop만 실제 알파에 맞추며 최하단 네이티브 y22는 고정한다.'});print(out)
if __name__=='__main__':main()
