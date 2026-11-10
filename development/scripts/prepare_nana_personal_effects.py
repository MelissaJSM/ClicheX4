"""수용 나나 머리를 잔기에 재사용하고 X 전용 잔상·사망 색상을 변경한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import all_compositions,composed,render_pixels,require
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
from src.psx_static_effect import patch_static
from src.psx_ui_atlas import local_composition,tile_pixels,write_tile
from src.psx_personal_effects import trail_palette

PARENT=ROOT/'out/ver_rin_nana/nana_hud_theme_20261030T044031308363Z'
PARENT_SHA='d966208b6698209c125ebaf34fbb32d7c70d7e0b1bb2bd441a23e6e2dffe2a49'
ART=ROOT/'work/ver_rin_nana/nana_personal_effects_v1'
STATIC={1,2,3,4,*range(9,22)}
BUBBLES={513,514,515}
DEATH_LUT=bytes((0,9,8,7,6,13,9,8,7,6,5,8,7,6,5,5))
BUBBLE_LUT=bytes((0,1,5,3,6,7,8,9,13,9,10,11,13,9,8,7))

def sources():
 require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Accepted parent differs')
 m=json.loads((PARENT/'manifest.json').read_text('utf8'));raw={};records={}
 with (PARENT/'rin_nana.bin').open('rb') as f:
  d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size)
  for r in d.inspect()['files']:
   n=r['path'].split('/')[-1].split(';')[0]
   if n in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','SLUS_005.61') or (n.startswith('COL') and n.endswith('X.ARC') and n[3:5] not in ('0D','0E','0F')):
    a=d.read(r['lba'],r['size']);raw[n]=a;records[n]={**r,'sha256':sha256(a)}
 require(len(raw)==28,'Unexpected X stage/resource count')
 require(raw['PL00_U.ARC']==(PARENT/'modified.arc').read_bytes() and raw['PL02_U.ARC']==(PARENT/'PL02_U.ARC').read_bytes(),'Parent ARC readback differs')
 require(raw['SLUS_005.61'][0xbb67c:0xbb680]==bytes.fromhex('02780224'),'Death base CLUT is not 0x7802')
 return m,records,raw

def preserve_rin_death(raw):
 # Same bounded CLUT correction as the accepted Shibuki/Riko release:
 # EXE base 0x7802 -> 0x7800; Rin offset1 -> 3 keeps final 0x7803.
 parts=entry(raw,3);np_=bytearray(parts);comps=all_compositions(parts);selected={(1,n)for n in range(105,114)};allowed=set()
 for k in selected:
  for p in comps[k]['parts']:
   require(p['clut']==1,'Rin death CLUT differs from expected preserved 0x7803')
   o=p['record_offset'];np_[o]=(p['flags']&~12)|12;allowed.add(o)
 nc=all_compositions(bytes(np_))
 for k,c in comps.items():
  if k not in selected:require(c==nc[k],'Rin compensation aliases another frame')
  else:
   for p,q in zip(c['parts'],nc[k]['parts']):require(p['clut']+2==q['clut'] and {a:b for a,b in p.items()if a not in ('clut','flags')}=={a:b for a,b in q.items()if a not in ('clut','flags')},'Rin geometry/CLUT changed')
 require(all(a==b or i in allowed for i,(a,b)in enumerate(zip(parts,np_))),'Rin correction escaped CLUT flags')
 result=replace_entry(raw,3,bytes(np_));return result,{'clut_before':'0x7802+1','clut_after':'0x7800+3','final_clut':'0x7803','records':len(allowed),'all_texture_palette_geometry_exact':True,'other_compositions_exact':True}

def head_from_accepted(arc):
 g=entry(arc,2);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][184]
 raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 px,size,bb,_=compose_launch(raw,f['tile_count'],composition_frame(entry(arc,3),0,184))
 require(size==(16,16),'Accepted ride head is not 16x16')
 return np.frombuffer(px,np.uint8).reshape(16,16).copy()

def clone_effect(raw,selected,lut,only_tiles=None):
 require(len(lut)==16 and lut[0]==0 and all(0<v<16 for v in lut[1:]),'Invalid effect LUT')
 tex,parts=entry(raw,0x10206),entry(raw,3);comps=all_compositions(parts)
 used={p['page']*256+p['tile']for c in comps.values()for p in c['parts']}
 target={p['page']*256+p['tile']for k in selected for p in comps[k]['parts']}
 if only_tiles is not None:target&=only_tiles
 free=iter(sorted(set(range(len(tex)//128))-used));nt=bytearray(tex);np_=bytearray(parts);mapping={};expected=bytearray(tex);allowed=set()
 for old in sorted(target):
  new=next(free,None);require(new is not None,'No private effect slots');mapping[old]=new
  px=bytes(lut[v]for v in tile_pixels(tex,old));write_tile(nt,new,px);write_tile(expected,old,px)
 for k in selected:
  for p in comps[k]['parts']:
   old=p['page']*256+p['tile']
   if old in mapping:
    n=mapping[old];o=p['record_offset'];np_[o:o+2]=bytes(((p['flags']&~3)|n//256,n%256));allowed.update((o,o+1))
 nc=all_compositions(bytes(np_));checked=0
 for k,c in comps.items():
  if k not in selected:require(nc[k]==c,'Effect UV alias escaped targets')
  if k[0] in STATIC:
   a,sz,bb,_=composed(expected if k in selected else tex,c);b,ns,nb,_=composed(nt,nc[k]);require(sz==ns and bb==nb and np.array_equal(a,b),'Effect changed unrelated display');checked+=1
 require(all(a==b or i in allowed for i,(a,b)in enumerate(zip(parts,np_))),'Effect changed geometry/CLUT')
 require(all(tile_pixels(tex,t)==tile_pixels(nt,t)for t in range(len(tex)//128)if t not in mapping.values()),'Shared original tile changed')
 result=replace_entry(replace_entry(raw,3,bytes(np_)),0x10206,bytes(nt))
 return result,{'selected':sorted(selected),'private_tile_mapping':mapping,'static_compositions_checked':checked,'all_other_parts_exact':True,'original_shared_tiles_exact':True,'geometry_alpha_clut_timing_preserved':True,'lut':list(lut)}

def player(raw,head):
 require(head.shape==(16,16)and head.dtype==np.uint8 and head.max()<=15,'Invalid head')
 tex,parts=entry(raw,0x10206),entry(raw,3);comps=all_compositions(parts);cps={};targets={};details=[]
 for n in range(89,99):
  c=comps[3,n];ps=[p for p in c['parts']if p['page']*256+p['tile'] not in BUBBLES]
  require(all(p['clut']==0 for p in c['parts']),'Unexpected pickup CLUT')
  if not ps:continue
  cp=local_composition({**c,'parts':ps});a,sz,bb,cov=composed(tex,cp)
  side=16 if n in (89,96,97,98)else 14 if n<=92 else 10 if n==93 else 6
  tiny=np.array(Image.fromarray(head).resize((side,side),Image.Resampling.NEAREST));new=np.zeros_like(a);x=max(0,min(sz[0]-side,-side//2-bb[0]));y=max(0,min(sz[1]-side,-side//2-bb[1]));new[y:y+side,x:x+side]=tiny
  coverage=np.array([bool(v)for v in cov]).reshape(new.shape)
  if np.any((new>0)&~coverage):
   candidates=[]
   for dy in range(max(0,y-2),min(sz[1]-side,y+2)+1):
    for dx in range(max(0,x-2),min(sz[0]-side,x+2)+1):
     v=np.zeros_like(a);v[dy:dy+side,dx:dx+side]=tiny
     if not np.any((v>0)&~coverage):candidates.append(((dx-x)**2+(dy-y)**2,dx,dy,v))
   require(bool(candidates),f'Head outside native coverage frame {n}: {sz}, {bb}, {x}, {y}')
   _,x,y,new=min(candidates,key=lambda q:q[:3])
  cps[n]=cp;targets[n]=(new.tobytes(),sz);details.append({'frame':n,'size':[side,side],'origin':[bb[0]+x,bb[1]+y]})
 require(set(cps)=={89,90,91,92,93,94,96,97,98},'Pickup scope differs')
 nt=patch_static(tex,cps,targets);changed={t for t in range(len(tex)//128)if tile_pixels(tex,t)!=tile_pixels(nt,t)}
 for k,c in comps.items():
  if k[0]==3 and k[1]in cps:
   a,sz,_,_=composed(nt,cps[k[1]]);require((a.tobytes(),sz)==targets[k[1]],'Head roundtrip differs')
  else:require(not changed&{p['page']*256+p['tile']for p in c['parts']},'Head tile used by another frame')
 result=replace_entry(raw,0x10206,nt)
 result,bubble=clone_effect(result,{(3,n)for n in range(89,99)},BUBBLE_LUT,BUBBLES)
 result,death=clone_effect(result,{(1,n)for n in range(105,114)},DEATH_LUT)
 for e in psx_arc(raw):
  if e['type']not in ('0x3','0x10206'):require(entry(raw,int(e['type'],16))==entry(result,int(e['type'],16)),'Other player entry changed')
 require(len(result)==len(raw),'Player ARC resized')
 return result,{'heads':details,'head_tiles':sorted(changed),'bubble':bubble,'death':death,'all_compressed_body_warp_armor_exact':True,'all_player_palettes_menu_text_exact':True}

def prepare(out):
 out=out.resolve();require(out.is_relative_to(ART)and out!=ART and not out.exists(),'Fresh isolated preparation required')
 m,recs,old=sources();head=head_from_accepted(old['PL00_U.ARC']);pal=entry(old['PL00_U.ARC'],9)[:32]
 inv=json.loads((ART/'inventory.json').read_text('utf8'));require(inv['parent_sha256']==PARENT_SHA,'Audit parent differs')
 require(sha256(head.tobytes())==sha256(np.array(Image.open(ART/'accepted_head_indices.png')).tobytes()),'Audited accepted head differs')
 stage=entry(old['COL00_0X.ARC'],5);deathpal=pal;trail=trail_palette(pal,reference_index=8);files={};checks={};stages=[]
 for n in ('PL00_U.ARC','PL02_U.ARC'):files[n],checks[n]=player(old[n],head)
 files['PL01_U.ARC'],checks['rin_death_compensation']=preserve_rin_death(old['PL01_U.ARC'])
 exe=old['SLUS_005.61'];files['SLUS_005.61']=exe[:0xbb67c]+bytes([0])+exe[0xbb67d:];require([i for i,(a,b)in enumerate(zip(exe,files['SLUS_005.61']))if a!=b]==[0xbb67c],'EXE scope differs')
 for n,a in old.items():
  if not n.startswith('COL'):continue
  p=entry(a,5);require(p[64:96]==stage[64:96],'Original effect colors differ between stages');require(p[352:384]==stage[352:384]and p[416:512]==stage[416:512],'Unexpected X life/trail colors')
  np_=p[:352]+pal+p[384:416]+trail+p[512:];files[n]=replace_entry(a,5,np_)
  e=next(q for q in psx_arc(a)if q['type']=='0x5');allowed=set(range(e['offset']+352,e['offset']+384))|set(range(e['offset']+416,e['offset']+512));require(len(a)==len(files[n])and all(x==y or i in allowed for i,(x,y)in enumerate(zip(a,files[n]))),'Stage edit escaped life/trail rows');stages.append(n)
 require(len(stages)==24,'Stage palette count differs');out.mkdir()
 for n,a in files.items():(out/n).write_bytes(a)
 (out/'life_palette.bin').write_bytes(pal);(out/'death_palette.bin').write_bytes(deathpal);(out/'trail_palette.bin').write_bytes(trail);Image.fromarray(head).save(out/'head_indices.png');render_pixels(head,pal).save(out/'native_head.png')
 board=Image.new('RGB',(720,360),'#242633');draw=ImageDraw.Draw(board);a=files['PL00_U.ARC'];comps=all_compositions(entry(a,3))
 for i,(bank,n,p)in enumerate([(3,n,pal)for n in range(89,99)]+[(1,n,deathpal)for n in range(105,114)]):
  v,sz,bb,_=composed(entry(a,0x10206),comps[bank,n]);im=render_pixels(v,p);im.save(out/f'frame_{bank}_{n}.png');x,y=i%7*100,i//7*115;pic=im.resize((sz[0]*3,sz[1]*3),Image.Resampling.NEAREST);board.paste(pic,(x,y+22),pic);draw.text((x+2,y+3),f'{bank}/{n}',fill='white')
 board.save(out/'effects_review.png')
 r={'kind':'nana_personal_effects','parent_sha256':PARENT_SHA,'parent_manifest_sha256':digest(PARENT/'manifest.json'),'files':[{'file':n,'source':recs[n],'sha256':sha256(a)}for n,a in sorted(files.items())],'head_source':{'frame':184,'size':[16,16],'sha256':sha256(head.tobytes()),'palette_sha256':sha256(pal)},'checks':checks,'stages':stages,'actual_life_clut':'0x780B','actual_death_clut':'0x7800','afterimage_cluts':['0x780D','0x780E','0x780F'],'known_life_palette_shared_users':['EX life tank type18','pickup visual at US0x800CA540'],'exe_change':{'file_offset':0xbb67c,'before':'02780224','after':'00780224','scope':'one-byte death CLUT constant; same method as accepted Shibuki/Riko','all_other_exe_bytes_exact':True},'projectiles_charge_effects_exact':True,'runtime_verified':False}
 (out/'recipe.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'archives':len(files),'head':r['head_source'],'static_checks':checks}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
