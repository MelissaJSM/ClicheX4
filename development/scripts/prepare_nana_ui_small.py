"""전투용 나나 도트를 선택/저장 UI에 원래 크기로 재사용한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ui import actual
from scripts.prepare_rin_ui_small import world,protected_repack
from scripts.discover_inputs import DiscReader,sha256
from scripts.project import digest
from scripts.prepare_nana_idle_shot import PILOT,write
from scripts.extract_zero import save_image
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,place_frame,tile_pixels
from src.sprite_window_fit import fit_windows
PARENT=ROOT/'out/ver_rin_nana/nana_vehicle_hurt_20261030T014147573781Z'
PARENT_SHA='ae3a01b1cafd2d2dc75c7999a76a4ce12f2486d234007410357e64cd80cfabaf'
ARC_SHA='e404c04c2590b567155f9970fee277e1ac4c47b0fa5d637f5180834c7071a4ab'
CONFIG=ROOT/'config/riko_ui_us.json'
SOURCE_HASHES={'COL0E_U1.ARC':'f85770e4c43ce8c920d4a2bb09fed0fb452bae2795b9263e56ef1d581d5f2095','LOAD_U.ARC':'d86e38448dc28ba6d333d08283853cc9adaa2425b2a1001bde811933c38c8a36','ST0E_U1.ARC':'aaf650776da851eb95489b16b3477f9a4bbd4a113475fdd2d9e8531910ac3e10','MOJIPAT.ARC':'990dc54fd2f0bd1bd1dde7c4b796f681dfd6a873d5a70ebcb17e182b7e3f683a'}
MAPPING={0:0,1:85,2:86,3:87,4:88,5:89,6:90,7:91,8:92,18:207,19:156,20:157,21:158,22:159,23:160,24:161}
SHIFT_Y={18:-1,22:-1,23:-1,24:-2}
def read_sources():
 m=json.loads((PARENT/'manifest.json').read_text('utf8'));arc=(PARENT/'modified.arc').read_bytes();cfg=json.loads(CONFIG.read_text('utf8'));game=PARENT/'rin_nana.bin'
 if m['task']!='x_nana'or m['modified_bin']['sha256']!=PARENT_SHA or sha256(arc)!=ARC_SHA or digest(game)!=PARENT_SHA:raise ValueError('Unsupported Nana parent')
 if digest(PILOT/'nana_000_indexed.png')!='97a6d85d422eb25cf405de164d4c9e8709ab726b6fa6cb1b19d148d9f61df3bf'or digest(PILOT/'palette.bin')!='8f281da04b2b3eeaa95582f94a4a5356d1b6fc7977566f62bfce3eab20b2f764':raise ValueError('Accepted Nana style changed')
 originals={};records=[]
 with game.open('rb')as f:
  disc=DiscReader(f,game.stat().st_size);iso={q['path']:q for q in disc.inspect()['files']}
  for rec in cfg['archives']:
   if any(iso[rec['path']][k]!=rec[k]for k in('lba','size')):raise ValueError('UI ISO location changed')
   data=disc.read(rec['lba'],rec['size']);name=rec['path'].split('/')[-1].split(';')[0]
   if sha256(data)!=SOURCE_HASHES[name]:raise ValueError('Parent UI resource changed')
   originals[name]=data;records.append({**rec,'sha256':SOURCE_HASHES[name]})
 return m,arc,records,originals
def target_frame(arc,n):
 px,sz,bb=actual(arc,MAPPING[n]);a=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);dy=SHIFT_Y.get(n,0)
 if n in(19,20):a=a[:,::-1].copy();bb=(-bb[2],bb[1],-bb[0],bb[3])
 return a.tobytes(),sz,(bb[0],bb[1]+dy,bb[2],bb[3]+dy)
def register(parts,bank,targets,texture):
 changed=bytearray(parts);packed={};layouts={}
 for n,fr in targets.items():
  c=composition_frame(parts,bank,n)
  try:place_frame(fr,c,texture);positions=[(p['x'],p['y'])for p in c['parts']]
  except ValueError:
   a=np.frombuffer(fr[0],np.uint8).reshape(fr[1][1],fr[1][0]);dummy=[dict(p,tile=i+1,flip_x=False)for i,p in enumerate(c['parts'])];fit=fit_windows(dummy,a,fr[2][0],fr[2][1])
   if fit is None:raise ValueError(f'Cannot fit native Nana {bank}:{n}')
   by={p['record_offset']:(x,y)for p,x,y in fit};positions=[by[p['record_offset']]for p in c['parts']]
  for p,(x,y)in zip(c['parts'],positions):
   if not -128<=x<=127 or not -128<=y<=127:raise ValueError('UI coordinate overflow')
   changed[p['record_offset']+2:p['record_offset']+4]=bytes((x&255,y&255))
  packed[n]=place_frame(fr,composition_frame(changed,bank,n),texture);layouts[n]=positions
 return bytes(changed),packed,layouts
def verify(originals,edited,arc):
 s,ns=originals['ST0E_U1.ARC'],edited['ST0E_U1.ARC'];t,nt=entry(s,0x10102),entry(ns,0x10102);p,np_=entry(s,10),entry(ns,10);palette=entry(arc,9)[:32]
 if nt[:90112]!=t[:90112]or replace_entry(replace_entry(s,0x10102,nt),10,np_)!=ns:raise ValueError('Rin, portrait or other selection resource changed')
 counts={'selection_targets':0,'selection_other_frames':0,'save_other_frames':0};allowed=set()
 def tile_scope(ot,nt,op,np_,bank,ids):
  owned={q['page']*256+q['tile']for n in ids for q in composition_frame(op,bank,n)['parts']}
  for tid in set(range(len(ot)//128))-owned:
   if tile_pixels(ot,tid)!=tile_pixels(nt,tid):raise ValueError('Unowned UI tile changed')
  for n in ids:
   for q in composition_frame(np_,bank,n)['parts']:
    tid=q['page']*256+q['tile'];px=tile_pixels(nt,tid)
    if(tid%16==0 and any(px[::16]))or(tid%256<16 and any(px[:16])):raise ValueError('Opaque UV0 boundary')
  return len(ot)//128-len(owned)
 counts['selection_unowned_tiles_preserved']=tile_scope(t[90112:],nt[90112:],p,np_,2,MAPPING)
 for bank,lo,hi in((0,0,40960),(1,40960,90112),(2,90112,len(t))):
  for n in range(composition_frame(p,bank,0)['bank_frame_count']):
   a,b=composition_frame(p,bank,n),composition_frame(np_,bank,n)
   if len(a['parts'])!=len(b['parts']):raise ValueError('UI part count changed')
   if bank==2 and n in MAPPING:
    if world(compose_static(nt[lo:hi],local_composition(b)))!=world(target_frame(arc,n)):raise ValueError('Nana selection pixels/anchor differ')
    for x,y in zip(a['parts'],b['parts']):
     if any(x[k]!=y[k]for k in('flip_x','flip_y','clut','unknown_flags','record_offset')):raise ValueError('UI flags or order changed')
     allowed.update(range(x['record_offset'],x['record_offset']+4))
    counts['selection_targets']+=1
   else:
    if a!=b or compose_static(t[lo:hi],local_composition(a))[:3]!=compose_static(nt[lo:hi],local_composition(b))[:3]:raise ValueError('Other selection frame changed')
    counts['selection_other_frames']+=1
 if any(x!=y and i not in allowed for i,(x,y)in enumerate(zip(p,np_))):raise ValueError('Other selection parts/header changed')
 col=originals['COL0E_U1.ARC'];cp=entry(col,5)
 if replace_entry(col,5,cp[:512]+palette+cp[544:])!=edited['COL0E_U1.ARC']:raise ValueError('Other selection palette changed')
 menu,nm=originals['MOJIPAT.ARC'],edited['MOJIPAT.ARC'];tex,ntex=entry(originals['LOAD_U.ARC'],0x10008),entry(edited['LOAD_U.ARC'],0x10008);po=struct.unpack_from('<I',menu,4)[0]
 if po!=6788:raise ValueError('Menu palette offset changed')
 counts['save_unowned_tiles_preserved']=tile_scope(tex,ntex,menu,nm,2,[44]);allowed=set(range(po+8*32,po+9*32))
 for n in range(composition_frame(menu,2,0)['bank_frame_count']):
  a,b=composition_frame(menu,2,n),composition_frame(nm,2,n)
  if n==44:
   if len(a['parts'])!=len(b['parts'])or world(compose_static(ntex,local_composition(b)))!=world(actual(arc,0)):raise ValueError('Save sprite changed size or world anchor')
   for x,y in zip(a['parts'],b['parts']):
    if any(x[k]!=y[k]for k in('flip_x','flip_y','clut','unknown_flags','record_offset')):raise ValueError('Save flags/order changed')
    allowed.update(range(x['record_offset'],x['record_offset']+4))
  else:
   if a!=b or compose_static(tex,local_composition(a))[:3]!=compose_static(ntex,local_composition(b))[:3]:raise ValueError('Other save/armor/Rin frame changed')
   counts['save_other_frames']+=1
 if nm[po+8*32:po+9*32]!=palette or any(x!=y and i not in allowed for i,(x,y)in enumerate(zip(menu,nm))):raise ValueError('Other menu bytes/palette changed')
 if replace_entry(originals['LOAD_U.ARC'],0x10008,ntex)!=edited['LOAD_U.ARC']:raise ValueError('Other load resource changed')
 if any(len(originals[n])!=len(edited[n])for n in originals):raise ValueError('UI resource length changed')
 return {**counts,'native_pixels_exact':True,'clipped_opaque_pixels':0,'art_rescaled':False,'all_gameplay_unchanged':True,'rin_portrait_names_background_preserved':True,'armor_overlay_tiles_and_palettes_preserved':True,'selection_attack_effects_preserved':True,'timing_headers_exact':True,'runtime_verified':False}
def prepare(out):
 out=out.resolve()
 if not out.is_relative_to(ROOT/'work/ver_rin_nana/nana_ui_small')or out.exists():raise ValueError('Fresh isolated Nana UI output required')
 m,arc,records,originals=read_sources();out.mkdir(parents=True);s=originals['ST0E_U1.ARC'];t,p=entry(s,0x10102),entry(s,10)
 if struct.unpack('<3I',entry(s,12))!=(0,40960,90112):raise ValueError('Unknown selection bank layout')
 rp,targets,layout=register(p,2,{n:target_frame(arc,n)for n in MAPPING},t[90112:]);nt,np_,report=protected_repack(t[90112:],p,rp,2,targets);edited={'ST0E_U1.ARC':replace_entry(replace_entry(s,0x10102,t[:90112]+nt),10,np_)}
 palette=entry(arc,9)[:32];words=struct.unpack('<16H',palette);col=originals['COL0E_U1.ARC'];cp=entry(col,5);edited['COL0E_U1.ARC']=replace_entry(col,5,cp[:512]+palette+cp[544:]);menu,load=originals['MOJIPAT.ARC'],originals['LOAD_U.ARC'];tex=entry(load,0x10008);rm,save_targets,_=register(menu,2,{44:actual(arc,0)},tex);ntex,nm,sreport=protected_repack(tex,menu,rm,2,save_targets);po=struct.unpack_from('<I',menu,4)[0];edited['MOJIPAT.ARC']=nm[:po+8*32]+palette+nm[po+9*32:];edited['LOAD_U.ARC']=replace_entry(load,0x10008,ntex);v=verify(originals,edited,arc)
 for name,data in edited.items():(out/name).write_bytes(data)
 board=Image.new('RGB',(800,560),'#222630');dr=ImageDraw.Draw(board)
 for i,n in enumerate(MAPPING):
  px,sz,bb,_=compose_static(nt,local_composition(composition_frame(np_,2,n)));im=save_image(px,sz,words,out/f'select_{n:03d}.png').convert('RGBA');im=im.resize((sz[0]*2,sz[1]*2),Image.Resampling.NEAREST);x,y=i%8*100,i//8*260;board.paste(im,(x+50+bb[0]*2,y+140+bb[1]*2),im);dr.text((x+3,y+5),str(n),fill='white')
 board.save(out/'selection_review.png');px,sz,bb,_=compose_static(ntex,local_composition(composition_frame(edited['MOJIPAT.ARC'],2,44)));save_image(px,sz,words,out/'save_044.png');(out/'palette.bin').write_bytes(palette)
 recipe={'kind':'nana_selection_save_small','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'parent_manifest_sha256':digest(PARENT/'manifest.json'),'config_sha256':digest(CONFIG),'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'mapping':MAPPING,'selection_shift_y':SHIFT_Y,'selection_mirrored':[19,20],'selection_atlas':report,'save_atlas':sreport,'files':[{'source':rec,'file':rec['path'].split('/')[-1].split(';')[0],'sha256':sha256(edited[rec['path'].split('/')[-1].split(';')[0]])}for rec in records],'verification':v};write(out/'recipe.json',recipe);print(json.dumps({'output':str(out),'verification':v,'packing':[report,sreport]}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
