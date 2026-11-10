"""나나 등장 원화와 실체화 효과를 원작17참조의 공유 구조에 등록한다."""
import argparse,json,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
from scripts.prepare_nana_idle_shot import INV,PILOT,write,shifted
from scripts.normalize_nana_run import quantize
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.solve_sprite_cover import cover
PARENT=ROOT/'out/ver_rin_nana/nana_low_hp_20261029T233800161474Z'

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=ROOT/'work/ver_rin_nana/nana_art/arrival_v1';out=args.output.resolve()
 if not args.source.resolve().is_relative_to(root)or not out.is_relative_to(root)or out.exists():raise ValueError('Fresh isolated Nana arrival paths required')
 im=Image.open(args.source).convert('RGBA');lab,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(lab.flat);objs=[(i,(s[1].start,s[0].start,s[1].stop,s[0].stop))for i,s in enumerate(find_objects(lab),1)if sizes[i]>1000];objs.sort(key=lambda q:(int((q[1][1]+q[1][3])/2*2/im.height),q[1][0]))
 if len(objs)!=6:raise ValueError(f'Expected six figures, got {len(objs)}')
 scale=45/(objs[-1][1][3]-objs[-1][1][1]);pal=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal],np.int32);out.mkdir(parents=True);targets={};records=[]
 for n,(idx,bb) in zip((133,135,136,137,138),objs):
  crop=np.array(im.crop(bb));crop[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(crop);size=(round(crop.width*scale*.9),round(crop.height*scale));v=quantize(crop,size,rgb)
  rgba=np.array(crop).astype(np.int32);red,green,blue=rgba[:,:,:3].transpose(2,0,1);gm=(green>=60)&(green>red+20)&(green>blue+20);votes=np.array(Image.fromarray(np.where(gm,rgba[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX));votes[int(size[1]*.65):]=0;ey,ex=np.nonzero(votes>=8)
  if not len(ex):raise ValueError('Eye missing')
  y0=int(ey.min());candidates=votes.copy();candidates[:y0]=0;candidates[y0+2:]=0;ey0,ex0=np.unravel_index(candidates.argmax(),votes.shape);v[ey0,ex0]=14;ys,xs=np.nonzero(v);left=76-int(ex0);top=102-int(ys.max());canvas=np.zeros((160,160),np.uint8)
  if min(left,top)<0 or left+size[0]>160 or top+size[1]>160:raise ValueError('Pose clipped')
  canvas[top:top+size[1],left:left+size[0]]=v;targets[n]=canvas;records.append({'frame':n,'source_box':bb,'native_size':size,'position':[left-80,top-80],'eye':[76,top+int(ey0)],'sole_canvas_y':102})
 arc=(PARENT/'modified.arc').read_bytes();es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};g,c=es[2],es[3];bank=graphics_bank(g,0,allow_bank_aliases=True);plan=json.loads((root/'plan.json').read_text('utf8'));rows={r['frame']:r for r in plan['groups']};groups=[]
 def compose(n,tiles=None):
  f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cp=composition_frame(c,0,n)
  if tiles is not None:cp={**cp,'parts':[r for r in cp['parts']if r['tile']in tiles]}
  return canvas_from_parts(raw,f['tile_count'],cp)%16
 def put(n,aliases=None,writable=None,kind='body',effects=None):
  aliases=aliases or[k for b,k in rows[n]['aliases']];parts={k:rows[k]['parts']for k in aliases};w=sorted({r['tile']for ps in parts.values()for r in ps}if writable is None else writable)
  groups.append({'frame':n,'aliases':aliases,'writable':w,'kind':kind,'effect_tiles':sorted(effects or[]),'translations':{str(k):[0,0]for k in aliases},'budget':rows[n]['budget'],'tile_count':rows[n]['tile_count'],'part_slots':{str(k):[r['index']for r in ps if r['tile']in w]for k,ps in parts.items()}})
 # Original blue energy ramps become the existing Nana pink/white ramp.
 fxmap=np.array([0,5,1,10,12,9,7,5,13,9,6,1,8,7,6,5],np.uint8)
 def over(bg,fg):
  v=bg.copy();v[fg!=0]=fg[fg!=0];return v
 put(133);put(135);put(136,writable=range(7),effects=[7]);put(137,writable=range(7),effects=[7]);put(138);targets[139]=shifted(targets[138],0,-1);put(139)
 idle=compose(0);targets[141]=idle.copy();put(141,writable=range(7),effects=[7]);targets[142]=idle.copy();put(142);targets[140]=np.where(idle!=0,13,0).astype(np.uint8);put(140,writable=range(8),effects=[8])
 orb=fxmap[compose(129)];targets[130]=over(orb,np.where(targets[133]!=0,13,0).astype(np.uint8))
 # The outer energy ring is mirrored from shared tiles. It occludes the
 # materializing silhouette; the following full-color pose reveals the body.
 cp130=composition_frame(c,0,130);tiles130=[p['tile']for p in cp130['parts']];native_rim=fxmap[compose(130)]
 for p130 in cp130['parts']:
  if tiles130.count(p130['tile'])>1:
   x,y=p130['x']+80,p130['y']+80;targets[130][y:y+16,x:x+16]=native_rim[y:y+16,x:x+16]
 put(130,kind='original_grid')
 targets[131]=np.where(targets[133]!=0,13,0).astype(np.uint8);targets[132]=np.zeros((160,160),np.uint8);put(131,[131,132],range(8,16),effects=range(8));groups[-1]['part_slots']['132']=[]
 targets[134]=over(orb,targets[133]);put(134)
 for n in(126,128,129):put(n,kind='effect')
 if {k for q in groups for k in q['aliases']}!=set(range(126,143)):raise ValueError('Incomplete arrival')
 for n,v in targets.items():save_image(v.tobytes(),(160,160),pal,out/f'frame_{n:03d}.png')
 art={'task':'x_nana','scope':'base_nana_arrival_17','source':args.source.as_posix(),'source_sha256':digest(args.source),'source_inventory':INV.relative_to(ROOT).as_posix(),'parent':PARENT.relative_to(ROOT).as_posix(),'canvas_size':[160,160],'origin':[80,80],'remaining_frames':list(range(126,143)),'groups':groups,'frames':[{'frame':n,'image':f'frame_{n:03d}.png'}for n in sorted(targets)],'palette_words':pal,'effect_index_mapping':fxmap.tolist(),'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'registrations':records,'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'runtime_verified':False};write(out/'art.json',art)
 board=Image.new('RGB',(4*240,3*264),'#222630');dr=ImageDraw.Draw(board)
 for i,n in enumerate([0,133,135,136,137,138,139,140,141,142,130,134]):
  v=idle if n==0 else targets[n];path=out/f'preview_{n:03d}.png';save_image(v.tobytes(),(160,160),pal,path);pic=Image.open(path).convert('RGBA').crop((40,35,120,115)).resize((240,240),Image.Resampling.NEAREST);x,y=i%4*240,i//4*264;board.paste(pic,(x,y+24),pic);dr.text((x+5,y+5),'accepted idle'if n==0 else str(n),fill='white')
 board.save(out/'body_review.png');layouts=[]
 for q in groups:
  if q['kind']in('effect','original_grid'):continue
  n=q['frame'];limit=min(min(len(v)for v in q['part_slots'].values()if v),len(q['writable']));r=cover(targets[n]!=0,limit,10);r.update(frame=n);layouts.append(r);write(out/'layout.json',layouts);print({'frame':n,'fits':r['fits'],'rects':len(r.get('rects',[]))},flush=True)
 print(json.dumps({'output':str(out),'scale':scale,'registrations':records}))
if __name__=='__main__':main()
