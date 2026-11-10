"""기존 포스183 원화에서 잘못 등록된 옷 영역을 복원한다. 게임 파일은 입력 전용."""
import json,struct,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,TASK,SOURCES,sha,write,need,relative,FONT,read
from scripts.fix_x_idle_return import patch_return_idle,INPUTS
from scripts.prepare_riko_ui import replace_entry
from scripts.prepare_shibuki_armor_motion import identical
from src.psx_player import composition_frame,decode_stream,indexed_atlas,bank_offsets,graphics_bank
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank
D=TASK/'shibuki_ladder_fix'
MASTER=ROOT/'work/ver_buki_riko/shibuki_art/fourth_armor_remaining_v1/layers06/master_183.png'
MASTER_SHA='1ced7b7014491ff9d573b01d056d29b4fd4dc7c49e35e8765de7bad2dda11fc3'

def target_layers(arc):
 b=arc.layer(183)[0][80:240,80:240];reg=np.array(Image.open(MASTER));yy,xx=np.indices(b.shape);cx,neck,hip=81,84,98
 hair=np.isin(b,[5,8,14]);hair|=binary_dilation(hair)&np.isin(b,[2,15]);skin=np.isin(b,[12,13]);headprotect=(yy<neck)&(xx>=cx-11)&(xx<=cx+10)
 garment=(b>0)&~hair&~skin&~headprotect
 coords=np.argwhere((reg>0)&~np.isin(reg,[4,5,6,9]));mapped=np.zeros_like(b)
 for y,x in np.argwhere(garment):
  dist=(coords[:,0]-y)**2*2+(coords[:,1]-x)**2;sy,sx=coords[np.argmin(dist)];mapped[y,x]=reg[sy,sx]
 legs=garment&(yy>=hip);arms=garment&~legs&((xx<cx-5)|(xx>cx+7));body=garment&~legs&~arms
 targets={}
 for bank,mask in((6,body),(7,arms),(8,legs)):
  v=np.zeros((384,384),np.uint8);v[80:240,80:240]=np.where(mask,mapped,0);targets[bank]=v
 return targets

def patch_ladder(data,baseline,*,expected_input_sha):
 need(sha(baseline)==INPUTS['shibuki','PL00_U.ARC'],'지원하지 않는 기준 자원')
 need(sha(data)==expected_input_sha,'입력 자원 해시 불일치')
 registration=json.loads((D/'registration.json').read_text('utf8'));need(sha(MASTER.read_bytes())==registration['master_sha256']==MASTER_SHA,'기존183 원화가 변경됨')
 before=Archive(data);original=Archive(baseline);need(before.p==original.p,'팔레트 불일치')
 for b in(0,5,6,7,8):
  old,om=before.layer(183,b);orig,rm=original.layer(183,b);need(np.array_equal(old,orig) and om['decoded_sha256']==rm['decoded_sha256'],'183이 먼저 변경됨')
 targets=target_layers(before);g,c=before.g,before.c;f=before.banks[0]['frames'][183]
 need([q['index'] for q in before.banks[0]['frames'] if q['offset']==f['offset']]==[183],'183 raw별칭 변경')
 raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=raw;nc=bytearray(c);changed_positions=set()
 protected={p['tile'] for b in(0,5) for p in composition_frame(c,b,183)['parts']};pool={p['tile'] for b in(6,7,8) for p in composition_frame(c,b,183)['parts']};need(not pool&protected,'보호 타일 공유')
 free=set(pool);assignments=[]
 for b in(6,7,8):
  cp=composition_frame(c,b,183);nr,rr=identical(nr,f['tile_count'],targets[b][80:240,80:240],free,len(cp['parts']));used={t for t,x,y in rr};free-=used
  owner_positions={p['record_offset'] for p in cp['parts']}
  for n in range(237):
   if n!=183:need(not owner_positions&{p['record_offset'] for p in composition_frame(c,b,n)['parts']},'183 조립이 다른ref와공유됨')
  for i,p in enumerate(cp['parts']):
   t,x,y=rr[min(i,len(rr)-1)];at=p['record_offset'];nc[at:at+4]=struct.pack('<BBbb',0,t,x-80,y-80);changed_positions.update(range(at,at+4))
  assignments.append({'bank':b,'tiles':sorted(used),'records':rr})
 nc=bytes(nc);need(all(a==b or i in changed_positions for i,(a,b) in enumerate(zip(c,nc))),'비대상 조립 변경')
 code=encode_stream(nr)
 if len(code)<=f['limit']-f['offset']:ng,packing=replace_stream(g,f,nr,allocated_limit=f['limit'])
 else:ng,packing=repack_graphics_bank(g,0,{183:code})
 out=replace_entry(replace_entry(data,2,ng),3,nc);after=Archive(out)
 need(replace_entry(replace_entry(out,2,g),3,c)==data,'비대상entry 변경')
 need(bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True) and bank_offsets(c)==bank_offsets(nc),'bank경계 변경')
 raw_checks=0
 for bank,oldbank in enumerate(before.banks):
  newbank=after.banks[bank]
  for oldf,newf in zip(oldbank['frames'],newbank['frames']):
   need(oldf['tile_count']==newf['tile_count'],'tilecount 변경')
   a=decode_stream(g,oldf['offset'],oldf['limit'],oldf['tile_count']*128).data;b=decode_stream(ng,newf['offset'],newf['limit'],newf['tile_count']*128).data
   need(b==(nr if bank==0 and oldf['index']==183 else a),'비대상raw 변경');raw_checks+=1
 layer_checks=0
 for n in range(237):
  if n in(105,*range(175,183)):continue
  for b in(0,5,6,7,8):
   expected=targets[b] if n==183 and b in targets else before.layer(n,b)[0]
   need(np.array_equal(after.layer(n,b)[0],expected),f'layer회귀{n}/{b}');layer_checks+=1
 atlas=np.frombuffer(indexed_atlas(nr,f['tile_count'])[0],np.uint8).reshape(-1,256);gpu=0
 for b in(6,7,8):
  for p in composition_frame(nc,b,183)['parts']:
   t=p['tile'];patch=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];need(t%16!=0 or not patch[:,0].any(),'새GPU U경계');need(not p['flip_y'] or t//16%16!=0 or not patch[0].any(),'새GPU V경계');gpu+=1
 masks=0
 for arm in(1,2):
  for mask in range(16):
   goal=before.composite(183,0)[0]
   for bit,b in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:goal.alpha_composite(before.rgba(targets.get(b,before.layer(183,b)[0]),32 if b==7 and arm==2 else 16))
   need(after.composite(183,mask,arm)[0].tobytes()==goal.tobytes(),'16mask회귀');masks+=1
 return out,{'input_sha256':sha(data),'output_sha256':sha(out),'master_sha256':sha(MASTER.read_bytes()),'registration':registration,'assignments':assignments,'packing':packing,'raw_checks':raw_checks,'indexed_layer_checks':layer_checks,'mask_checks':masks,'new_gpu_parts_checked':gpu,'base_head_hair_skin_geometry_exact':True,'all_other_refs_palette_and_entries_exact':True,'runtime_verified':False}

def main():
 source,assets,records=read('shibuki');baseline=assets['PL00_U.ARC']
 tone_path=ROOT/'work/sprite_consistency_20261105/coverage/shibuki_special/prepared_v1/PL00_U.ARC';tone=tone_path.read_bytes();tone_sha='f1c3ae2c4f11fec6275abd4e33205abf0ca350f37febcd53a35d6e4136e7c118';need(sha(tone)==tone_sha,'full_detail 입력 변경')
 linked,link_proof=patch_return_idle(tone,baseline,'shibuki','PL00_U.ARC',expected_input_sha=tone_sha)
 out,proof=patch_ladder(linked,baseline,expected_input_sha=sha(linked));folder=D/'combined_v1';need(not folder.exists(),'기존 준비물 덮어쓰기 거부');folder.mkdir()
 path=folder/'PL00_U.ARC';path.write_bytes(out)
 write(folder/'proposal.json',{'project':SOURCES['shibuki'][0],'baseline':relative(source),'baseline_sha256':SOURCES['shibuki'][2],'files':{'PL00_U.ARC':{'before':sha(baseline),'after':sha(out),'size':len(out),'path':relative(path),'record':records['PL00_U.ARC']}},'semantic_order':['full_detail6','142_idle_link','183_clothing_registration'],'tone_source':relative(tone_path),'idle_return':link_proof,'ladder':proof,'runtime_verified':False})
 board=Image.new('RGB',(1120,350),(32,37,49));draw=ImageDraw.Draw(board)
 for i,(a,n,label) in enumerate(((Archive(baseline),183,'183 이전'),(Archive(out),183,'183 옷 복원'),(Archive(out),143,'기존 사다리143'),(Archive(out),0,'기존 대기0'))):
  im=a.composite(n,15)[0];box=(125,120,195,200);bb=im.getbbox();need(bb[0]>=box[0] and bb[1]>=box[1] and bb[2]<=box[2] and bb[3]<=box[3],'비교 잘림');im=im.crop(box).resize((280,320),Image.Resampling.NEAREST);draw.text((i*280+4,4),label,font=FONT,fill='white');board.paste(im,(i*280,28),im)
 board.save(folder/'comparison.png');print(json.dumps({'output':relative(path),'sha256':sha(out),'raw_checks':proof['raw_checks'],'layers':proof['indexed_layer_checks'],'mask':proof['mask_checks']}))

if __name__=='__main__':main()
