"""Measure observable pixel landmarks; these are not inferred skeletal joints."""
from pathlib import Path
import sys,json,struct,hashlib,itertools
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).resolve().parent;variant=sys.argv[1]if len(sys.argv)>1 else'run03';assert variant in('run03','run03_fix02','targeted');OUT=D/({'run03':'rin_extension/run_anchor_review_v1','run03_fix02':'rin_extension/run_anchor_review_fix02','targeted':'rin_extension/run_anchor_review_targeted'}[variant]);OUT.mkdir(exist_ok=True)
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
parent=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';arc=read_disc(parent,('PL01_U.ARC',))[0]['PL01_U.ARC'];pal=struct.unpack_from('<16H',entry(arc,9));new={};sources={}
folders=[ROOT/'work/sprite_style_unification_20261107/rin/locomotion01/native',*(D/'rin_extension/run_inputs'/f'{name}/native'for name in ('run01','run02','run03_fix02'if variant=='targeted'else variant))]
if variant=='targeted':folders += [D/'rin_extension/run_registration_v1',*(D/f'rin_extension/targeted_fixes_registered/pose{n}/native'for n in(17,18))]
for folder in folders:
 for p in folder.glob('*_indices.png'):
  n=int(p.stem.split('_')[1])
  if 7<=n<=20:new[n]=np.array(Image.open(p));sources[n]={'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def components(mask):
 lab,num=ndimage.label(mask,np.ones((3,3),int));out=[]
 for n in range(1,num+1):
  ys,xs=np.nonzero(lab==n)
  if len(xs)<2:continue
  out.append({'bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'center':[float(xs.mean()),float(ys.mean())],'pixels':len(xs)})
 return out
def measure(a):
 yy,xx=np.nonzero(a);skin=components(np.isin(a,[12,13,14]));skin.sort(key=lambda q:q['bbox'][1]);face=skin[0];box=face['bbox'];eye_roi=np.zeros_like(a,bool);eye_roi[max(0,box[1]-3):box[3]+1,max(0,box[0]-3):box[2]+2]=True;ey,ex=np.nonzero((a==15)&eye_roi);feet=components(np.isin(a,[4,5,6])&(np.indices(a.shape)[0]>=yy.max()-13));legs=[q for q in skin if q['bbox'][1]>face['bbox'][3]+9];return {'bounds':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'face':face,'eye':None if not len(ex)else[float(ex.mean()),float(ey.mean())],'foot_color_regions':feet,'lower_skin_regions':legs}
rows=[]
for n in range(7,21):
 old=render(arc,0,0,n)[0];a,b=measure(old),measure(new[n]);row={'ref':n,'source':sources[n],'before':a,'after':b,'eye_delta':None if a['eye']is None or b['eye']is None else[np.round(y-x,2).item()for x,y in zip(a['eye'],b['eye'])],'head_top_delta':b['bounds'][1]-a['bounds'][1],'foot_pairs':[]}
 if len(a['foot_color_regions'])==len(b['foot_color_regions'])and len(a['foot_color_regions'])<=4:
  aa=a['foot_color_regions'];bb=b['foot_color_regions'];perm=min(itertools.permutations(range(len(bb))),key=lambda p:sum(sum((x-y)**2 for x,y in zip(aa[i]['center'],bb[j]['center']))for i,j in enumerate(p)))
  for i,j in enumerate(perm):row['foot_pairs'].append({'before_bbox':aa[i]['bbox'],'after_bbox':bb[j]['bbox'],'center_delta':[round(y-x,2)for x,y in zip(aa[i]['center'],bb[j]['center'])]})
 rows.append(row)
for start in range(0,14,4):
 ns=list(range(7,21))[start:start+4];board=Image.new('RGB',(1152,408*len(ns)),'#64717b');draw=ImageDraw.Draw(board)
 for row,n in enumerate(ns):
  old=render(arc,0,0,n)[0];after=new[n];diff=Image.new('RGBA',(384,384));arr=np.zeros((384,384,4),np.uint8);arr[(old>0)&(after>0)]=(160,160,160,255);arr[(old>0)&(after==0)]=(255,60,80,255);arr[(old==0)&(after>0)]=(40,230,230,255);diff=Image.fromarray(arr)
  for col,(label,pic)in enumerate([('before',rgba(old,pal)),('new',rgba(after,pal)),('old-only red / new-only cyan',diff)]):
   p=pic.crop((128,128,192,192)).resize((384,384),Image.Resampling.NEAREST);x=col*384;y=row*408;board.paste(p,(x,y+24),p);draw.text((x+4,y+5),f'{n} {label}',fill='white')
 board.save(OUT/f'poses_{start//4:02d}.png')
report={'source_bin_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'method':'眼=最上部の肌領域近傍のcyan。足=下14行の青領域。これは観測画素であり骨格の確定座標ではない。','frames':rows,'game_changed':False};report['method']='눈은 최상단 피부 영역 근처의 청록색 픽셀, 발은 아래14행의 파란 영역이다. 관측 가능한 픽셀 표식이며 실제 관절 좌표로 단정하지 않는다.';(OUT/'measurements.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps([{k:r[k]for k in('ref','eye_delta','head_top_delta','foot_pairs')}for r in rows]))
