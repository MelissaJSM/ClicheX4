"""Unpacked registration study: source-only rigid body regions, no old-art paste."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';S=D/'hurt_lowhp01';O=D/'hurt_registered_probe_v1';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();arc=(D/'prepared_movement_finish_v1/PL01_U.ARC').read_bytes()
assert hashlib.sha256(arc).hexdigest()=='72d04d36dde42379a144dc4688b09c582e4c0f867bc70d5742c33bb65b75b42a'
assert sha(S/'generated.png')=='8193b97476cee882485ba6999788cd79565e2bd6cf37861a8b1fe5827b506889'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
spec={
135:[('upper',[(120,125),(195,125),(195,176),(167,176),(167,164),(156,164),(153,165),(146,165),(144,163),(137,163),(134,165),(130,164),(130,158),(120,158)],(0,2),False),('head',[(144,130),(170,130),(170,149),(164,149),(162,151),(153,151),(146,146),(144,144)],(-1,1),True)],
139:[('upper',[(120,125),(195,125),(195,173),(176,173),(173,169),(166,169),(163,166),(156,166),(153,164),(147,164),(142,165),(139,164),(140,159),(120,159)],(0,1),False),('head',[(149,130),(178,130),(178,146),(170,149),(166,151),(161,152),(154,151),(149,147)],(0,1),True)],
149:[('head',[(142,138),(171,138),(171,152),(166,156),(160,159),(153,159),(147,156),(142,153)],(1,1),True)],
152:[]}
def mask(poly):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon(poly,fill=1);return np.array(im,bool)
reg=json.loads((S/'native/registration.json').read_text('utf8'));inf=json.loads((S/'inputs.json').read_text('utf8'));gen=Image.open(S/'generated.png').convert('RGBA');cw=gen.width/2
def votes(n):
 f=next(f for f in inf['frames']if f['ref']==n);cx,cy=f['cell'];dy=next(f['translate'][1]for f in reg['records']if f['ref']==n);v=np.array(gen.crop((round(cx*cw),round(cy*cw),round((cx+1)*cw),round((cy+1)*cw)))).astype(float);r,g,b,alpha=[v[:,:,k]for k in range(4)];ratio=np.divide(g,b,out=np.zeros_like(g),where=b>0);yy,xx=np.nonzero((alpha>=128)&(r<g*.6)&(g>90)&(ratio>.6)&(ratio<1.15));return collections.Counter(zip((112+xx*96/cw).astype(int).tolist(),(112+yy*96/cw+dy).astype(int).tolist()))
targets={};records=[]
for n in (135,139,149,152):
 p=S/'native'/f'b0_{n:03}_indices.png';z=np.array(Image.open(p));b=z.copy();operations=[]
 if n==149:
  vv=votes(n);pos,num=max(vv.items(),key=lambda q:q[1]);assert num>=10;assert 148<=pos[0]<=155 and 149<=pos[1]<=155;b[pos[1],pos[0]]=15;operations.append({'source_iris':list(pos),'source_cyan_votes':num,'index':15})
 for name,poly,(dx,dy),negative in spec[n]:
  m=mask(poly);layer=b.copy();b[m]=0;y,x=np.where(m if negative else m&(layer>0));b[y+dy,x+dx]=layer[y,x];operations.append({'name':name,'polygon':poly,'delta':[dx,dy],'negative_spaces':negative})
 if n==152:b=np.roll(b,3,axis=1);operations.append({'name':'wholebody','delta':[3,0]})
 assert b.max()<=15;targets[n]=b;Image.fromarray(b).save(O/f'b0_{n:03}_indices.png')
 old=render(arc,0,0,n)[0]
 records.append({'ref':n,'source':str(p.relative_to(ROOT)),'source_sha256':sha(p),'operations':operations,'output_sha256':sha(O/f'b0_{n:03}_indices.png'),'floor_before':int(np.where(old>0)[0].max()),'floor_after':int(np.where(b>0)[0].max()),'old_pixels_pasted':0})
for form,words in [('normal',pal),('black',red)]:
 items=[]
 for n in (135,139,149,152):
  old=render(arc,0,0,n)[0];z=np.array(Image.open(S/'native'/f'b0_{n:03}_indices.png'));im=rgba(targets[n],words);im.save(O/f'b0_{n:03}_{form}.png');items.extend([(f'{n} previous',rgba(old,words)),(f'{n} generic',rgba(z,words)),(f'{n} registered study',im)])
 page(items,rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'records':records,'unpacked':True,'accepted':False,'scope':'새 원화의 상체·머리를 강체 이동한 검토용 중간안. 원래 하체를 덮거나 전신 비율을 확대축소하지 않았다. 접점과 몸체 두께의 실제 검토가 필요하다.'},ensure_ascii=False,indent=2)+'\n','utf8');print(str(O))
