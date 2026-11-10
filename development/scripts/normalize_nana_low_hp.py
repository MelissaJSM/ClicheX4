"""나나 저체력 원화 한 몸에 접지 호흡과 입 오버레이를 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
from scripts.normalize_nana_run import quantize
from scripts.prepare_nana_idle_shot import PILOT,INV,write,shifted
from scripts.prepare_shibuki_idle import breathe
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.solve_sprite_cover import cover

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=ROOT/'work/ver_rin_nana/nana_art/low_hp_v1';out=args.output.resolve()
 if not args.source.resolve().is_relative_to(root) or not out.is_relative_to(root) or out.exists():raise ValueError('Fresh isolated Nana low HP paths required')
 im=Image.open(args.source).convert('RGBA');lab,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(lab.flat);objs=[(i,(s[1].start,s[0].start,s[1].stop,s[0].stop))for i,s in enumerate(find_objects(lab),1)if sizes[i]>1000];objs.sort(key=lambda q:q[1][0])
 if len(objs)!=3:raise ValueError('Expected idle calibration and two tired figures')
 scale=45/(objs[0][1][3]-objs[0][1][1]);pal=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31]for w in pal],np.int32);out.mkdir(parents=True);registered=[];sources=[]
 for idx,bb in objs[1:]:
  crop=np.array(im.crop(bb));crop[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(crop);size=(round(crop.width*scale*.9),round(crop.height*scale));v=quantize(crop,size,rgb)
  # Green brooch is a separate landmark. Preserve the tiny eye vote in the
  # head region even when the larger brooch already occupies palette14.
  rgba=np.array(crop).astype(np.int32);red,green,blue=rgba[:,:,:3].transpose(2,0,1);gm=(green>=60)&(green>red+20)&(green>blue+20);votes=np.array(Image.fromarray(np.where(gm,rgba[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX));votes[size[1]//4:]=0
  if votes.max()>=8:v[np.unravel_index(votes.argmax(),votes.shape)]=14
  ys,xs=np.nonzero(v);ey,ex=np.nonzero((v==14)&(np.indices(v.shape)[0]<size[1]//4))
  if not len(ex):raise ValueError('Eye landmark missing')
  left=44-round(float(np.median(ex)));top=62-int(ys.max());canvas=np.zeros((80,96),np.uint8)
  if left<24 or left+size[0]>72 or top<16 or top+size[1]>63:raise ValueError('Body outside registered breathing region')
  canvas[top:top+size[1],left:left+size[0]]=v;registered.append(canvas);sources.append({'source_box':bb,'native_size':size,'position':[left-48,top-40],'eye':[44,top+round(float(np.median(ey)))]})
 base,sample=registered;ex,ey=sources[0]['eye'];sample=shifted(sample,ex-sources[1]['eye'][0],ey-sources[1]['eye'][1]);yy,xx=np.indices(base.shape)
 # Only one authored open-mouth colour enters the fixed face; other generated
 # changes are discarded. Restrict it to skin below the eye, away from outline.
 candidates=(xx>=ex-1)&(xx<=ex+2)&(yy>=ey+2)&(yy<=ey+4)&np.isin(base,[5,6,10,11,12,13])&np.isin(sample,[1,2,5,6])&(base!=sample)
 cy,cx=np.nonzero(candidates)
 if not len(cx):
  save_image(base.tobytes(),(96,80),pal,out/'debug_base.png');save_image(sample.tobytes(),(96,80),pal,out/'debug_open.png');raise ValueError('Generated open mouth not isolated')
 k=int(np.argmin((cx-ex)**2+(cy-(ey+3))**2));mx,my=int(cx[k]),int(cy[k]);opened=base.copy();opened[my,mx]=sample[my,mx];records=[];layouts=[];board=Image.new('RGB',(4*288,2*264),'#222630');dr=ImageDraw.Draw(board)
 for i,(n,delta) in enumerate(((120,1),(122,0),(124,-1))):
  for variant,src in enumerate((base,opened)):
   canvas=np.zeros_like(base);canvas[15:63,24:72]=breathe(src[15:63,24:72],delta)
   if not np.array_equal(canvas[58:],base[58:]):raise ValueError('Breathing soles drift')
   save_image(canvas.tobytes(),(96,80),pal,out/f'frame_{n+variant:03d}.png');records.append({'frame':n+variant,'image':f'frame_{n+variant:03d}.png','breathing_delta':delta,'mouth_open':bool(variant),'eye':[ex,ey+delta]})
   pic=Image.open(out/f'frame_{n+variant:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);x,y=(i+1)*288,variant*264;board.paste(pic,(x,y+24),pic);dr.text((x+5,y+5),str(n+variant),fill='white')
   if variant==0:r=cover(canvas!=0,7,10);r.update(frame=n);layouts.append(r);print({'frame':n,'fits':r['fits'],'rects':len(r['rects'])},flush=True)
 for row in range(2):
  pic=Image.open(ROOT/'out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z/art/frame_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);board.paste(pic,(0,row*264+24),pic);dr.text((5,row*264+5),'accepted idle',fill='white')
 board.save(out/'body_review.png');write(out/'layout.json',layouts);write(out/'art.json',{'task':'x_nana','scope':'base_low_hp_6','source':args.source.as_posix(),'source_sha256':digest(args.source),'source_inventory':INV.relative_to(ROOT).as_posix(),'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'palette_words':pal,'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'source_registration':sources,'mouth_sample':{'x':mx,'y':my,'index':int(sample[my,mx])},'feet_unchanged_from_row':58,'frames':records,'runtime_verified':False})
 plan=json.loads((root/'plan.json').read_text('utf8'));pics=[]
 for s in plan['animation']['steps']:
  pic=Image.open(out/f"frame_{s['frame']:03d}.png").convert('RGBA');bg=Image.new('RGBA',pic.size,'#222630');bg.alpha_composite(pic);pics.append(bg.resize((384,320),Image.Resampling.NEAREST))
 pics[0].save(out/'breathing_preview.gif',save_all=True,append_images=pics[1:],duration=[round(s['duration_ticks']*1000/60)for s in plan['animation']['steps']],loop=0,disposal=2);print(json.dumps({'output':str(out),'scale':scale,'mouth':[mx,my,int(sample[my,mx])]}))
if __name__=='__main__':main()
