"""Original US ladder image/part mirrors and EXE sequence, read-only evidence."""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
D=Path(__file__).parent;B=D.parent;O=D/'ultimate_ladder_aliases01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
us=ROOT/'MegaMan X4.bin'
with us.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
assets,_=read_disc(us,('PL00_U.ARC','PL02_U.ARC','SLUS_005.61'))
exe=assets['SLUS_005.61'];currentp=B/'shibuki_audit/prepared_ultimate_dash01/PL02_U.ARC';current=currentp.read_bytes()
assert sha(current)=='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb'
archives={'original_PL00':Archive(assets['PL00_U.ARC']),'original_PL02':Archive(assets['PL02_U.ARC']),'current_shibuki_PL02':Archive(current)}
pairs=[(144,145),(146,147),(149,148),(151,152)]
def mirrored(a,k):
 out=np.zeros_like(a);ys,xs=np.nonzero(a[:,:,3]if a.ndim==3 else a);tx=320-xs+k
 assert np.all((tx>=0)&(tx<384))
 out[ys,tx]=a[ys,xs];return out
def bbox(mask):
 ys,xs=np.nonzero(mask)
 return[int(xs.min()-160),int(ys.min()-160),int(xs.max()+1-160),int(ys.max()+1-160)]if len(xs)else None
rows=[]
for name,a in archives.items():
 for source,target in pairs:
  row={'archive':name,'source':source,'target':target,'transform_convention':'목표 world_x=-source_world_x+k, world_y 동일','layers':{}}
  fs,ft=(a.banks[0]['frames'][n]for n in(source,target))
  row['same_raw_stream']=fs['offset']==ft['offset'];row['tile_counts']=[fs['tile_count'],ft['tile_count']]
  for pb in(0,5,6,7,8):
   s=a.layer(source,pb)[0];t=a.layer(target,pb)[0];matches=[];distances=[]
   for k in range(-3,4):
    pred=mirrored(s,k);delta=pred!=t
    if not np.any(delta):matches.append(k)
    distances.append({'k':k,'different_index_pixels':int(delta.sum()),'different_alpha_pixels':int(np.count_nonzero((pred>0)!=(t>0))),'difference_bbox':bbox(delta)})
   best=min(distances,key=lambda v:v['different_index_pixels'])
   ps=composition_frame(a.c,pb,source)['parts'];pt=composition_frame(a.c,pb,target)['parts']
   partmatches=[]
   for k in range(-3,4):
    wanted=collections.Counter((p['tile'],p['flags']^64,-p['x']-15+k,p['y'])for p in ps)
    actual=collections.Counter((p['tile'],p['flags'],p['x'],p['y'])for p in pt)
    if wanted==actual:partmatches.append(k)
   row['layers'][str(pb)]={'empty_both':not np.any(s)and not np.any(t),'exact_raster_mirror_k':matches,'best':best,'part_count':[len(ps),len(pt)],'exact_same_tiles_flipped_part_k':partmatches,
    'source_parts':[{'tile':p['tile'],'flags':p['flags'],'x':p['x'],'y':p['y']}for p in ps],
    'target_parts':[{'tile':p['tile'],'flags':p['flags'],'x':p['x'],'y':p['y']}for p in pt]}
  row['whole5_layer_exact_k']=[k for k in range(-3,4)if all(k in l['exact_raster_mirror_k']for l in row['layers'].values())]
  rows.append(row)
base=struct.unpack_from('<I',exe,24)[0]
at=lambda address,size:exe[address-base+2048:address-base+2048+size]
table=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json').read_text('utf8'))
seq=[];relevant=set(range(143,156))|{183}
for a in table['animations']:
 if not any(s['frame']in relevant for s in a['steps']):continue
 ptr=struct.unpack('<I',at(0x80119df0+a['id']*4,4))[0]
 assert ptr==int(a['address'],16)
 for s in a['steps']:assert at(int(s['address'],16),4).hex()==s['bytes']
 seq.append({'id':a['id'],'pointer':hex(ptr),'steps':[{'frame':s['frame'],'position':s['position'],'calls':s['duration_calls_uninterrupted'],'event':s['event_signed'],'relative_step':s['relative_step']}for s in a['steps']]})
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
code=[]
for name,start,end in [('ladder_up',0x80032950,0x80032a28),('ladder_down',0x80032a28,0x80032b04)]:
 ins=[{'address':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}for i in md.disasm(at(start,end-start),start)]
 code.append({'function':name,'start':hex(start),'end':hex(end),'bytes_sha256':sha(at(start,end-start)),'instructions':ins})
images=[];pal=archives['original_PL02'];crop=(128,112,192,200);scale=4;cw,ch=280,380
for n,(s,t)in enumerate(pairs):
 board=Image.new('RGB',(cw*3,ch*4),'#263345');draw=ImageDraw.Draw(board)
 for row,(name,full)in enumerate((('original_PL02',False),('original_PL02',True),('current_shibuki_PL02',False),('current_shibuki_PL02',True))):
  a=archives[name];left=a.layer(s)[0];right=a.layer(t)[0]
  if full:
   left=np.array(a.composite(s,15,1)[0]);right=np.array(a.composite(t,15,1)[0])
  best=next(r for r in rows if r['archive']==name and r['source']==s)['layers']['0']['best']['k']
  for col,(label,v)in enumerate(((f'{name} {s} '+('full'if full else'base'),left),(f'mirror k={best}',mirrored(left,best)),(f'{name} {t}',right))):
   im=(Image.fromarray(v)if v.ndim==3 else a.rgba(v)).crop(crop).resize((256,352),Image.Resampling.NEAREST);board.paste(im,(col*cw+8,row*ch+25),im);draw.text((col*cw+5,row*ch+5),label,fill='white')
 p=O/f'base_mirror_{n:02}.png';board.save(p);images.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())})
report={'scope':'원US PL00/PL02 및 현재Shibuki PL02 사다리4쌍 반전·공유·EXE표 읽기. 수정/패킹/실기 없음.',
 'input_hashes':{'original_disc': '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b',**{k:sha(v)for k,v in assets.items()},'current_PL02':sha(current)},
 'pairs':rows,'original_exe_sequences':seq,'native_code_disassembly':code,'sheets':images,'actual_sheet_views':True,
 'view_notes':'원본/현재 base와팔레트16 overlay를실제합성한4판을직접열람. 원본몸체손발교대반전과전체아머발끝1px예외를확인했고 현재시부키148은별도옛등록차이가큰것을확인. 새사다리원화수용이나실기검사가아님.',
 'conclusions':[
  '원US PL00와PL02의base층4쌍은모두동일tile/flipX파트로정확반전.145=-144-1,147=-146,148=-149,152=-151(worldx). y는동일하다.',
  '원US PL02의144/145는5층전체k=-1 exact.151/152는5층전체k=0 exact이며152 overlay5에는tile14파트가중복되지만그림은같다.',
  '원US PL02의146/147 overlay5 tile15는정반전x=-1대신0으로+1px;149/148 tile15는x=-14대신-13으로+1px. 각차이는y16이후발창92/96색인픽셀이다. 이두원작예외를base몸체반전실패로오인하지않는다.',
  '원표31오르기는148,151,145,147,149,152,144,146.32내리기는그역순이다. event7..0은상하입력전환시다른표의position으로전달하며유지시간을복원한다.',
  '실제US0x800329a4/329bc와32a7c/32a94는좌우입력으로객체+0x15를0/0x40으로쓴다. 원표의손발교대미러와캐릭터방향입력은별개다.',
  '새수용기본형의4반전관절규칙을새Ultimate의상에쓰는근거는원USbase몸체exact이다. 현재시부키의상색인exact나모든발접점동일성으로확대하지말고새손발/최하단1px는독립등록검사한다.'
 ],
 'source_code':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in[ROOT/'work/research/decomp/src/main/player.c',ROOT/'work/research/decomp/src/main/player_enter.c',ROOT/'work/research/decomp/src/main/player_special.c']],
 'limits':['조립 flipX는 몸체 반전이며 캐릭터 방향필드/진행방향은별개다. 원표에서 번갈아손발을바꾸는그림을 런타임좌우방향변경으로단정하지않는다.',
 '이번은 실제원본바이트 읽기와 정적복원이다. MIPS실행/게임입력은하지않았다. 새기본형수용원화의반전규칙은원Ultimate색인동일성근거로대체하지않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':sha((O/'report.json').read_bytes()),'pairs':[{k:r[k]for k in('archive','source','target','same_raw_stream','whole5_layer_exact_k')}for r in rows],'animation_ids':[s['id']for s in seq]}))
