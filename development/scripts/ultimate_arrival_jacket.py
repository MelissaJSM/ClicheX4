"""승인 캐릭터 몸을 보호하며 누락 등장 재킷만 생성 원화에서 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.ultimate_costume_swap import SOURCES,WORK,layer,image,pack,require,save_json
from scripts.c01_audio_build import read_disc
from scripts.project import digest
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import rgba,board,sha
from scripts.overhaul_sprites_state_layers import part_layer
from scripts.prepare_rin_run import quantize
from src.psx_player import composition_frame,graphics_bank,decode_stream,bank_offsets
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.overhaul_sprites_costume_pack import resize_tile_storage,repack_variable

MASTERS=(133,135,136,137)
SHIBUKI={
 133:dict(eye=(75,81),region=(59,83,96,99),head=(66,0,96,85),hands=[(75,97,82,104),(87,91,94,96)]),
 135:dict(eye=(75,72),region=(62,75,94,93),head=(66,0,95,76),hands=[(64,76,73,81),(84,83,90,88)]),
 136:dict(eye=(75,71),region=(61,74,94,93),head=(66,0,95,75),hands=[(64,75,73,80),(84,82,90,88)]),
 137:dict(eye=(75,72),region=(61,64,94,93),head=(70,0,86,78),hands=[(63,58,70,67),(83,58,91,67)]),
}
NANA={
 133:dict(eye=(76,78),region=(61,80,98,99),head=(68,0,98,82),hands=[(62,88,70,95),(77,98,84,104)]),
 135:dict(eye=(76,67),region=(64,70,94,91),head=(68,0,96,72),hands=[(65,70,72,77),(82,70,89,78)]),
 136:dict(eye=(76,68),region=(62,71,96,91),head=(70,0,97,72),hands=[(65,65,73,74),(82,79,88,85)]),
 137:dict(eye=(76,65),region=(62,60,97,89),head=(72,0,88,70),hands=[(66,51,74,62),(88,77,96,84)]),
}

def region_mask(shape,box):
 a=np.zeros(shape,bool);x,y,x2,y2=box;a[y:y2,x:x2]=True;return a

def register(project,arc,folder):
 specs=SHIBUKI if project=='ver_buki_riko'else NANA
 src=Image.open(folder/'generated.png').convert('RGBA');require(src.getchannel('A').getextrema()==(0,255),'Missing generated alpha')
 words=struct.unpack_from('<16H',entry(arc,9),32)
 colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words[1:]],np.int32)
 old=(ROOT/'work/overhaul_20261105/sprites'/project/'baseline/PL02_U.ARC').read_bytes()
 result={};reports=[]
 for i,n in enumerate(MASTERS):
  spec=specs[n];a=layer(arc,0,n);body=np.array(Image.open(folder/f'owned_body_{n}.png'))[:,:,3]>0
  ys,xs=np.nonzero(body);height=int(ys.max()-ys.min()+1)
  cw,ch=src.width//2,src.height//2
  cell=src.crop((i%2*cw,i//2*ch,(i%2+1)*cw,(i//2+1)*ch));data=np.array(cell);data[:,:,3]=np.where(data[:,:,3]>=224,255,0)
  labs,_=label(data[:,:,3]>0,np.ones((3,3),bool));counts=np.bincount(labs.ravel());counts[0]=0;mask=labs==int(counts.argmax());data[~mask,3]=0
  cell=Image.fromarray(data);cell=cell.crop(cell.getbbox());pixels=np.array(cell).astype(np.int32);yy,xx=np.indices(pixels.shape[:2]);r,g,b=pixels[:,:,:3].transpose(2,0,1)
  if project=='ver_buki_riko':eyes=(r>140)&(g>65)&(g<205)&(r>g+25)&(b<125)
  elif n==135:eyes=(r>g+12)&(g>135)&(r>b+30)&(yy>cell.height*.23)
  else:eyes=(g>r+8)&(g>b+8)
  eyes&=(pixels[:,:,3]>0)&(yy<cell.height*.56)&(xx<cell.width*.62)
  ey,ex=np.nonzero(eyes);require(len(ex)>0,'Generated face anchor missing')
  scale=height/cell.height;target=quantize(cell,colors,scale)
  px=round((float(np.median(ex))+.5)*scale-.5);py=round((float(np.median(ey))+.5)*scale-.5)
  dx,dy=spec['eye'][0]-px,spec['eye'][1]-py;h,w=target.shape
  reg=np.zeros_like(a);reg[dy:dy+h,dx:dx+w]=target
  clothing=region_mask(a.shape,spec['region']);protected=region_mask(a.shape,spec['head'])
  for box in spec['hands']:protected|=region_mask(a.shape,box)
  protected[97:]=True
  # Preserve the already approved flowing hair at the right side of the torso.
  yy,xx=np.indices(a.shape)
  hair=[2,3,8,14]if project=='ver_buki_riko'else[5,6,7,8,9]
  protected|=(xx>=85)&(yy<94)&np.isin(a,hair)
  fx=np.zeros_like(a)
  if n in(136,137):
   comp=composition_frame(entry(old,3),0,n);ids=[p['index']for p in comp['parts']if p['tile']==7]
   fx=part_layer(old,n,ids)[80:240,80:336];protected|=fx>0
  overlay=np.where(clothing&~protected,reg,0).astype(np.uint8)
  require(np.count_nonzero(overlay)>35,'Too few jacket pixels')
  require(not np.any(overlay[protected]),'Protected head/hand/foot overwritten')
  result[n]=overlay
  reports.append({'frame':n,'generated_cell':[i%2,i//2],'scale':scale,'registration_offset':[dx,dy],
                  'head_hand_foot_regions':spec,'jacket_pixels':int(np.count_nonzero(overlay)),
                  'base_entirely_preserved':True,'original_spark_mask_preserved':n in(136,137)})
 result[134]=result[133].copy()
 return result,reports

def pack_arrival(arc,targets):
 g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);groups={}
 for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
 replacements,counts,changes={},{},{};reports=[]
 for off,refs in groups.items():
  if not set(refs)&set(targets):continue
  require(set(refs)<=set(targets),'Arrival stream aliases a protected frame')
  f=bank['frames'][refs[0]];raw=decode_stream(g,off,f['limit'],f['tile_count']*128).data
  protected={p['tile']for n in refs for b in(0,6,7,8)for p in composition_frame(c,b,n)['parts']}
  expanded=resize_tile_storage(raw,f['tile_count'],32);pool=set(range(32))-protected
  new,assigned=pack_shared(expanded,32,[targets[n]for n in refs],pool,[12]*len(refs))
  for n,rr in zip(refs,assigned):
   require(bool(rr),'Missing jacket layer');changes[n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rr)
   replacements[n]=new;counts[n]=32
  reports.append({'frames':refs,'preserved_tiles':sorted(protected),'available_tiles':len(pool),'parts':[len(q)for q in assigned]})
 nc,slack=repack_parts(c,5,changes);ng,gproof=repack_variable(g,replacements,counts)
 result=replace_entry(replace_entry(arc,2,ng),3,nc)
 for n in range(237):
  if n in{105,*range(175,183)}:continue
  for b in(0,5,6,7,8):
   expected=targets[n]if b==5 and n in targets else layer(arc,b,n)
   require(np.array_equal(layer(result,b,n),expected),f'Arrival final layer changed {b}:{n}')
 checked=0
 for bi in range(len(bank_offsets(g,allow_aliases=True))):
  for a,b in zip(graphics_bank(g,bi,allow_bank_aliases=True)['frames'],graphics_bank(ng,bi,allow_bank_aliases=True)['frames']):
   if bi==0 and a['index']in targets:continue
   require(decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data==decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data,'Unrelated raw graphics changed');checked+=1
 for bi in range(len(bank_offsets(c))):
  for n in range(composition_frame(c,bi,0)['bank_frame_count']):
   if bi==5 and n in targets:continue
   require(records(c,bi,n)==records(nc,bi,n),'Other part records changed')
 from scripts.discover_inputs import psx_arc
 for e in psx_arc(arc):
  k=int(e['type'],16)
  if k not in(2,3):require(entry(arc,k)==entry(result,k),'Non-graphics resource changed')
 require(len(arc)==len(result),'ARC length changed')
 return result,{'groups':reports,'parts_bank5_slack':slack,'graphics':gproof,'unchanged_graphics_refs':checked,
                'all_base_layers_preserved':True,'all_other_compositions_and_entries_preserved':True}

def prepare(project,out,do_pack=False):
 out=out.resolve();require(out.is_relative_to(WORK)and not out.exists(),'Fresh work output required')
 f,s,expected=SOURCES[project];path=ROOT/'out'/project/f/(s+'.bin');require(digest(path)==expected,'Source differs')
 arc=read_disc(path,('PL02_U.ARC',))[0]['PL02_U.ARC'];folder=WORK/'arrival_v1'/project
 targets,reports=register(project,arc,folder)
 result=None;packing=None
 if do_pack:
  previous=WORK/'prepared_special_v1'/project
  before=(previous/'PL02_U.ARC').read_bytes();meta=json.loads((previous/'proposal.json').read_text('utf8'))
  require(sha(before)==meta['after_sha256'] and meta['baseline_sha256']==expected,'Special source differs')
  result,packing=pack_arrival(before,targets)
 out.mkdir(parents=True);items=[]
 for n,t in sorted(targets.items()):
  Image.fromarray(t).save(out/f'overlay_{n:03}.png')
  a=layer(arc,0,n)
  for name,pic in(('SWIM preserved',image(arc,a,np.zeros_like(a))),('JACKET',image(arc,a,t))):
   canvas=Image.new('RGBA',(384,384));canvas.alpha_composite(pic,(80,80));items.append((str(n)+' '+name,canvas))
  image(arc,a,t).save(out/f'full_{n:03}.png')
 board(items,out/'arrival_review.png',cols=4)
 save_json(out/'registration.json',{'project':project,'source_BIN_sha256':expected,'source_arc_sha256':sha(arc),
             'generated_sha256':digest(folder/'generated.png'),'prompt_sha256':digest(folder/'prompt.txt'),
             'frames':sorted(targets),'masters':reports,'base_pixels_unchanged':True,'tool':'builtin image_gen',
             'registered_only_jacket':True,'runtime_verified':False})
 if result is not None:
  (out/'PL02_U.ARC').write_bytes(result)
  save_json(out/'proposal.json',{'project':project,'baseline':path.relative_to(ROOT).as_posix(),'baseline_sha256':expected,
       'source_arc_sha256':sha(arc),'after_sha256':sha(result),'resource':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),
       'special_preparation':(WORK/'prepared_special_v1'/project/'proposal.json').relative_to(ROOT).as_posix(),
       'special_frames':list(range(217,231)),'arrival_frames':sorted(targets),'arrival_packing':packing,
       'base_arrival_swimsuit_preserved':True,'capsule_banks_preserved':True,'palettes_timing_audio_preserved':True,
       'runtime_verified':False})
 print(out)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--project',choices=SOURCES,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--pack',action='store_true');a=p.parse_args();prepare(a.project,a.output,a.pack)
