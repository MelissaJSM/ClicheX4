"""Register authored new art to pose contacts; no old head/body paste."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'after122_registered_v1';assert not O.exists();O.mkdir()
arc=(D/'prepared_ground_first_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='cf01c08e17c742983abcd566e08f165c2c48205b453d051ce64ea58ca1a8c0c1'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
def poly(points):
 m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon(points,fill=1);return np.array(m,bool)
def move(z,points,delta):
 m=poly(points);a=z.copy();dx,dy=delta;z[m]=0;y,x=np.where(m);assert np.all((x+dx>=0)&(x+dx<384)&(y+dy>=0)&(y+dy<384));z[y+dy,x+dx]=a[y,x]
 return {'polygon':points,'translation':list(delta),'source_opaque_pixels':int((a[m]>0).sum()),'source_negative_pixels':int((a[m]==0).sum())}
def iris_vote(folder,n):
 info=json.loads((folder/'inputs.json').read_text('utf8'));reg=json.loads((folder/'native/registration.json').read_text('utf8'));im=Image.open(folder/'generated.png').convert('RGBA');cw,ch=im.width/info['columns'],im.height/info['rows'];nw,nh=info['native_cell'];f=next(q for q in info['frames']if q['ref']==n);cx,cy=f['cell'];dy=next(q['translate'][1]for q in reg['records']if q['ref']==n)
 v=np.array(im.crop((round(cx*cw),round(cy*ch),round((cx+1)*cw),round((cy+1)*ch)))).astype(float);r,g,b,a=[v[:,:,k]for k in range(4)];ratio=np.divide(g,b,out=np.zeros_like(g),where=b>0);yy,xx=np.where((a>=128)&(r<g*.6)&(g>90)&(ratio>.6)&(ratio<1.15));votes=collections.Counter(zip((info['crop'][0]+xx*nw/cw).astype(int).tolist(),(info['crop'][1]+yy*nh/ch+dy).astype(int).tolist()));votes={p:c for p,c in votes.items()if 130<=p[0]<=160 and 138<=p[1]<=155};p,c=max(votes.items(),key=lambda q:q[1]);assert c>=10,(n,p,c);return p,c
whole={(0,71):(1,0),(0,73):(2,0),(0,82):(1,0),(0,131):(3,0),(1,51):(1,0),(1,57):(2,0)}
records=[]
for folder,b,refs in [('ground_followup01',0,[71,73,82,131]),('wall_saber01',1,[50,51,54,57])]:
 items={k:[]for k in ('normal','black')}
 for n in refs:
  source=D/folder/'native'/f'b{b}_{n:03}_indices.png';a=np.array(Image.open(source));z=a.copy();ops=[]
  if b==1 and n in(50,57):
   pos,count=iris_vote(D/folder,n);z[pos[1],pos[0]]=15;ops.append({'source_iris_cell':list(pos),'actual_cyan_source_pixels':count,'mapped_palette_index':15})
  if (b,n)in whole:
   dx,dy=whole[b,n];z=np.roll(z,(dy,dx),(0,1));ops.append({'whole_translation':[dx,dy],'reason':'눈·몸통·부츠의 공통 수평 편차를 새 원화 전체의 평행이동으로 정합'})
  if b==0 and n==131:
   ops.append(move(z,[(144,133),(165,133),(171,140),(172,150),(168,153),(150,153),(144,149)],(0,1)))
   ops.append(move(z,[(178,142),(188,142),(188,156),(183,161),(176,161),(176,155),(179,153)],(-2,0)))
  if b==1 and n==51:
   ops.append(move(z,[(148,152),(153,152),(163,159),(164,166),(156,166),(150,160)],(0,1)))
  if b==1 and n in(54,57):
   pts=[(156,145),(158,139),(158,131),(168,131),(168,145),(163,150),(157,151)] if n==54 else [(158,144),(159,137),(159,131),(168,131),(168,145),(163,149),(157,150)]
   ops.append(move(z,pts,(0,-1)))
  p=O/f'b{b}_{n:03}_indices.png';Image.fromarray(z).save(p);old=render(arc,b,b*5,n)[0]
  records.append({'key':f'b{b}_{n:03}','bank':b,'ref':n,'source_native':str(source.relative_to(ROOT)),'source_native_sha256':sha(source.read_bytes()),'generated_sha256':sha((D/folder/'generated.png').read_bytes()),'operations':ops,'output_sha256':sha(p.read_bytes()),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'old_body_or_head_override':False,'manually_invented_color':False})
  for form,words in [('normal',pal),('black',red)]:
   pic=rgba(z,words);pic.save(O/f'{form}_b{b}_{n:03}.png');items[form].extend([(f'{n} before',rgba(old,words)),(f'{n} source',rgba(a,words)),(f'{n} registered',pic)])
 for form,words in [('normal',pal),('black',red)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{folder}_{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'candidate_only':True,'source_arc_sha256':sha(arc),'records':records,'runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(str(O))
