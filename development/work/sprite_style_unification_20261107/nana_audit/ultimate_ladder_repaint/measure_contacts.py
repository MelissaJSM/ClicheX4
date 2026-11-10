"""현재 원화의 국소 손/발 위치를 읽기 측정한다. 그림을 수정하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,helper
BOXES={143:{'raised_hand':[-17,-32,-5,-20],'lower_foot':[-2,13,18,27]},144:{'raised_hand':[-13,-34,-2,-23],'lower_foot':[-5,14,9,27]},146:{'raised_hand':[-12,-34,-1,-23],'lower_foot':[-5,14,9,27]},149:{'raised_hand':[0,-37,10,-26],'front_hand':[-17,-13,-6,-3],'lower_foot':[-3,14,11,27]},151:{'left_hand':[-14,-30,-3,-20],'right_hand':[5,-22,16,-11],'lower_foot':[-8,13,5,26]},153:{'left_hand':[-20,-2,-8,9],'right_hand':[7,-2,20,9],'feet':[-8,0,9,14]}}
def metric(z,box,skin):
 x0,y0,x1,y1=box;q=z[y0+160:y1+160,x0+160:x1+160];mask=np.isin(q,(10,11,12,13))if skin else q>0;y,x=np.nonzero(mask)
 return None if not len(x)else {'pixels':len(x),'world_bbox':[int(x.min()+x0),int(y.min()+y0),int(x.max()+x0+1),int(y.max()+y0+1)],'mean_world':[float(x.mean()+x0),float(y.mean()+y0)]}
def main():
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());out=D/'contact_measurements_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 for n in BOXES:
  source=D/('a_arm_registered_v1'if n in(143,144,146)else'b_registered_v1')
  for form,mask in(('before',15),('after',0)):
   src=source/f'{form}_{n:03}_indices.png';new=np.array(Image.open(src));old=a.layer(n)[0].copy()
   if mask:
    for pb in(8,5,7,6):z=a.layer(n,pb)[0];old[z>0]=z[z>0]
   ims=[]
   for name,z in(('old exact',old),('new fixed',new)):
    im=a.rgba(z,16 if mask else 0);canvas=Image.new('RGBA',im.size);canvas.alpha_composite(im);dr=ImageDraw.Draw(canvas)
    for tag,box in BOXES[n].items():x0,y0,x1,y1=box;dr.rectangle((x0+160,y0+160,x1+159,y1+159),outline=(40,170,210,255),width=1)
    ims.append((name,canvas))
   rows.append((f'{form}{n}',ims));records.append({'ref':n,'form':form,'source':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'regions':{tag:{'box':box,'type':'skin-only'if 'hand'in tag else'full-visible-window','old':metric(old,box,'hand'in tag),'new':metric(new,box,'hand'in tag)}for tag,box in BOXES[n].items()},'art_modified':False})
 for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',5)
 write(out/'report.json',{'parent_arc_sha256':sha(a.data),'frames':records,'scope':'손/발 의미창의 기하 측정. 피부색창에 팔도 섞일 수 있어 평균점을 최종관절로 단정하지 않는다. 실제 전체원화와 함께 검토하며 자동이동/의상수정/채택 없음.','costume_edit_blocked_separately':True,'native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'form':q['form'],'bbox':{k:[v['old']['world_bbox']if v['old']else None,v['new']['world_bbox']if v['new']else None]for k,v in q['regions'].items()}}for q in records]))
if __name__=='__main__':main()
