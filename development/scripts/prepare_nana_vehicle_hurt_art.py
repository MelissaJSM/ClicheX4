"""체이서·탑승 머리·별도 피격을 수용 나나 축척으로 준비한다."""
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
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.solve_sprite_cover import cover
PARENT=ROOT/'out/ver_rin_nana/nana_air_clone_20261030T012148509868Z'
FRAMES=[*range(162,175),*range(184,204),*range(233,237)]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=ROOT/'work/ver_rin_nana/nana_art/vehicle_hurt_v1';out=args.output.resolve();source=root/'generated.png'
 if not out.is_relative_to(root)or out.exists():raise ValueError('Fresh isolated vehicle/hurt output required')
 arc=(PARENT/'modified.arc').read_bytes()
 if sha256(arc)!='423522ffc88e33fa1ab5c8f98e1eaa510bb8507babe7b0d8deb1f298b027b11b':raise ValueError('Parent changed')
 inv=json.loads(INV.read_text('utf8'));orig=(INV.parent/'original.arc').read_bytes()
 if sha256(orig)!=inv['archive']['sha256']:raise ValueError('Original changed')
 def decoded(arc):
  es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True)
  def get(n):
   f=bank['frames'][n];return canvas_from_parts(decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'],composition_frame(es[3],0,n))%16
  return es,get
 es,compose=decoded(arc);oe,original=decoded(orig)
 im=Image.open(source).convert('RGBA');lab,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(lab.flat);objs=[(i,(s[1].start,s[0].start,s[1].stop,s[0].stop))for i,s in enumerate(find_objects(lab),1)if sizes[i]>1000];objs.sort(key=lambda q:(int((q[1][1]+q[1][3])/2*2/im.height),q[1][0]))
 if len(objs)!=7:raise ValueError(f'Expected seven figures, got {len(objs)}')
 scale=45/(objs[0][1][3]-objs[0][1][1]);pal=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal],np.int32);out.mkdir(parents=True);targets={};registrations=[]
 for n,(idx,bb)in zip((162,166,170,174,233,234),objs[1:]):
  crop=np.array(im.crop(bb));crop[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(crop);size=(round(crop.width*scale*.9),round(crop.height*scale));v=quantize(crop,size,rgb)
  rgba=np.array(crop).astype(np.int32);r,g,b=rgba[:,:,:3].transpose(2,0,1);gm=(g>=60)&(g>r+20)&(g>b+20);votes=np.array(Image.fromarray(np.where(gm,rgba[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX));votes[size[1]//2:]=0;ey,ex=np.unravel_index(votes.argmax(),votes.shape)
  if votes[ey,ex]<8:raise ValueError('Missing green eye')
  # 원작 얼굴 살색 최소 좌표의 대기 대비 차이를 수용 눈 기준에 더한다.
  sy,sx=np.nonzero(np.isin(original(n),[3,4]));anchor=[76+int(sx.min())-69,68+int(sy.min())-67];left,top=anchor[0]-int(ex),anchor[1]-int(ey);v[ey,ex]=14;registration='accepted eye + original face translation relative to original idle';grip=None
  if n<200:
   gy,gx=np.nonzero(np.isin(original(n),[8,9,10])&(np.indices((160,160))[0]>sy.max()));ox=int(gx.min());oy=int(np.median(gy[gx<=ox+1]));hy,hx=np.nonzero(np.isin(v,[10,11,12])&(np.indices(v.shape)[0]>ey+2));ix=int(hx.min());iy=int(np.median(hy[hx<=ix+1]));left,top=ox-ix,oy-iy;anchor=[left+int(ex),top+int(ey)];registration='front grip anchored to original glove edge; common scale preserved';grip={'original':[ox,oy],'source':[ix,iy]}
  canvas=np.zeros((160,160),np.uint8);canvas[top:top+size[1],left:left+size[0]]=v;targets[n]=canvas;registrations.append({'frame':n,'source_box':bb,'native_size':size,'eye':anchor,'registration':registration,'grip':grip})
 rows={r['frame']:r for r in json.loads((root/'plan.json').read_text('utf8'))['groups']};groups=[]
 def put(n,w=None,kind='body'):
  aliases=[k for b,k in rows[n]['aliases']];w=set(rows[n]['base_tiles']if w is None else w);translations={};ps=rows[n]['parts']
  for k in aliases:
   diffs=[]
   for a in ps:
    if a['tile']not in w:continue
    matches=[b for b in rows[k]['parts']if b['tile']==a['tile']and b['flags']==a['flags']]
    if len(matches)==1:diffs.append([matches[0]['x']-a['x'],matches[0]['y']-a['y']])
   if k==198:dx,dy=0,0;targets[k]=np.zeros((160,160),np.uint8)
   else:
    if not diffs or any(d!=diffs[0]for d in diffs):raise ValueError('Alias is not a rigid translation')
    dx,dy=diffs[0];targets[k]=shifted(targets[n],dx,dy)
   translations[str(k)]=[dx,dy]
  armor={t for k in aliases for t in rows[k]['armor_tiles']}
  if w&armor:raise ValueError('Writable armor conflict')
  groups.append({'frame':n,'aliases':aliases,'writable':sorted(w),'kind':kind,'effect_tiles':[],'translations':translations,'budget':rows[n]['budget'],'tile_count':rows[n]['tile_count'],'part_slots':{str(k):[p['index']for p in rows[k]['parts']if p['tile']in w]for k in aliases}})
 for n in(162,166,170,174,233,234):put(n)
 # 원작234와 다른 오라 픽셀만 추출한다. 원래 몸의 얼굴/아머는 남기지 않는다.
 aura=[]
 for n in(235,236):
  old=original(n);base=original(234);mask=(old!=0)&(old!=base)&(base==0);fx=np.where(mask,old,0).astype(np.uint8);target=fx.copy();target[targets[234]!=0]=targets[234][targets[234]!=0];targets[n]=target;put(n);aura.append({'frame':n,'native_aura_pixels':int(mask.sum()),'visible_aura_pixels':int(np.count_nonzero(mask&(targets[234]==0))),'original_indices_and_coordinates_preserved_outside_new_body':True})
 # 머리 전용16x16 창. 승인된 도트의 눈 기준으로 잘라내며 머리 크기를 재조절하지 않는다.
 heads=[]
 for n,src in((184,0),(193,37),(195,94),(196,0),(199,0)):
  body=compose(src);yy,xx=np.nonzero(body==14);keep=yy<np.nonzero(body)[0].min()+16;yy,xx=yy[keep],xx[keep]
  if len(xx)!=1:raise ValueError(f'Ambiguous approved eye {src}: {list(zip(xx,yy))}')
  ex,ey=int(xx[0]),int(yy[0]);head=body[ey-10:ey+6,ex-10:ex+6].copy()
  # 위쪽 얼굴만 사용하는 원작 탑승 창의 왼쪽 GPU 경계는 반드시 투명해야 한다.
  if np.any(head[:,0]):raise ValueError(f'Head touches unsafe U edge {src}')
  p=rows[n]['parts'][0];canvas=np.zeros((160,160),np.uint8);x,y=80+p['x'],80+p['y'];canvas[y:y+16,x:x+16]=head;targets[n]=canvas;put(n,[p['tile']],'head');heads.append({'frame':n,'source':src,'source_box':[ex-10,ey-10,ex+6,ey+6],'scale':1,'original_slot':[x,y],'eye_in_slot':[10,10]})
 for n,v in targets.items():save_image(v.tobytes(),(160,160),pal,out/f'frame_{n:03d}.png')
 art={'task':'x_nana','scope':'base_nana_vehicle_hurt_37','source':source.as_posix(),'source_sha256':digest(source),'source_inventory':INV.relative_to(ROOT).as_posix(),'parent':PARENT.relative_to(ROOT).as_posix(),'canvas_size':[160,160],'origin':[80,80],'remaining_frames':FRAMES,'groups':groups,'frames':[{'frame':n,'image':f'frame_{n:03d}.png'}for n in FRAMES],'palette_words':pal,'effect_index_mapping':list(range(16)),'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'registrations':registrations,'heads':heads,'damage_aura':aura,'blank_reference_preserved':198,'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'runtime_verified':False};write(out/'art.json',art)
 board=Image.new('RGB',(1200,780),'#222630');dr=ImageDraw.Draw(board)
 for i,n in enumerate([0,162,166,170,174,233,234,235,236,184,193,195,196,199]):
  v=compose(0)if n==0 else targets[n];path=out/f'preview_{n:03d}.png';save_image(v.tobytes(),(160,160),pal,path);pic=Image.open(path).convert('RGBA').crop((40,32,120,110)).resize((240,234),Image.Resampling.NEAREST);x,y=i%5*240,i//5*260;board.paste(pic,(x,y+24),pic);dr.text((x+5,y+5),('accepted 'if n==0 else'')+str(n),fill='white')
 board.save(out/'body_review.png');layouts=[]
 for q in groups:
  n=q['frame'];limit=min(min(len(v)for v in q['part_slots'].values()if v),len(q['writable']));result=cover(targets[n]!=0,limit,12);result.update(frame=n);layouts.append(result);write(out/'layout.json',layouts);print({'frame':n,'fits':result['fits'],'rects':len(result.get('rects',[]))},flush=True)
 print(json.dumps({'scale':scale,'registrations':registrations,'heads':heads}))
if __name__=='__main__':main()
