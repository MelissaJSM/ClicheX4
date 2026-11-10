"""승리와 귀환 원화를 수용 나나 팔레트/공통 축척으로 등록한다."""
import argparse,json,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects,binary_dilation
from scripts.prepare_nana_idle_shot import INV,PILOT,write,shifted
from scripts.normalize_nana_run import quantize
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.solve_sprite_cover import cover
PARENT=ROOT/'out/ver_rin_nana/nana_arrival_20261029T235340020385Z'
FRAMES=set(range(156,162))|set(range(204,208))

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=ROOT/'work/ver_rin_nana/nana_art/victory_v1';out=args.output.resolve()
 if not args.source.resolve().is_relative_to(root)or not out.is_relative_to(root)or out.exists():raise ValueError('Fresh isolated Nana victory paths required')
 im=Image.open(args.source).convert('RGBA');lab,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(lab.flat);objs=[(i,(s[1].start,s[0].start,s[1].stop,s[0].stop))for i,s in enumerate(find_objects(lab),1)if sizes[i]>1000];objs.sort(key=lambda q:(int((q[1][1]+q[1][3])/2*2/im.height),q[1][0]))
 if len(objs)!=7:raise ValueError(f'Expected seven figures, got {len(objs)}')
 scale=45/(objs[-1][1][3]-objs[-1][1][1]);pal=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal],np.int32);out.mkdir(parents=True);targets={};registrations=[]
 for n,(idx,bb) in zip((156,158,204,205,206,207),objs):
  crop=np.array(im.crop(bb));crop[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(crop);size=(round(crop.width*scale*.9),round(crop.height*scale));v=quantize(crop,size,rgb)
  rgba=np.array(crop).astype(np.int32);red,green,blue=rgba[:,:,:3].transpose(2,0,1);gm=(green>=60)&(green>red+20)&(green>blue+20);votes=np.array(Image.fromarray(np.where(gm,rgba[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX));votes[int(size[1]*.65):]=0;ey,ex=np.nonzero(votes>=8)
  if not len(ex):raise ValueError('Eye missing')
  y0=int(ey.min());candidates=votes.copy();candidates[:y0]=0;candidates[y0+2:]=0;ey0,ex0=np.unravel_index(candidates.argmax(),votes.shape);v[ey0,ex0]=14;ys,xs=np.nonzero(v);left=76-int(ex0);sole=92 if n==158 else 102;top=sole-int(ys.max());canvas=np.zeros((160,160),np.uint8)
  if min(left,top)<0 or left+size[0]>160 or top+size[1]>160:raise ValueError('Pose clipped')
  canvas[top:top+size[1],left:left+size[0]]=v;targets[n]=canvas;registrations.append({'frame':n,'source_box':bb,'native_size':size,'position':[left-80,top-80],'eye':[76,top+int(ey0)],'sole_canvas_y':sole})
 arc=(PARENT/'modified.arc').read_bytes();es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};g,c=es[2],es[3];bank=graphics_bank(g,0,allow_bank_aliases=True);plan=json.loads((root/'plan.json').read_text('utf8'));rows={r['frame']:r for r in plan['groups']};groups=[]
 def compose(n):
  f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;return canvas_from_parts(raw,f['tile_count'],composition_frame(c,0,n))%16
 def put(n,kind='body'):
  aliases=[k for b,k in rows[n]['aliases']];ps={k:rows[k]['parts']for k in aliases};w=sorted({r['tile']for p in ps.values()for r in p});groups.append({'frame':n,'aliases':aliases,'writable':w,'kind':kind,'effect_tiles':[],'translations':{str(k):[0,0]for k in aliases},'budget':rows[n]['budget'],'tile_count':rows[n]['tile_count'],'part_slots':{str(k):[r['index']for r in p]for k,p in ps.items()}})
 fxmap=np.array([0,5,1,10,12,9,7,5,13,9,6,1,8,7,6,5],np.uint8)
 # Reuse precisely the previous pose under a bright materialization outline.
 targets[157]=shifted(targets[156],0,-1);m=targets[157]!=0;halo=binary_dilation(m,iterations=2);inner=binary_dilation(m);targets[157][halo&~inner]=7;targets[157][inner&~m]=13
 ascent=targets[158].copy();fx=fxmap[compose(159)];energy_map=np.array([0,5,6,7,8,5,6,7,8,9,8,9,13,13,9,9],np.uint8);energy=energy_map[ascent];fx[energy!=0]=energy[energy!=0];targets[158]=fx
 # The adjacent empty energy shell has two pixels outside frame158's
 # original coverage. Keep all Nana body pixels and the original slot layout.
 coverage=np.zeros((160,160),bool)
 for part in composition_frame(c,0,158)['parts']:
  x,y=part['x']+80,part['y']+80;coverage[y:y+16,x:x+16]=True
 if np.any((ascent!=0)&~coverage):raise ValueError('Return body outside original parts')
 clipped_effect_pixels=int(np.count_nonzero((targets[158]!=0)&~coverage));targets[158][~coverage]=0
 for n in(156,157,158,204,205,206,207):put(n,'original_grid'if n==158 else'body')
 for n in(159,160):put(n,'effect')
 for n,v in targets.items():save_image(v.tobytes(),(160,160),pal,out/f'frame_{n:03d}.png')
 save_image(ascent.tobytes(),(160,160),pal,out/'ascent_body.png')
 art={'task':'x_nana','scope':'base_nana_victory_return_10','source':args.source.as_posix(),'source_sha256':digest(args.source),'source_inventory':INV.relative_to(ROOT).as_posix(),'parent':PARENT.relative_to(ROOT).as_posix(),'canvas_size':[160,160],'origin':[80,80],'remaining_frames':sorted(FRAMES),'groups':groups,'frames':[{'frame':n,'image':f'frame_{n:03d}.png'}for n in sorted(targets)],'palette_words':pal,'effect_index_mapping':fxmap.tolist(),'ascent_energy_mapping':energy_map.tolist(),'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'registrations':registrations,'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'runtime_verified':False};write(out/'art.json',art)
 art.update(return_body_preserved_under_effect=True,return_shell_edge_pixels_omitted=clipped_effect_pixels);write(out/'art.json',art)
 board=Image.new('RGB',(960,552),'#222630');dr=ImageDraw.Draw(board)
 for i,n in enumerate([0,204,205,206,207,156,157,158]):
  v=compose(0)if n==0 else targets[n];path=out/f'preview_{n:03d}.png';save_image(v.tobytes(),(160,160),pal,path);pic=Image.open(path).convert('RGBA').crop((40,25,120,109)).resize((240,252),Image.Resampling.NEAREST);x,y=i%4*240,i//4*276;board.paste(pic,(x,y+24),pic);dr.text((x+5,y+5),'accepted idle'if n==0 else str(n),fill='white')
 board.save(out/'body_review.png');layouts=[]
 for q in groups:
  if q['kind']in('effect','original_grid'):continue
  n=q['frame'];limit=min(min(len(v)for v in q['part_slots'].values()),len(q['writable']));r=cover(targets[n]!=0,limit,10);r.update(frame=n);layouts.append(r);write(out/'layout.json',layouts);print({'frame':n,'fits':r['fits'],'rects':len(r.get('rects',[]))},flush=True)
 print(json.dumps({'output':str(out),'scale':scale,'registrations':registrations}))
if __name__=='__main__':main()
