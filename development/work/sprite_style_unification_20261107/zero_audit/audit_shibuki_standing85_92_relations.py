"""85..92의 실제 원US/최신 그림·공유·idle 복귀 관계 읽기 전용 조사."""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;H=B/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile
O=D/'shibuki_standing85_92_relations01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def readb(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
def box(mask):
 y,x=np.nonzero(mask);return [int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]if len(x)else None
def shift(z,dx,dy):
 out=np.zeros_like(z);sy=slice(max(-dy,0),min(384,384-dy));sx=slice(max(-dx,0),min(384,384-dx));out[max(dy,0):min(384,384+dy),max(dx,0):min(384,384+dx)]=z[sy,sx];return out
oldreport=json.loads(readb(D/'shibuki_standing_special_relations01/report.json'))
assets,_=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC','PL02_U.ARC','SLUS_005.61'))
for k,v in assets.items():assert sha(v)==oldreport['original_hashes'][k]
exe=assets['SLUS_005.61'];base=struct.unpack_from('<I',exe,24)[0];at=lambda ad,n:exe[ad-base+2048:ad-base+2048+n]
ars={f'original_{n[:4]}':Archive(v)for n,v in assets.items()if n.endswith('.ARC')}
for name,path,h in [('current_PL00',H/'prepared_standing_special_base01/PL00_U.ARC','fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e'),('current_PL02',H/'prepared_standing_special_ultimate01/PL02_U.ARC','26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce')]:
 data=readb(path);assert sha(data)==h;ars[name]=Archive(data)
PBS=(0,5,6,7,8);REFS=(0,85,86,87,89,90,91,92);PAIRS=((0,87),(0,92),(87,92),(0,85),(85,86),(85,89),(89,90),(90,91),(89,91),(0,90))
rows=[];relations=[];boards=[]
for name,a in ars.items():
 layers={(n,pb):a.layer(n,pb)[0]for n in REFS for pb in PBS}
 for n in REFS:
  f=a.banks[0]['frames'][n];rr={'archive':name,'ref':n,'stream_offset':f['offset'],'tile_count':f['tile_count'],'raw_sha256':sha(raw(a,0,n)),'raw_owners':[g['index']for g in a.banks[0]['frames']if g['offset']==f['offset']],'layers':{}}
  for pb in PBS:
   ps=parts(a,pb,n);addr={q['record_offset']for q in ps}
   rr['layers'][str(pb)]={'opaque':int(np.count_nonzero(layers[n,pb])),'bbox':box(layers[n,pb]>0),'values':sorted(map(int,np.unique(layers[n,pb]))),'parts':ps,'record_owners':[j for j in range(237)if j!=n and addr&{p['record_offset']for p in parts(a,pb,j)}]}
  rows.append(rr)
 for sn,tn in PAIRS:
  rr={'archive':name,'source':sn,'target':tn,'layers':{}}
  for pb in PBS:
   x,y=layers[sn,pb],layers[tn,pb];d=x!=y;best=None;exact=[]
   for dy in range(-3,4):
    for dx in range(-3,4):
     moved=shift(x,dx,dy);count=int(np.count_nonzero(moved!=y));key=(count,abs(dx)+abs(dy),dx,dy)
     if best is None or key<best:best=key
     if count==0:exact.append([dx,dy])
   sp,tp=parts(a,pb,sn),parts(a,pb,tn)
   def signature(ar,n,p):
    v=tile(ar,n,p['page']*256+p['tile'])
    if p['flip_x']:v=v[:,::-1]
    if p['flip_y']:v=v[::-1]
    return (p['x'],p['y'],p['clut'],sha(v.tobytes()))
   ss=[signature(a,sn,p)for p in sp];matched=[];targetonly=[]
   for i,p in enumerate(tp):
    sk=signature(a,tn,p)
    if sk in ss:matched.append({'target_part':i,'source_part':ss.index(sk)});ss[ss.index(sk)]=None
    else:targetonly.append({'index':i,'part':p})
   rr['layers'][str(pb)]={'exact':not bool(d.any()),'changed_pixels':int(d.sum()),'alpha_changed_pixels':int(np.count_nonzero((x>0)!=(y>0))),'changed_bbox':box(d),'best_rigid_within3':{'diff':best[0],'dx':best[2],'dy':best[3]},'exact_rigid_shifts':exact,'same_position_same_oriented_tile_parts':matched,'target_nonmatching_parts':targetonly}
  rr['RGBA']=[{'mask':mask,'arm':arm,'changed':int(np.any(np.asarray(a.composite(sn,mask,arm)[0])!=np.asarray(a.composite(tn,mask,arm)[0]),axis=2).sum())}for mask in(0,15)for arm in(1,2)]
  relations.append(rr)
 cw,ch=232,320;window=(131,126,189,201);im=Image.new('RGB',(cw*8,ch*2),'#273442');draw=ImageDraw.Draw(im)
 for row,mask in enumerate((0,15)):
  for col,n in enumerate(REFS):
   pic=a.composite(n,mask,2)[0];bb=pic.getbbox();assert bb is None or window[0]<=bb[0]and window[1]<=bb[1]and window[2]>=bb[2]and window[3]>=bb[3]
   pic=pic.crop(window).resize((232,300),Image.Resampling.NEAREST);im.paste(pic,(col*cw,row*ch+20),pic);draw.text((col*cw+3,row*ch+4),f'{n} mask {mask}',fill='white')
 p=O/f'{name}.png';im.save(p);boards.append({'path':rel(p),'sha256':sha(p.read_bytes()),'actual_viewed':False})
tables=json.loads(readb(ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json'));linked=[]
for q in tables['animations']:
 if any(s['frame']in REFS[1:]for s in q['steps']):
  assert struct.unpack('<I',at(0x80119DF0+q['id']*4,4))[0]==int(q['address'],16)
  for step in q['steps']:assert at(int(step['address'],16),4).hex()==step['bytes']
  linked.append(q)
r={'scope':'원US 및 최신 Shibuki PL00/PL02 0·85/86/87/89/90/91/92의 실제 그림/파트 공유와 원표 읽기. 생성·제작함수·게임 실행 없음.','original_hashes':{k:sha(v)for k,v in assets.items()},'archives':{k:sha(v.data)for k,v in ars.items()},'refs':list(REFS),'frames':rows,'relations':relations,'tables':linked,'EXE_table_bytes_exact':True,'source_files':tracked,'boards':boards,'native_execution_performed':False,'gameplay_verified':False,'game_or_art_modified':False}
p=O/'report.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':sha(p.read_bytes()),'layers0':[{k:q[k]for k in('archive','source','target')}|{'diff':q['layers']['0']['changed_pixels'],'bbox':q['layers']['0']['changed_bbox'],'best':q['layers']['0']['best_rigid_within3'],'RGBA':q['RGBA']}for q in relations],'tables':[{'id':q['id'],'refs':[s['frame']for s in q['steps']]}for q in linked]}))
