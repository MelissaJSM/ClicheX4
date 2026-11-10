"""나나 사다리 원화의 공통 축척·팔레트·손/총구 좌표를 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
from scripts.normalize_nana_run import quantize
from scripts.prepare_nana_idle_shot import PILOT,INV,write,shifted
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_ladder import MIRRORS,GROUPS,mirror_canvas
from scripts.solve_sprite_cover import cover
from scripts.solve_paired_cover import paired_cover

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=ROOT/'work/ver_rin_nana/nana_art/ladder_v1';out=args.output.resolve()
 if not args.source.resolve().is_relative_to(root) or not out.is_relative_to(root) or out.exists():raise ValueError('Fresh isolated Nana ladder paths required')
 im=Image.open(args.source).convert('RGBA');lab,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(lab.flat);objs=[(i,(s[1].start,s[0].start,s[1].stop,s[0].stop))for i,s in enumerate(find_objects(lab),1)if sizes[i]>1000];objs.sort(key=lambda q:(int((q[1][1]+q[1][3])/2*3/im.height),q[1][0]))
 if len(objs)!=9:raise ValueError('Expected eight ladder poses and idle calibration')
 scale=45/(objs[-1][1][3]-objs[-1][1][1]);pal=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31]for w in pal],np.int32);out.mkdir(parents=True);records=[]
 soles={143:63,144:63,146:63,149:62,151:61,153:50,154:64,183:70}
 for n,(idx,bb) in zip((143,144,146,149,151,153,154,183),objs):
  crop=np.array(im.crop(bb));crop[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(crop);size=(round(crop.width*scale*.9),round(crop.height*scale));v=quantize(crop,size,rgb);ys,xs=np.nonzero(v);left=round(48-(xs.min()+xs.max())/2);top=soles[n]-int(ys.max());canvas=np.zeros((80,96),np.uint8)
  if left<0 or top<0 or left+size[0]>96 or top+size[1]>80:raise ValueError('Ladder pose clipped')
  canvas[top:top+size[1],left:left+size[0]]=v;save_image(canvas.tobytes(),(96,80),pal,out/f'frame_{n:03d}.png');records.append({'frame':n,'image':f'frame_{n:03d}.png','source_box':bb,'native_size':size,'position':[left-48,top-40],'sole_canvas_y':soles[n]})
 # Reuse the authored air-shot gun and sleeve, never redraw the weapon procedurally.
 arm_source=ROOT/'work/ver_rin_nana/nana_art/air_v1/paired03/gun_043.png';arm=np.array(Image.open(arm_source));ay,ax=np.nonzero(arm);anchor=np.array([ax.min(),float(np.median(ay[ax==ax.min()]))]);body=np.array(Image.open(out/'frame_149.png'));ey,ex=np.nonzero((body==14)&(np.indices(body.shape)[0]<40))
 if not len(ex):raise ValueError('Shot-facing eye missing')
 eye_x,eye_y=round(float(np.median(ex))),round(float(np.median(ey)));yy,xx=np.indices(body.shape);mask=(xx<eye_x+2)&(yy>=eye_y+4)&(yy<eye_y+16);common=body.copy();common[mask]=0;inv=json.loads(INV.read_text('utf8'))
 for n in (150,155):
  original=np.array(Image.open(INV.parent/f'base_{n:03d}.png'));oy,ox=np.nonzero(np.isin(original,[1,2]));edge=ox<ox.min()+2;bb=inv['base_frames'][n]['bounds'];muzzle=np.array([int(ox.min()+bb[0]+48),float(np.median(oy[edge])+bb[1]+40)]);dx,dy=[round(float(v))for v in muzzle-anchor];gun=shifted(arm,dx,dy);gun[(xx>=eye_x-3)&(yy<eye_y+4)]=0;target=common.copy();target[gun!=0]=gun[gun!=0]
  save_image(target.tobytes(),(96,80),pal,out/f'frame_{n:03d}.png');save_image(gun.tobytes(),(96,80),pal,out/f'gun_{n:03d}.png');records.append({'frame':n,'image':f'frame_{n:03d}.png','shared_body':149,'original_muzzle_world':(muzzle-[48,40]).tolist(),'arm_shift':[dx,dy],'eye':[eye_x,eye_y]})
 for n,(alias,delta) in MIRRORS.items():save_image(mirror_canvas(np.array(Image.open(out/f'frame_{n:03d}.png')),delta).tobytes(),(96,80),pal,out/f'frame_{alias:03d}.png')
 write(out/'art.json',{'task':'x_nana','scope':'base_ladder_14','source':args.source.as_posix(),'source_sha256':digest(args.source),'source_inventory':INV.relative_to(ROOT).as_posix(),'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'palette_words':pal,'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'arm_source':arm_source.relative_to(ROOT).as_posix(),'arm_source_sha256':digest(arm_source),'frames':sorted(records,key=lambda r:r['frame']),'runtime_verified':False})
 board=Image.new('RGB',(5*288,3*264),'#222630');dr=ImageDraw.Draw(board)
 for i,n in enumerate([0]+list(range(143,156))+[183]):
  path=ROOT/'out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z/art/frame_000.png'if n==0 else out/f'frame_{n:03d}.png';pic=Image.open(path).convert('RGBA').resize((288,240),Image.Resampling.NEAREST);x,y=i%5*288,i//5*264;board.paste(pic,(x,y+24),pic);dr.text((x+6,y+5),'accepted idle'if n==0 else str(n),fill='white')
 board.save(out/'family_3x.png');plan=json.loads((root/'plan.json').read_text('utf8'));layouts=[]
 for n in GROUPS:
  q=next(r for r in plan['groups']if r['frame']==n);v=np.array(Image.open(out/f'frame_{n:03d}.png'))
  if n==149:
   shot=np.array(Image.open(out/'frame_150.png'))
   for counts in ([6,1,3],[5,2,3],[6,2,2],[5,3,2],[4,3,3]):
    r=paired_cover(v,shot,counts,12)
    if r['fits']:break
  else:r=cover(v!=0,min(q['part_count'],len(q['writable'])-(n in (144,146,151))),12)
  r.update(frame=n);layouts.append(r);print({'frame':n,'fits':r['fits'],'rects':len(r['rects'])},flush=True);write(out/'layout.json',layouts)
 print(json.dumps({'output':str(out),'scale':scale}))
if __name__=='__main__':main()
