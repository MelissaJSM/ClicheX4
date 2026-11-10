"""138 하체의 폭/그늘 표본을 대기·원138·새 앞뒤 프레임과 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,helper
from prepare_effect_probe import full
def bbox(m):
 y,x=np.nonzero(m);return[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]if len(x)else None
def main():
 a=Archive((N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC').read_bytes());out=D/'settle_body_audit_v1';out.mkdir(exist_ok=False);items={'idle':a.layer(0)[0],'old138':a.layer(138)[0],**{f'new{n}':np.array(Image.open(D/f'common_hands_probe_v1/after_{n:03}.png'))for n in(135,136,137,138)}};reports={};yy,xx=np.indices((384,384));yy-=160;xx-=160
 for name,z in items.items():
  rows=[]
  for y in range(6,23):
   row={'world_y':y}
   for leg,x0,x1 in(('screen_left',-18,0),('screen_right',0,18)):
    vals=z[y+160,x0+160:x1+160];xs=np.flatnonzero(vals);row[leg]={'span':[int(xs.min()+x0),int(xs.max()+x0)]if len(xs)else None,'opaque_count':len(xs),'skin_10_12':int(np.isin(vals,(10,11,12)).sum()),'dark_1_4':int(np.isin(vals,(1,2,3,4)).sum()),'indices':vals.tolist()}
   rows.append(row)
  skin=(z>0)&(yy>=6)&(yy<20)&(xx>-18)&(xx<18);reports[name]={'body_bbox':bbox(z>0),'legs_y6_19_opaque':int(skin.sum()),'legs_y6_19_dark1_4':int((skin&np.isin(z,(1,2,3,4))).sum()),'rows':rows}
 source=D/'settle_v1/generated.png';im=Image.open(source).convert('RGBA').crop((0,0,768,1024));arr=np.array(im);pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);rgb=arr[:,:,:3].astype(np.float32);alpha=arr[:,:,3].astype(np.float32)/255;labs=np.empty(alpha.shape,np.uint8)
 for y in range(len(labs)):labs[y]=1+((rgb[y,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
 coverage=np.array(Image.fromarray(alpha,'F').resize((96,128),Image.Resampling.BOX));dark=np.array(Image.fromarray(np.where(np.isin(labs,(1,2,3,4)),alpha,0).astype(np.float32),'F').resize((96,128),Image.Resampling.BOX));base=np.array(Image.open(D/'settle_registered_v1/before_138_indices.png'));samples=[]
 for y in range(6,20):
  for x in range(-18,18):
   cv=float(coverage[y+64,x+48]);dv=float(dark[y+64,x+48]);v=int(base[y+160,x+160])
   if cv>=.5 and v in(10,11,12,13)and dv>.05:samples.append({'world':[x,y],'native_index':v,'source_alpha_coverage':cv,'actual_dark1_4_fraction':dv})
 helper.grid([('same-world lower-body',[ (name,a.rgba(z).crop((128,152,192,188)))for name,z in items.items()])],out/'legs_comparison.png',7)
 for form,mask in(('before',15),('after',0)):
  rows=[('same origin',[(f'idle0',a.composite(0,mask)[0]),('old138',a.composite(138,mask)[0]),('new137',a.rgba(np.array(Image.open(D/f'common_hands_probe_v1/{form}_137.png')),16 if mask else 0)),('new138',a.rgba(np.array(Image.open(D/f'common_hands_probe_v1/{form}_138.png')),16 if mask else 0))])];helper.grid(rows,out/f'{form}_comparison.png',7)
 write(out/'report.json',{'parent_arc_sha256':sha(a.data),'source_art':source.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'source_fixed_cell':[768,1024,96,128],'candidates':reports,'lost_dark_fraction_cells':samples,'scope':'같은세계행의폭/색면측정.동작간관절높이가다르므로대기와수치만으로체형확정하지않음.현재원화의그늘표본도측정했으며아트수정없음.'});print(json.dumps({'metrics':{k:{q:v[q]for q in('body_bbox','legs_y6_19_opaque','legs_y6_19_dark1_4')}for k,v in reports.items()},'source_cells_with_nonwinning_dark':len(samples)}))
if __name__=='__main__':main()
