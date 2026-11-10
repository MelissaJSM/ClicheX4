"""나나 선택 그림을 기존 UI 은행 안에 등록한다. 다른79그림의 표시 보존."""
import argparse,json,random,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from scripts.extract_zero import save_image
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,repack_frames,tile_pixels
PARENT=ROOT/'out/ver_rin_nana/nana_ui_small_20261030T015636110862Z'
PARENT_SHA='46e43fc433a1eb4bff9d9f43c151725b496313801019df18f80d3d091d794326'
ART=ROOT/'work/ver_rin_nana/illustrations/nana_selection_v1'
GENERATED_SHA='24bd4783b8e1bea2a679e3f2f3b0da2b732d804ed4a8219fe16851f8b16bd5cb'
# Indices1/2 are also used by a name frame. Preserve their exact PS1 words.
RGB=[(41,33,49),(255,255,255),(22,37,82),(55,52,64),(110,106,119),
     (218,157,131),(104,23,59),(232,84,130),(181,42,88),(255,139,172),
     (251,227,204),(95,192,211),(171,165,180),(137,191,55),(45,91,28)]

def sources():
 m=json.loads((PARENT/'manifest.json').read_text('utf8'))
 if m['task']!='x_nana'or m['modified_bin']['sha256']!=PARENT_SHA or digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Nana UI parent changed')
 cfg=json.loads((ROOT/'config/riko_ui_us.json').read_text('utf8'));original={};records=[]
 with(PARENT/'rin_nana.bin').open('rb')as f:
  d=DiscReader(f,m['modified_bin']['size']);iso={q['path']:q for q in d.inspect()['files']}
  for r in cfg['archives']:
   name=r['path'].split('/')[-1].split(';')[0]
   if name not in('ST0E_U1.ARC','COL0E_U1.ARC'):continue
   if any(iso[r['path']][k]!=r[k]for k in('lba','size')):raise ValueError('UI ISO layout changed')
   data=d.read(r['lba'],r['size'])
   if data!=(PARENT/'ui'/name).read_bytes():raise ValueError('Frozen UI resource mismatch')
   records.append({**r,'sha256':sha256(data)});original[name]=data
 return m,records,original

def locate(body,raw):
 return next((i for i in range(0,len(body)-len(raw)+1,4)if body[i:i+len(raw)]==raw),None)

def compact_bank(records):
 # First frame must start at the header count: the engine derives count from it.
 # Other records may reuse identical aligned subsequences, retaining draw order.
 first=records[0];chunks=[q for i,q in enumerate(records)if q not in records[:i]]
 chunks=[q for q in chunks if q==first or not any(q!=p and locate(p,q)is not None for p in chunks)]
 best=None
 for seed in range(40):
  rng=random.Random(seed);items=chunks.copy()
  while True:
   candidates=[];greatest=0
   for i,a in enumerate(items):
    for j,b in enumerate(items):
     if i==j or locate(b,first)==0:continue
     k=next((n for n in range(min(len(a),len(b)),0,-4)if a[-n:]==b[:n]),0)
     if k>greatest:candidates=[];greatest=k
     if k and k==greatest:candidates.append((i,j,k))
   if not candidates:break
   i,j,k=rng.choice(candidates);merged=items[i]+items[j][k:];items=[v for n,v in enumerate(items)if n not in(i,j)]+[merged]
  head=next(q for q in items if locate(q,first)==0);body=head+b''.join(q for q in items if q is not head)
  if best is None or len(body)<len(best):best=body
 if not best.startswith(first)or any(locate(best,q)is None for q in records):raise ValueError('Invalid lossless record compaction')
 count=len(records);headers=[(len(q)//4)|((count+locate(best,q)//4)<<16)for q in records]
 return struct.pack('<'+'I'*count,*headers)+best

def layout(parts,positions,texture):
 blocks=[]
 for bank in range(3):
  records=[]
  for n in range(composition_frame(parts,bank,0)['bank_frame_count']):
   c=composition_frame(parts,bank,n)
   if(bank,n)==(1,0):raw=b''.join(struct.pack('<BBbb',0,254,x-96,y-80)for x,y in positions)
   else:
    kept=[q for q in c['parts']if (bank,n)!=(1,1)or any(tile_pixels(texture,q['page']*256+q['tile']))]
    raw=b''.join(parts[q['record_offset']:q['record_offset']+4]for q in kept)
   records.append(raw)
  blocks.append(compact_bank(records))
 out=bytearray(12)
 for b,block in enumerate(blocks):struct.pack_into('<I',out,b*4,len(out));out+=block
 if len(out)>len(parts):raise ValueError(f'Portrait parts need {len(out)} bytes, capacity {len(parts)}')
 slack=len(parts)-len(out);out+=bytes(slack)
 return bytes(out),{'bytes':len(parts),'free_bytes':slack,'portrait_parts':len(positions),'bank_bytes':[len(q)for q in blocks],'lossless_record_sharing':True,'rin_empty_windows_removed':12}

def verify(original,new,indices,palette):
 if set(new)!=set(original)or any(len(new[n])!=len(original[n])for n in original):raise ValueError('Portrait resource scope or length changed')
 s,ns=original['ST0E_U1.ARC'],new['ST0E_U1.ARC'];t,nt=entry(s,0x10102),entry(ns,0x10102);p,np_=entry(s,10),entry(ns,10)
 if len(p)!=len(np_)or t[:40960]!=nt[:40960]or t[90112:]!=nt[90112:]or replace_entry(replace_entry(s,0x10102,nt),10,np_)!=ns:raise ValueError('Other selection resources changed')
 count=0
 for bank,lo,hi in((0,0,40960),(1,40960,90112),(2,90112,len(t))):
  for n in range(composition_frame(p,bank,0)['bank_frame_count']):
   a,b=composition_frame(p,bank,n),composition_frame(np_,bank,n)
   if a['bank_frame_count']!=b['bank_frame_count']:raise ValueError('UI frame count changed')
   if(bank,n)==(1,0):
    if any(q['clut']or q['flip_x']or q['flip_y']or q['unknown_flags']for q in b['parts']):raise ValueError('Unexpected portrait flags')
    if compose_static(nt[lo:hi],local_composition(b))[:3]!=(indices,(192,160),(-96,-80,96,80)):raise ValueError('Portrait pixel/anchor readback differs')
   else:
    clean=lambda c:[{k:v for k,v in q.items()if k!='record_offset'}for q in c['parts']]
    wanted=clean(a)
    if(bank,n)==(1,1):
     wanted=[q for q in wanted if any(tile_pixels(t[lo:hi],q['page']*256+q['tile']))]
     if len(a['parts'])-len(wanted)!=12:raise ValueError('Rin empty-window layout differs')
     for i,q in enumerate(wanted):q['index']=i
    if wanted!=clean(b)or compose_static(t[lo:hi],local_composition(a))[:3]!=compose_static(nt[lo:hi],local_composition(b))[:3]:raise ValueError('Rin/name/other UI frame changed')
    count+=1
 protected={q['page']*256+q['tile']for n in range(composition_frame(p,1,0)['bank_frame_count'])if n!=0 for q in composition_frame(p,1,n)['parts']}
 for tid in protected:
  if tile_pixels(t[40960:90112],tid)!=tile_pixels(nt[40960:90112],tid):raise ValueError('Other portrait tile changed')
 col=original['COL0E_U1.ARC'];cp=entry(col,5)
 if len(palette)!=32 or replace_entry(col,5,cp[:128]+palette+cp[160:])!=new['COL0E_U1.ARC']:raise ValueError('Other UI palette changed')
 if palette[2:6]!=cp[130:134]:raise ValueError('Shared name colours changed')
 def rgba(texture,comp,cols):
  _,size,bounds,_=compose_static(texture,local_composition(comp));a=np.zeros((size[1],size[0],4),np.uint8)
  for q in comp['parts']:
   pixels=np.frombuffer(tile_pixels(texture,q['page']*256+q['tile']),np.uint8).reshape(16,16)
   if q['flip_x']:pixels=pixels[:,::-1]
   if q['flip_y']:pixels=pixels[::-1]
   w=struct.unpack_from('<16H',cols,(4+q['clut'])*32);rgb=np.array([[(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31,255 if i else 0]for i,v in enumerate(w)],np.uint8);patch=rgb[pixels];x,y=q['x']-bounds[0],q['y']-bounds[1];dest=a[y:y+16,x:x+16];dest[pixels!=0]=patch[pixels!=0]
  return a.tobytes()
 for n in range(1,14):
  if n in(8,11):continue # X's two outer-frame states intentionally use Nana colours.
  if rgba(t[40960:90112],composition_frame(p,1,n),cp)!=rgba(nt[40960:90112],composition_frame(np_,1,n),entry(new['COL0E_U1.ARC'],5)):raise ValueError('Other UI rendered colours changed')
 return {'other_select_index_frames_preserved':count,'other_frame_tiles_preserved':len(protected),'other_visible_coordinates_flags_palette_order_exact':True,'rin_empty_windows_removed':12,'rin_opaque_pixels_bounds_exact':True,'name_and_other_portrait_rgba_frames_preserved':11,'personal_border_palette_frames':[8,11],'native_size':[192,160],'native_bounds':[-96,-80,96,80],'frame_count_timing_unchanged':True,'portrait_parts':len(composition_frame(np_,1,0)['parts']),'palette_row':4,'runtime_verified':False}

def prepare(out):
 out=out.resolve()
 if not out.is_relative_to(ART)or out.exists():raise ValueError('Fresh Nana art output required')
 source=ART/'generated_v2.png'
 if digest(source)!=GENERATED_SHA:raise ValueError('Nana generated art changed')
 m,records,original=sources();im=Image.open(source).convert('RGBA');box=im.getchannel('A').getbbox();im=im.crop(box);scale=max(192/im.width,160/im.height);dims=(round(im.width*scale),round(im.height*scale));im=im.convert('RGBa').resize(dims,Image.Resampling.LANCZOS).convert('RGBA');x,y=(im.width-192)//2,(im.height-160)//2;im=im.crop((x,y,x+192,y+160));a=np.array(im);mask=a[:,:,3]>=128
 words=[0]+[0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10)for r,g,b in RGB];pal=struct.pack('<16H',*words);actual=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31]for w in words[1:]],np.int32);dist=((a[:,:,:3].astype(np.int32)[:,:,None,:]-actual)**2).sum(3);ix=np.where(mask,dist.argmin(2)+1,0).astype(np.uint8);indices=ix.tobytes()
 positions=[(x,y)for y in range(0,160,16)for x in range(0,192,16)if np.any(ix[y:y+16,x:x+16])]
 s=original['ST0E_U1.ARC'];t=entry(s,0x10102);p=entry(s,10);np_,grid=layout(p,positions,t[40960:90112]);reserved={q['page']*256+q['tile']for n in range(composition_frame(p,1,0)['bank_frame_count'])if n!=0 for q in composition_frame(p,1,n)['parts']};nt,np_,packing=repack_frames(t[40960:90112],np_,1,{0:(indices,(192,160))},reserved_tiles=reserved);col=original['COL0E_U1.ARC'];cp=entry(col,5)
 new={'ST0E_U1.ARC':replace_entry(replace_entry(s,0x10102,t[:40960]+nt+t[90112:]),10,np_),'COL0E_U1.ARC':replace_entry(col,5,cp[:128]+pal+cp[160:])};v=verify(original,new,indices,pal)
 out.mkdir()
 for n,data in new.items():(out/n).write_bytes(data)
 pic=save_image(indices,(192,160),words,out/'portrait.png');pic.resize((768,640),Image.Resampling.NEAREST).save(out/'portrait_4x.png');(out/'indices.bin').write_bytes(indices);(out/'palette.bin').write_bytes(pal)
 recipe={'kind':'nana_selection_portrait','parent_sha256':PARENT_SHA,'parent_manifest_sha256':digest(PARENT/'manifest.json'),'generated_source':source.relative_to(ROOT).as_posix(),'generated_sha256':GENERATED_SHA,'prompt':(ART/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':digest(ART/'prompt.txt'),'tool':'built-in image_gen','size':[192,160],'bounds':[-96,-80,96,80],'uniform_scale':scale,'source_alpha_bbox':box,'transparent_index':0,'opaque_colors':len(set(indices)-{0}),'faces_right':True,'palette_rgb':RGB,'parts_layout':grid,'packing':packing,'verification':v,'files':[{'source':q,'file':q['path'].split('/')[-1].split(';')[0],'sha256':sha256(new[q['path'].split('/')[-1].split(';')[0]])}for q in records]}
 recipe.update(correction_prompt=(ART/'opacity_prompt.txt').relative_to(ROOT).as_posix(),correction_prompt_sha256=digest(ART/'opacity_prompt.txt'))
 (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'verification':v,'grid':grid,'packing':packing}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
