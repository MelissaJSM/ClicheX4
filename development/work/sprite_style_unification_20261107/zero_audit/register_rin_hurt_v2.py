"""Candidate native registration after new two-pose anatomy correction."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'hurt_registered_v2';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();arc=(D/'prepared_movement_finish_v1/PL01_U.ARC').read_bytes()
assert hashlib.sha256(arc).hexdigest()=='72d04d36dde42379a144dc4688b09c582e4c0f867bc70d5742c33bb65b75b42a'
pal=struct.unpack_from('<16H',entry(arc,9));red=struct.unpack_from('<16H',entry(arc,9),13*32)
spec={135:dict(source='hurt135139_fix01',poly=[(144,133),(168,133),(169,137),(170,146),(166,149),(159,151),(151,151),(144,146)],delta=(-1,-1)),139:dict(source='hurt135139_fix01'),149:dict(source='hurt_lowhp01',poly=[(142,138),(171,138),(171,152),(166,156),(160,159),(153,159),(147,156),(142,153)],delta=(1,1)),152:dict(source='hurt_lowhp01',whole=(3,0))}
def votes(d,n):
 inf=json.loads((d/'inputs.json').read_text('utf8'));reg=json.loads((d/'native/registration.json').read_text('utf8'));gen=Image.open(d/'generated.png').convert('RGBA');cw,ch=gen.width/inf['columns'],gen.height/inf['rows'];nw,nh=inf['native_cell'];f=next(f for f in inf['frames']if f['ref']==n);cx,cy=f['cell'];dy=next(f['translate'][1]for f in reg['records']if f['ref']==n);v=np.array(gen.crop((round(cx*cw),round(cy*ch),round((cx+1)*cw),round((cy+1)*ch)))).astype(float);r,g,b,alpha=[v[:,:,k]for k in range(4)];ratio=np.divide(g,b,out=np.zeros_like(g),where=b>0);yy,xx=np.nonzero((alpha>=128)&(r<g*.6)&(g>90)&(ratio>.6)&(ratio<1.15));return collections.Counter(zip((inf['crop'][0]+xx*nw/cw).astype(int).tolist(),(inf['crop'][1]+yy*nh/ch+dy).astype(int).tolist()))
targets={};records=[]
for n,s in spec.items():
 source=D/s['source'];p=source/'native'/f'b0_{n:03}_indices.png';z=np.array(Image.open(p));b=z.copy();ops=[]
 if n in (139,149):
  vv=votes(source,n)
  pos,num=max(vv.items(),key=lambda q:q[1])
  assert num>=10 and 145<=pos[0]<=165 and 140<=pos[1]<=160
  b[pos[1],pos[0]]=15
  ops.append({'source_iris':list(pos),'source_cyan_votes':num,'index':15})
 if 'poly'in s:
  mi=Image.new('1',(384,384));ImageDraw.Draw(mi).polygon(s['poly'],fill=1);m=np.array(mi,bool);dx,dy=s['delta'];b[m]=0;y,x=np.where(m);b[y+dy,x+dx]=z[y,x]
  if n==149:
   # The source iris is part of the translated head, preserve its weighted vote.
   b[pos[1]+dy,pos[0]+dx]=15
  ops.append({'name':'head','polygon':s['poly'],'delta':s['delta'],'negative_spaces':True})
 if 'whole'in s:
  dx,dy=s['whole'];b=np.roll(np.roll(b,dx,1),dy,0);ops.append({'name':'wholebody','delta':s['whole']})
 old=render(arc,0,0,n)[0];assert b.max()<=15;targets[n]=b;Image.fromarray(b).save(O/f'b0_{n:03}_indices.png')
 def eyes(v):
  y,x=np.where(v==15);return list(map(list,zip(x.tolist(),y.tolist())))
 records.append({'ref':n,'source_native':str(p.relative_to(ROOT)),'source_native_sha256':sha(p),'source_generated_sha256':sha(source/'generated.png'),'operations':ops,'output_sha256':sha(O/f'b0_{n:03}_indices.png'),'eye_before':eyes(old),'eye_after':eyes(b),'bbox_before':rgba(old,pal).getbbox(),'bbox_after':rgba(b,pal).getbbox(),'floor_before':int(np.where(old>0)[0].max()),'floor_after':int(np.where(b>0)[0].max()),'old_pixels_pasted':0})
for form,words in [('normal',pal),('black',red)]:
 items=[]
 for n in spec:
  old=render(arc,0,0,n)[0];im=rgba(targets[n],words);im.save(O/f'b0_{n:03}_{form}.png');items.extend([(f'{n} previous',rgba(old,words)),(f'{n} detailed candidate',im)])
 page(items,rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=2,scale=5)
(O/'registration.json').write_text(json.dumps({'records':records,'unpacked':True,'accepted':False,'scope':'135/139 새 국소 보완 원화 사용.135 머리(-1,-1),149 source cyan 복원 및 머리(+1,+1),152 전신(+3,0).139는 원화보다 약2px 깊게 웅크리는 잔차가 있어 미술검토 대기. 원래 몸체 픽셀 덮기/전신축소 없음.'},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
