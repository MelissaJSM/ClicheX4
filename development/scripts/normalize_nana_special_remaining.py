"""프로스트 타워·라이징 파이어 원화를 공통 축척과 원작을 참고한 기준점에 등록한다."""
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
PARENT=ROOT/'out/ver_rin_nana/nana_special_20261030T004646283984Z'
FRAMES={95,96,100,101,102,103,104,231,232}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=ROOT/'work/ver_rin_nana/nana_art/special_remaining_v1';out=args.output.resolve()
 if not args.source.resolve().is_relative_to(root)or not out.is_relative_to(root)or out.exists():raise ValueError('Fresh isolated special paths required')
 im=Image.open(args.source).convert('RGBA');lab,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(lab.flat);objs=[(i,(s[1].start,s[0].start,s[1].stop,s[0].stop))for i,s in enumerate(find_objects(lab),1)if sizes[i]>1000];objs.sort(key=lambda q:(int((q[1][1]+q[1][3])/2*2/im.height),q[1][0]))
 if len(objs)!=8:raise ValueError('Expected eight figures')
 scale=45/(objs[-1][1][3]-objs[-1][1][1]);pal=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal],np.int32);out.mkdir(parents=True);targets={};reg=[]
 for n,(idx,bb)in zip((95,100,101,102,103,104,231),objs):
  crop=np.array(im.crop(bb));crop[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(crop);size=(round(crop.width*scale*.9),round(crop.height*scale));v=quantize(crop,size,rgb)
  rgba=np.array(crop).astype(np.int32);r,g,b=rgba[:,:,:3].transpose(2,0,1);gm=(g>=60)&(g>r+20)&(g>b+20);votes=np.array(Image.fromarray(np.where(gm,rgba[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX));votes[int(size[1]*.65):]=0;ey,ex=np.nonzero(votes>=8)
  if not len(ex):raise ValueError('Eye missing')
  y0=int(ey.min());votes[:y0]=0;votes[y0+2:]=0;ey0,ex0=np.unravel_index(votes.argmax(),votes.shape);v[ey0,ex0]=14;ys,xs=np.nonzero(v);left=76-int(ex0);top=102-int(ys.max())if n==231 else ({95:60,100:65,101:60,102:67,103:67,104:63}[n]-int(ey0));canvas=np.zeros((160,160),np.uint8);canvas[top:top+size[1],left:left+size[0]]=v;targets[n]=canvas
  reg.append({'frame':n,'source_box':bb,'native_size':size,'eye':[76,top+int(ey0)],'sole_canvas_y':top+int(ys.max()),'registration':'native relative face Y; fixed eye X; grounded231 sole22'})
 targets[96]=shifted(targets[95],1,0);targets[232]=targets[231].copy()
 plan=json.loads((root/'plan.json').read_text('utf8'));rows={r['frame']:r for r in plan['groups']};groups=[]
 for n in(95,100,101,102,103,104,231,232):
  aliases=[k for b,k in rows[n]['aliases']];w=set(rows[n]['base_tiles']);spare=[];w.update(spare)
  groups.append({'frame':n,'aliases':aliases,'writable':sorted(w),'unreferenced_tiles':spare,'kind':'body','effect_tiles':[],'translations':{str(k):[1 if k==96 else 0,0]for k in aliases},'budget':rows[n]['budget'],'tile_count':rows[n]['tile_count'],'part_slots':{str(k):[p['index']for p in rows[k]['parts']if p['tile']in w]for k in aliases}})
 for n,v in targets.items():save_image(v.tobytes(),(160,160),pal,out/f'frame_{n:03d}.png')
 art={'task':'x_nana','scope':'base_nana_special_remaining_9','source':args.source.as_posix(),'source_sha256':digest(args.source),'source_inventory':INV.relative_to(ROOT).as_posix(),'parent':PARENT.relative_to(ROOT).as_posix(),'canvas_size':[160,160],'origin':[80,80],'remaining_frames':sorted(FRAMES),'groups':groups,'frames':[{'frame':n,'image':f'frame_{n:03d}.png'}for n in sorted(targets)],'palette_words':pal,'effect_index_mapping':list(range(16)),'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'registrations':reg,'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'runtime_verified':False};write(out/'art.json',art)
 arc=(PARENT/'modified.arc').read_bytes();es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True)
 board=Image.new('RGB',(960,828),'#222630');dr=ImageDraw.Draw(board)
 for i,n in enumerate([0,138,95,96,100,101,102,103,104,231,232]):
  if n in targets:v=targets[n]
  else:
   f=bank['frames'][n];v=canvas_from_parts(decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'],composition_frame(es[3],0,n))%16
  path=out/f'preview_{n:03d}.png';save_image(v.tobytes(),(160,160),pal,path);pic=Image.open(path).convert('RGBA').crop((40,25,120,109)).resize((240,252),Image.Resampling.NEAREST);x,y=i%4*240,i//4*276;board.paste(pic,(x,y+24),pic);dr.text((x+5,y+5),('accepted 'if n in(0,138)else'')+str(n),fill='white')
 board.save(out/'body_review.png');layouts=[]
 for q in groups:
  n=q['frame'];limit=min(min(len(v)for v in q['part_slots'].values()),len(q['writable']));r=cover(targets[n]!=0,limit,10);r.update(frame=n);layouts.append(r);write(out/'layout.json',layouts);print({'frame':n,'fits':r['fits'],'rects':len(r.get('rects',[]))},flush=True)
 print(json.dumps({'scale':scale,'registrations':reg}))
if __name__=='__main__':main()
