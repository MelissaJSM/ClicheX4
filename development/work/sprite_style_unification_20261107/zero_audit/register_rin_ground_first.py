"""Register new source art locally; never paste old coarse body or draw colors."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';S=D/'ground_first01';O=D/'ground_registered_v1';assert not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();arc=(D/'prepared_hurt_lowhp_v1/PL01_U.ARC').read_bytes()
assert sha(arc)=='4e18b1cda6731f97272eba361a2ac19df3606f75a19b5352f6025d403196e769'
assert sha((S/'generated.png').read_bytes())=='ac417d1d1295943ad845f4b53f5719fca0a0096cb0cfba53afeb1bf376e2af10'
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
def polygon(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon(points,fill=1);return np.array(im,bool)
def move_part(a,points,delta,protected=None):
 m=polygon(points);protect=polygon(protected)if protected else np.zeros_like(m);m&=~protect
 out=a.copy();out[m]=0;dx,dy=delta;dst=np.roll(m,(dy,dx),(0,1));shift=np.roll(a,(dy,dx),(0,1));out[dst&~protect]=shift[dst&~protect];out[protect]=a[protect]
 return out,{'polygon':points,'translate':[dx,dy],'protected_polygon':protected,'source_art_pixels':int(np.count_nonzero(a[m])),'affected_pixels':int(np.count_nonzero(out!=a))}
ops={
 62:([[(158,132),(170,132),(171,147),(169,152),(164,152),(161,148),(158,148)],[-1,2],[(139,135),(157,134),(161,140),(161,149),(157,151),(144,151)]],),
 63:([[(133,144),(146,144),(146,154),(133,154)],[3,2],None],),
 65:([[(134,154),(145,153),(146,158),(142,164),(137,167),(132,165)],[0,2],None],),
}
items={name:[]for name in('normal','black')};records=[]
for n in(62,63,65,67):
 sourcepath=S/'native'/f'b0_{n:03}_indices.png';a=np.array(Image.open(sourcepath));z=a.copy();movements=[]
 if n==67:z=np.roll(z,2,axis=1);movements.append({'whole_art_translation':[2,0],'reason':'머리·몸통·앞발이 함께 왼쪽으로 약2px 벗어난 원화 등록을 되돌린다.'})
 for points,delta,protected in ops.get(n,[]):z,r=move_part(z,points,delta,protected);movements.append(r)
 assert z.shape==(384,384)and z.max()<16
 p=O/f'b0_{n:03}_indices.png';Image.fromarray(z).save(p)
 for label,words in[('normal',pal),('black',black)]:
  im=rgba(z,words);im.save(O/f'{label}_b0_{n:03}.png');items[label].extend([(f'{n} before',rgba(render(arc,0,0,n)[0],words)),(f'{n} new source',rgba(a,words)),(f'{n} registered',im)])
 records.append({'key':f'b0_{n:03}','native_source':str(sourcepath.relative_to(ROOT)),'native_source_sha256':sha(sourcepath.read_bytes()),'output_sha256':sha(p.read_bytes()),'operations':movements,'old_body_or_head_override':False,'new_color_drawn':False,'output_bounds':rgba(z,pal).getbbox()})
for label,words in[('normal',pal),('black',black)]:page(items[label],rgba(render(arc,0,0,147)[0],words),O/f'{label}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'candidate_only':True,'source_arc_sha256':sha(arc),'generated_sha256':sha((S/'generated.png').read_bytes()),'scope':'원래 손 접점으로 신규 원화 장갑/팔만 국소 평행이동.67 전체 원화x+2 등록.색 채움·옛 그림 덮기 없음.미술/접점 검수 후 선택.','records':records,'runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(str(O))
