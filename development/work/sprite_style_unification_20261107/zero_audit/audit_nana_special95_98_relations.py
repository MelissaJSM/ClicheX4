"""기본/포스95..99의 현재/원US 공유와 실제 원표. 자원 읽기만 수행."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig
O=D/'nana_special95_98_relations01';O.mkdir(exist_ok=True)
PBS=(0,5,6,7,8);REFS=(95,96,98,99);tracked={}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def load(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def shift(z,dx):
 out=np.zeros_like(z);y,x=np.nonzero(z);out[y,x+dx]=z[y,x];return out
source=B/'root_nana_lowhp/packed_lowhp01/PL00_U.ARC';a=Archive(load(source))
assert sha(a.data)=='ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16'
disc,_=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC','SLUS_005.61'));us=Archive(disc['PL00_U.ARC']);exe=disc['SLUS_005.61']
def section(address,size):
 off=2048+address-struct.unpack_from('<I',exe,0x18)[0];return exe[off:off+size]
tabpath=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json'
table=json.loads(load(tabpath));linked=[]
for q in table['animations']:
 if any(s['frame']in REFS for s in q['steps']):
  pointer=struct.unpack('<I',section(0x80119DF0+q['id']*4,4))[0]
  assert pointer==int(q['address'],16)
  for s in q['steps']:assert section(int(s['address'],16),4).hex()==s['bytes']
  linked.append(q)
rows=[];relations=[]
for ar,name in((a,'current'),(us,'original_US')):
 for n in REFS:
  f=ar.banks[0]['frames'][n];layers={}
  for pb in PBS:
   ps=parts(ar,pb,n);slots={q['record_offset']for q in ps}
   layers[str(pb)]={'parts':ps,'opaque':int(np.count_nonzero(ar.layer(n,pb)[0])),
    'cluts':sorted({q['clut']for q in ps}),
    'shared_record_owners':[j for j in range(237)if j!=n and slots&{q['record_offset']for q in parts(ar,pb,j)}]}
  rows.append({'archive':name,'ref':n,'raw_sha256':sha(raw(ar,0,n)),'tile_count':f['tile_count'],
   'stream_offset':f['offset'],'raw_owners':[x['index']for x in ar.banks[0]['frames']if x['offset']==f['offset']],'layers':layers})
 for s,t in((95,96),(98,99)):
  per=[]
  for pb in PBS:
   x,y=ar.layer(s,pb)[0],ar.layer(t,pb)[0]
   per.append({'bank':pb,'translation_x_plus1_difference':int(np.count_nonzero(shift(x,1)!=y)),
    'part_translation_x_plus1':[(q['flags'],q['tile'],q['x']+1,q['y'])for q in parts(ar,pb,s)]==[sig(q)for q in parts(ar,pb,t)]})
  rgba=[]
  for mask in range(16):
   for arm in(1,2):
    x=np.asarray(ar.composite(s,mask,arm)[0]);y=np.asarray(ar.composite(t,mask,arm)[0]);z=np.zeros_like(x);z[:,1:]=x[:,:-1]
    rgba.append(int(np.any(z!=y,axis=2).sum()))
  relations.append({'archive':name,'source':s,'target':t,'layers':per,'all32_RGBA_x_plus1_exact':not any(rgba)})
for p in('work/research/decomp/src/main/player_weapon.c','work/research/decomp/src/main/player_special.c','work/research/decomp/src/main/player_common.c'):load(ROOT/p)
boards=[]
for i,ns in enumerate(((0,95,96,97),(138,139,98,99))):
 im=Image.new('RGB',(4*288,2*400),'#263345');dr=ImageDraw.Draw(im)
 for row,mask in enumerate((0,15)):
  for col,n in enumerate(ns):
   pic=a.composite(n,mask)[0].crop((126,104,194,196)).resize((272,368),Image.Resampling.NEAREST)
   x,y=col*288,row*400;im.paste(pic,(x+8,y+24),pic);dr.text((x+8,y+5),f'{n} mask{mask}',fill='white')
 p=O/f'current_{i:02}.png';im.save(p);boards.append({'path':rel(p),'sha256':sha(p.read_bytes())})
r={'scope':'최신ac1e 기본/포스95/96/98/99 저장·원US표시·원EXE표 관계 읽기. 새후보 제작/검증과 분리.',
 'source':rel(source),'source_sha256':sha(a.data),'original_US_arc_sha256':sha(us.data),'original_US_exe_sha256':sha(exe),
 'frames':rows,'x_plus1_relations':relations,'original_tables':linked,'original_exe_table_bytes_independently_checked':True,
 'callers':[
 {'function':'player_enter_frost_tower_pose','source':'work/research/decomp/src/main/player_weapon.c:965','animation':95,'note':'PLAYER_WEAPON_POSE. event80은player_weapon_pose에서shot_type2/11에따라별도무기생성.'},
 {'function':'player_enter_soul_body','source':'work/research/decomp/src/main/player_weapon.c:974','animation':96,'note':'PLAYER_SOUL_BODY. event80에서clone초기화. charged와비charged의정확입력은별도검증.'},
 {'function':'player_update_init','source':'work/research/decomp/src/main/player_common.c:566','animation':97,'note':'is_clone분기에서96단독표97. clone도SP_PLAYER_GFX bank0사용.'},
 {'function':'player_enter_double_cyclone_pose','source':'work/research/decomp/src/main/player_weapon.c:1026','animations':[104,105],'note':'shot_type7이면104,그밖105. event80에서7은2무기,16은10무기와2visual객체생성.'}],
 'important_limits':['table95와ref95는별개식별자다. unfiltered caller에같은숫자의Zero함수가있으나여기서는X경로만분리했다.',
 'func_80037484 C switch는PC/Saturn조건부라미국PS1 dispatcher를직접검증한것으로세지않는다.',
 'event/terminal을게임상태가소비하므로표끝96을실제96프레임대기라고단정하지않는다.',
 '타일/파트공유와표시그림공유는별도다. 새후보/실제효과접점/MIPS/게임실기는이보고밖이다.'],
 'boards':boards,'boards_actually_viewed':False,'tracked_sources':tracked,'runtime_verified':False}
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'relations':relations,
 'owners':[{k:v for k,v in q.items()if k!='layers'}for q in rows]},ensure_ascii=False))
