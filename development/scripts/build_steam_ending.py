"""Localize native ending maps while preserving each region's creator credits."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_steam_get_boss import find,replace_map,background_texture,digest,sha
from scripts.c01_audio_build import read_disc
from scripts.discover_inputs import DiscReader
from scripts.prepare_riko_ui import entry
from scripts.prepare_korean_ending import extract_screens
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_player import unpack_indices
from src.steam_ui import stage_texture
W=ROOT/'work/steam_port_20261109';D=W/'ending_completion/v2';OUT=ROOT/'out/steam_ending_20261109_v2'
STEAM=Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection')
JP_ROLES={4:['원작 록맨 X4','제작진','제작'],6:['기획','프로그래밍'],8:['캐릭터와 오브젝트 디자인'],10:['배경 디자인','타이틀 디자인'],12:['일러스트','음악'],14:['효과음','성우'],18:['애니메이션 제작진'],36:['도움을 주신 분들'],38:['총괄 제작'],42:['제작 총책임'],44:['플레이해 주셔서 감사합니다']}
# The Japanese ending uses different prose and map positions than the US game.
# This translation follows the original Japanese, including the Iris reference.
JP_NARRATIVE={
26:[(32,0,'…싸움은 끝났다.'),(32,32,'하지만 되살아나는\n과거의 기억이\n린의 마음을 흔든다.'),(32,96,'…이레귤러를 용서할 수 없는\n헌터로서의 자신…'),(32,144,'…아이리스를 쓰러뜨릴\n숙명을 짊어진 진정한 자신…'),(32,208,'서로 완전히 다른\n두 운명…')],
28:[(32,16,'그리고 린의 결단은\n마침내 두 헌터를\n비극으로 이끌 것이다.'),(32,96,'머지않은 미래에…')],
30:[(32,0,'…싸움은 끝났다.'),(32,32,'하지만 나나의 마음에는\n말로 다할 수 없는\n불안이 엄습한다.'),(32,96,'“이레귤러란\n도대체 무엇일까?”'),(32,144,'“…어쩌면 나 자신도\n이레귤러가 되는 건 아닐까?”')],
32:[(32,0,'불길한 예감은 현실이 되어\n두 헌터를\n운명의 싸움으로 이끈다.'),(32,80,'머지않은 미래에…')],
}

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Output collision')
 p.write_bytes(b)
def indexed_screens(a):
 tex=find(a,b'TEX\0','\\dds\\').payload;mp=find(a,b'OMP\0').payload;cell=find(a,b'OCL\0').payload
 if len(mp)!=12+48*512 or struct.unpack_from('<I',mp,8)[0]!=48*256:raise ValueError('Ending screen geometry')
 if len(cell)!=12+struct.unpack_from('<I',cell,8)[0]*4:raise ValueError('Ending cell count')
 pixels=np.frombuffer(tex[20:],np.uint8).reshape(2048,2048);out={}
 for s in range(48):
  px=np.zeros((256,256),np.uint8);rows=np.full((16,16),64,np.uint8)
  for j,v in enumerate(struct.unpack_from('<256H',mp,12+s*512)):
   if not v:continue
   ident=v&16383
   if ident>=(len(cell)-12)//4:raise ValueError('Cell reference outside table')
   value=struct.unpack_from('<I',cell,12+ident*4)[0];tile=value>>16&4095;page,local=divmod(tile,256);x=page%8*256+local%16*16;y=page//8*256+local//16*16
   block=pixels[y:y+16,x:x+16]
   if v&16384:block=block[:,::-1]
   if v&32768:block=block[::-1]
   px[j//16*16:j//16*16+16,j%16*16:j%16*16+16]=block;rows[j//16,j%16]=64+(value>>8&63)
  out[s]=(px,rows)
 return out

def put_text(px,rows,x,y,text,row):
 font=ImageFont.truetype('C:/Windows/Fonts/gulim.ttc',16);baseline=font.getbbox('가')[1]
 for n,line in enumerate(text.split('\n')):
  yy=y//16*16+n*16
  if x%16 or x+16*len(line)>320 or yy+16>256:raise ValueError(('Ending text overflow',text))
  for col,c in enumerate(line):
   if c==' ':continue
   xx=x+col*16;mask=Image.new('1',(16,16));ImageDraw.Draw(mask).text((0,-baseline),c,font=font,fill=1)
   px[yy:yy+16,xx:xx+16][np.array(mask,bool)]=15;rows[yy//16,xx//16]=row

def japanese_targets(original):
 targets={};descriptions=[];protected=0
 for s in sorted(set(JP_ROLES)|set(JP_NARRATIVE)|{38,46}):
  px=np.concatenate([original[s][0],original[s+1][0]],1).copy();rows=np.concatenate([original[s][1],original[s+1][1]],1).copy();before=px.copy();oldrows=rows.copy()
  if s in JP_NARRATIVE:
   px[:]=0;rows[:]=80
   for x,y,t in JP_NARRATIVE[s]:put_text(px,rows,x,y,t,80);descriptions.append({'screen':s,'x':x,'y':y,'text':t,'kind':'japanese_narrative'})
  if s in JP_ROLES:
   palette=np.repeat(np.repeat(rows,16,0),16,1);ys=np.where(((palette==81)&(px>0)).any(1))[0];groups=[]
   for y in ys:
    if not groups or y>groups[-1][-1]+2:groups.append([int(y)])
    else:groups[-1].append(int(y))
   if s==44:groups=[list(ys)]
   if len(groups)!=len(JP_ROLES[s]):raise ValueError(('Native role layout changed',s,groups))
   px[palette==81]=0
   for ys,t in zip(groups,JP_ROLES[s]):put_text(px,rows,32,min(ys),t,81);descriptions.append({'screen':s,'x':32,'y':int(min(ys))//16*16,'text':t,'kind':'role'})
  if s==38:
   # Only the all-staff line: two creator names above it remain untouched.
   px[64:96]=0;put_text(px,rows,32,64,'그리고 캡콤의 모든 제작진',80);descriptions.append({'screen':s,'x':32,'y':64,'text':'그리고 캡콤의 모든 제작진','kind':'all_staff'})
  if s==46:
   px[80:96]=0;put_text(px,rows,64,80,'제공',80);descriptions.append({'screen':s,'x':64,'y':80,'text':'제공','kind':'presented_by'})
  if s not in JP_NARRATIVE:
   oldpalette=np.repeat(np.repeat(oldrows,16,0),16,1);newpalette=np.repeat(np.repeat(rows,16,0),16,1);mask=(before>0)&(oldpalette!=81)
   if s==38:mask[64:96]=False
   if s==46:mask[80:96]&=oldpalette[80:96]!=80
   if np.any(mask&((before!=px)|(oldpalette!=newpalette))):raise ValueError(('Creator name/company logo touched',s))
   protected+=int(mask.sum())
  targets[s]=(px[:,:256],rows[:,:16]);targets[s+1]=(px[:,256:],rows[:,16:])
 return targets,{'localized_blocks':descriptions,'protected_credit_pixels_on_edited_pages':protected}

def patch_screens(a,targets):
 """Append indexed tiles/cells inside native limits, preserving original ones."""
 te=find(a,b'TEX\0','\\dds\\');me=find(a,b'OMP\0');ce=find(a,b'OCL\0');tex=bytearray(te.payload);mp=bytearray(me.payload);cell=bytearray(ce.payload)
 values=list(struct.unpack('<'+'I'*((len(cell)-12)//4),cell[12:]));patterns={};attrs={}
 def tile_data(n):
  page,local=divmod(n,256);x=page%8*256+local%16*16;y=page//8*256+local//16*16
  return b''.join(tex[20+(y+dy)*2048+x:20+(y+dy)*2048+x+16]for dy in range(16))
 for i,v in enumerate(values):
  tile=v>>16&4095;px=tile_data(tile);patterns.setdefault(px,tile);attrs.setdefault((px,64+(v>>8&63)),i)
 next_tile=max(v>>16&4095 for v in values)+1;first_tile=next_tile
 for s,(px,rows) in sorted(targets.items()):
  if not 0<=s<48 or px.shape!=(256,256) or rows.shape!=(16,16) or np.any(px>15) or np.any(rows<64) or np.any(rows>127):raise ValueError('Unsupported ending target')
  for y in range(16):
   for x in range(16):
    block=px[y*16:y*16+16,x*16:x*16+16].tobytes();row=int(rows[y,x]);key=(block,row)
    if not any(block):ident=0
    elif key in attrs and attrs[key]!=0:ident=attrs[key]
    else:
     if block not in patterns:
      tile=next_tile;next_tile+=1
      if tile>=4096 or any(tile_data(tile)):raise ValueError('No verified empty native tile slot')
      page,local=divmod(tile,256);xx=page%8*256+local%16*16;yy=page//8*256+local//16*16
      for dy in range(16):tex[20+(yy+dy)*2048+xx:20+(yy+dy)*2048+xx+16]=block[dy*16:dy*16+16]
      patterns[block]=tile
     ident=len(values)
     if ident>=16384:raise ValueError('Ending OMP index overflow')
     value=patterns[block]<<16|(row-64)<<8;values.append(value);cell.extend(struct.pack('<I',value));attrs[key]=ident
    struct.pack_into('<H',mp,12+s*512+y*32+x*2,ident)
 struct.pack_into('<I',cell,8,len(values))
 return {te.key:bytes(tex),me.key:bytes(mp),ce.key:bytes(cell)}, {'first_added_tile':first_tile,'added_tiles':next_tile-first_tile,'old_cells':(len(ce.payload)-12)//4,'new_cells':len(values),'texture_dimensions_and_size_unchanged':True,'old_tiles_and_cells_preserved':True}

def main():
 D.mkdir(parents=True,exist_ok=True)
 if (W/'ending_v2_builds.json').exists():raise ValueError('Frozen ending v2 build exists')
 if (W/'ending_builds.json').exists():save(W/'ending_v1_builds.json',(W/'ending_builds.json').read_bytes())
 old_hashes={'MegaMan X4.bin':'3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','Rockman X4.bin':'a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1'}
 for n,h in old_hashes.items():
  if digest(ROOT/n)!=h:raise ValueError('Original PS1 source mismatch')
 us,_=read_disc(ROOT/'MegaMan X4.bin',['ST0F_U1.ARC','COL0F_U1.ARC'])
 # Japanese disc also contains /KOR duplicates; choose /ARC explicitly.
 with (ROOT/'Rockman X4.bin').open('rb') as f:
  dr=DiscReader(f,(ROOT/'Rockman X4.bin').stat().st_size);rs={r['path']:r for r in dr.inspect()['files']};r=rs['/ARC/ST0F_01.ARC;1'];jp=dr.read(r['lba'],r['size'])
 baseline={r['relative_path']:r['sha256']for r in json.loads((W/'backup_manifest.json').read_text('utf8'))['originals']};state={r['relative_path']:r['installed_sha256']for r in json.loads((W/'install_state.json').read_text('utf8'))['files']};reports=[]
 for mode,target in [('ver_rin_nana','st0f_01_regwor.arc'),('ver_buki_riko','st0f_01_eng.arc')]:
  ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));path=(ROOT/ptr['cue']).with_suffix('.bin')
  if digest(path)!=ptr['sha256']:raise ValueError('Current PS1 source mismatch')
  ps,_=read_disc(path,['ST0F_U1.ARC','COL0F_U1.ARC']);rel='nativeDX10/X4/romPC/'+target;a=SteamArc((W/'original'/rel).read_bytes(),baseline[rel]);parent=SteamArc((STEAM/rel).read_bytes(),state.get(rel,baseline[rel]));old=jp if mode=='ver_rin_nana' else us['ST0F_U1.ARC'];src=ps['ST0F_U1.ARC'];before=indexed_screens(a)
  # Ending sparkles/PAT and palette are already identical; retain native bytes.
  if find(a,b'PAT\0').payload!=pat_from_ps1(entry(old,10)) or entry(old,10)!=entry(src,10):raise ValueError('Ending actor PAT mismatch')
  if find(a,b'TEX\0','\\chr\\').payload[20:]!=unpack_indices(entry(old,0x10102)) or entry(old,0x10102)!=entry(src,0x10102):raise ValueError('Ending sparkle graphics changed')
  if find(a,b'COL\0').payload[12:]!=entry(ps['COL0F_U1.ARC'],5):raise ValueError('Ending palette differs')
  if mode=='ver_buki_riko':
   te=find(a,b'TEX\0','\\dds\\');updates={te.key:background_texture(te.payload,entry(old,0x10000),entry(src,0x10000))}
   for k,m,unit in [(0,b'OMP\0',2),(1,b'OCL\0',4)]:
    e=find(a,m);updates[e.key]=replace_map(e.payload,entry(old,k),entry(src,k),unit)
   expected=extract_screens(src);proof={'current_ps1_background_copied':True}
  else:
   stage_texture(find(a,b'TEX\0','\\dds\\').payload,entry(jp,0x10000),entry(jp,0x10000))
   if find(a,b'OCL\0').payload[12:]!=entry(jp,1):raise ValueError('JP original cells differ')
   native_map=find(a,b'OMP\0').payload[12:];jpmap=entry(jp,0);delta=[i for i in range(48)if native_map[i*512:i*512+512]!=jpmap[i*512:i*512+512]]
   if delta!=[16,18,19]:raise ValueError('JP native credit corrections changed')
   targets,proof=japanese_targets(before);updates,packing=patch_screens(a,targets);proof.update(packing);proof['native_map_corrections_preserved']=delta;expected={**before,**targets}
  for key in updates:
   if parent.by_key[key].payload!=a.by_key[key].payload:raise ValueError('Existing ending edit requires merge')
  result=parent.rebuild(updates);out=SteamArc(result);out.validate_stream_order();actual=indexed_screens(out)
  for i,(px,rows) in actual.items():
   ex,er=expected[i];mask=np.repeat(np.repeat(rows,16,0),16,1);em=np.repeat(np.repeat(er,16,0),16,1)
   if not np.array_equal(px,ex) or np.any((px!=0)&(mask!=em)):raise ValueError(('Ending screen mismatch',target,i))
   Image.fromarray(ex).save(D/(mode+f'_expected_indices_{i:02}.png'));Image.fromarray(er).save(D/(mode+f'_expected_rows_{i:02}.png'))
  for e in parent.entries:
   if out.by_key[e.key].payload!=updates.get(e.key,e.payload):raise ValueError('Unrelated ending entry changed')
  save(OUT/rel,result);write(D/(mode+'_translation.json'),proof)
  reports.append({'mode':mode,'target_arc':target,'relative_path':rel,'output':(OUT/rel).relative_to(ROOT).as_posix(),'output_sha256':sha(result),'parent_sha256':sha(parent.raw),'original_sha256':sha(a.raw),'source_bin_sha256':ptr['sha256'],'changed_entries':[{'name':a.by_key[k].name,'magic':a.by_key[k].payload[:4].decode('ascii'),'sha256':sha(v)}for k,v in updates.items() if v!=a.by_key[k].payload],'source_stage':'ST0F_U1.ARC','source_palette':'COL0F_U1.ARC','japanese_layout_preserved':mode=='ver_rin_nana','native_animation_and_creator_credits_preserved':True,'install_eligible':True,'runtime_verified':False})
 write(W/'ending_v2_builds.json',reports);write(W/'ending_builds.json',reports);print([{'target_arc':r['target_arc'],'changes':len(r['changed_entries']),'sha256':r['output_sha256']}for r in reports])
if __name__=='__main__':main()
