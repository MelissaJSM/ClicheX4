"""원US/현재 Shibuki 특수 그림과 호출 바이트 읽기. 제작 함수 호출 없음."""
from pathlib import Path
import hashlib,json,re,struct,sys
import numpy as np
from PIL import Image,ImageDraw
sys.path.append(str(Path.home()/'AppData/Local/Programs/Python/Python313/Lib/site-packages'))
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;H=B/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,render,tile
O=D/'shibuki_standing_special_relations01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
tracked={}
def load(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
def box(z):
 y,x=np.nonzero(z);return [int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)] if len(x) else None
def shift(z,dx):
 v=np.zeros_like(z);y,x=np.nonzero(z);v[y,x+dx]=z[y,x];return v
assets,_=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC','PL02_U.ARC','SLUS_005.61'))
exe=assets['SLUS_005.61'];base=struct.unpack_from('<I',exe,24)[0]
at=lambda addr,n:exe[addr-base+2048:addr-base+2048+n]
ps=[('current_PL00',H/'prepared_hurt_base01/PL00_U.ARC','87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b'),('current_PL02',H/'prepared_ultimate_return01/PL02_U.ARC','f40f33969d488af9db8c7d99b6bf4a78ad6e5542883bff63116fa26778de4cdc')]
ars={f'original_{n[:4]}':Archive(b) for n,b in assets.items() if n.endswith('.ARC')}
for name,p,h in ps:
 b=load(p);assert sha(b)==h;ars[name]=Archive(b)
PBS=(0,5,6,7,8);REFS=(88,89,95,96,97);rows=[];relations=[]
for name,a in ars.items():
 for n in REFS:
  f=a.banks[0]['frames'][n];layers={}
  for pb in PBS:
   pp=parts(a,pb,n);slots={p['record_offset'] for p in pp}
   layers[str(pb)]={'opaque':int(np.count_nonzero(a.layer(n,pb)[0])),'parts':pp,'record_owners':[m for m in range(237) if m!=n and slots & {p['record_offset'] for p in parts(a,pb,m)}]}
  rows.append({'archive':name,'ref':n,'stream_offset':f['offset'],'tile_count':f['tile_count'],'raw_sha256':sha(raw(a,0,n)),'raw_owners':[g['index']for g in a.banks[0]['frames']if g['offset']==f['offset']],'layers':layers})
 for s,t,dx in ((89,88,-1),(95,96,1)):
  rr={'archive':name,'source':s,'target':t,'dx':dx,'layers':[]}
  for pb in PBS:
   a0=shift(a.layer(s,pb)[0],dx);a1=a.layer(t,pb)[0];mask=a0!=a1
   pp=parts(a,pb,s);qq=parts(a,pb,t)
   ss=[(p['flags'],p['tile'],p['x']+dx,p['y'])for p in pp]
   used=[];extra=[]
   for i,p in enumerate(qq):
    sg=sig(p)
    if sg in ss:used.append(ss.index(sg));ss[ss.index(sg)]=None
    else:extra.append((i,p))
   ex=render(a,t,pb,[p for i,p in extra]);mixed=np.where(ex,ex,a0)
   rr['layers'].append({'bank':pb,'changed_pixels':int(mask.sum()),'changed_bbox':box(mask),'target_delta_values':{str(v):int(np.count_nonzero(a1[mask]==v))for v in np.unique(a1[mask])},'body_parts_all_matched':len(used)==len(pp),'extra_parts':[{'index':i,'part':p}for i,p in extra],'extra_render_opaque':int(np.count_nonzero(ex)),'extra_render_values':sorted(map(int,np.unique(ex[ex>0]))),'shift_then_extra_exact':bool(np.array_equal(mixed,a1)),'body_overlap_extra_pixels':int(np.count_nonzero((a0>0)&(ex>0))),'whole_extra_tiles':[{ 'tile':k,'sha256':sha(tile(a,t,k).tobytes())}for k in sorted({p['tile']for i,p in extra})]})
  rr['complete_RGBA_differences']=[]
  for mask in range(16):
   for arm in (1,2):
    x=np.asarray(a.composite(s,mask,arm)[0]);y=np.asarray(a.composite(t,mask,arm)[0]);z=np.roll(x,dx,axis=1)
    rr['complete_RGBA_differences'].append({'mask':mask,'arm':arm,'changed':int(np.any(z!=y,axis=2).sum())})
  relations.append(rr)
tablep=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json';tab=json.loads(load(tablep));linked=[]
for q in tab['animations']:
 if any(s['frame'] in REFS for s in q['steps']):
  assert struct.unpack('<I',at(0x80119DF0+q['id']*4,4))[0]==int(q['address'],16)
  for s in q['steps']:assert at(int(s['address'],16),4).hex()==s['bytes']
  linked.append(q)
syms={n:int(a,16)for n,a in re.findall(r'^(\w+) = (0x[0-9a-fA-F]+);',load(ROOT/'work/research/decomp/config/symbols.us.txt').decode(),re.M)}
cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
def dis(start,n):return [{'address':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}for i in cs.disasm(at(start,n),start)]
blocks=[]
for name,start,end in [('PS1_weapon_pose_dispatch',0x80037484,0x80037510),('frost_initializer',0x80037DB0,0x80037DFC),('cyclone_initializer',0x80037F78,0x80038004),('pose_update',0x80039378,0x800395E8),('clone_init',0x800355C0,0x80035694),('clone_update_init',0x80035694,0x800356E4)]:
 blocks.append({'name':name,'start':hex(start),'end':hex(end),'sha256':sha(at(start,end-start)),'instructions':dis(start,end-start)})
# PC/Saturn C switch is not evidence for PS1. Read the PS1 jump table used by this block.
ins=blocks[0]['instructions'];jt=[]
# The address is recorded only after inspecting the actual instruction words below.
for p in ('player_weapon.c','player_special.c','player_common.c'):load(ROOT/'work/research/decomp/src/main'/p)
boards=[]
for name,a in ars.items():
 im=Image.new('RGB',(5*232,2*324),'#273442');dr=ImageDraw.Draw(im)
 for row,mask in enumerate((0,15)):
  for col,n in enumerate(REFS):
   pic=a.composite(n,mask,2)[0];bb=pic.getchannel('A').getbbox();window=(130,126,188,202)
   assert bb is None or (bb[0]>=window[0]and bb[1]>=window[1]and bb[2]<=window[2]and bb[3]<=window[3])
   pic=pic.crop(window).resize((232,304),Image.Resampling.NEAREST);im.paste(pic,(col*232,row*324+20),pic);dr.text((col*232+3,row*324+4),f'{name} {n} mask{mask}',fill='white')
 p=O/f'{name}.png';im.save(p);boards.append({'path':rel(p),'sha256':sha(p.read_bytes()),'world_window':[-30,-34,28,42],'actual_viewed':False})
r={'scope':'원US PL00/PL02 및 현재 Shibuki88/89/95/96/97 공유·원EXE 표/호출 명령 읽기. 제작/게임실행 없음.','original_hashes':{n:sha(b)for n,b in assets.items()},'archives':{n:sha(a.data)for n,a in ars.items()},'frames':rows,'relations':relations,'tables':linked,'EXE_table_bytes_exact':True,'native_blocks':blocks,'source_files':tracked,'boards':boards,'native_execution_performed':False,'gameplay_verified':False,'game_or_art_modified':False}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'relations':[{'archive':q['archive'],'source':q['source'],'target':q['target'],'layers':[{k:x[k]for k in('bank','changed_pixels','extra_render_opaque','body_parts_all_matched','shift_then_extra_exact')}for x in q['layers']]}for q in relations],'tables':[{ 'id':q['id'],'refs':[s['frame']for s in q['steps']]}for q in linked]},ensure_ascii=False))
