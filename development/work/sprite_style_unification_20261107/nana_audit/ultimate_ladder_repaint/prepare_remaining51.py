"""새 사다리3원화의 의상 분리와 원래 반전 좌표를 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need,helper
from prepare_a_mirrors import mirrored,full
SRC=D/'b_costume_registered51';OUT=D/'remaining_common51c'
POLYS={149:[[(-8,-14),(-4,-14),(1,-11),(3,-7),(7,-4),(7,2),(1,2),(-4,-1),(-8,-3),(-9,-7)],[(0,-31),(7,-31),(7,-20),(1,-20)]],151:[[(-12,-21),(-6,-21),(-4,-15),(-4,-12),(-7,-10),(-12,-10)],[(7,-13),(12,-13),(13,-9),(11,-6),(8,-7)], [(-2,-12),(4,-12),(6,-6),(7,3),(-7,2),(-7,-4),(-3,-7)]],153:[[(-5,-10),(6,-10),(8,-5),(8,1),(-7,1),(-7,-5)], [(-11,-4),(-7,-3),(-8,2),(-11,6),(-15,6),(-13,1)],[(8,-4),(12,-3),(15,2),(16,6),(11,6),(8,2)]]}
def mask(n):
 im=Image.new('L',(384,384));dr=ImageDraw.Draw(im)
 for p in POLYS[n]:dr.polygon([(x+160,y+160)for x,y in p],fill=1)
 return np.array(im)>0
def main():
 need(not OUT.exists(),'Fresh output');OUT.mkdir();src=json.loads((W/'staging_rn_v43.json').read_text('utf8'))['resources']['PL02_U.ARC'];p=ROOT/src['path'];need(digest(p)==src['after'],'Parent');a=Archive(p.read_bytes());bodies={};rows=[];records=[]
 for n in(149,151,153):
  b=np.array(Image.open(SRC/f'before_{n:03}_indices.png'));donor=np.array(Image.open(SRC/f'after_{n:03}_indices.png'));m=mask(n);v=np.where(m,donor,b).astype(np.uint8)
  # Preserve the exact new jacket hand contact pixels, separately from sleeves.
  if n==153:
   for x0,x1 in[(-16,-10),(12,17)]:v[165:169,160+x0:160+x1]=b[165:169,160+x0:160+x1]
  fringe=(v>0)&(b==0);before=b.copy();before[fringe]=v[fringe]
  lab,k=label(v>0,np.ones((3,3)));print(json.dumps({'ref':n,'components':[{'size':int((lab==i).sum()),'bbox':[int(np.where(lab==i)[1].min()-160),int(np.where(lab==i)[0].min()-160),int(np.where(lab==i)[1].max()-159),int(np.where(lab==i)[0].max()-159)]}for i in range(1,k+1)]}));bodies[n]=(before,v)
  Image.fromarray(m.astype('uint8')*255).save(OUT/f'mask_{n}.png');records.append({'ref':n,'costume_polygons':POLYS[n],'fringe_new_source_links':[[int(x)-160,int(y)-160,int(v[y,x])]for y,x in np.argwhere(fringe)],'source_hashes':{f:digest(SRC/f'{f}_{n:03}_indices.png')for f in['before','after']}})
 for sn,tn in[(149,148),(151,152)]:
  need(np.array_equal(mirrored(full(a,sn),0),full(a,tn)),'Original jacket mirror relation');bodies[tn]=tuple(mirrored(z,0)for z in bodies[sn]);records.append({'ref':tn,'source_ref':sn,'world_x_formula':'-x','original_jacket_exact_relation':True,'new_both_costumes_share_mirror':True})
 for n,(b,v) in bodies.items():
  for f,z in[('before',b),('after',v)]:Image.fromarray(z).save(OUT/f'{f}_{n:03}_indices.png')
  rows.append((str(n),[('idle',a.composite(0)[0]),('new jacket',a.rgba(b,16)),('new bare',a.rgba(v))]))
 helper.grid(rows[:3],OUT/'common.png',6);helper.grid(rows[3:],OUT/'mirrors.png',6)
 # Enlarged native references for the two missing firing-arm poses.
 for name,fn in [('shot_body_reference',lambda n,form: a.rgba(bodies[149][0 if form=='before'else 1],16 if form=='before'else 0)),('shot_pose_reference',lambda n,form:a.composite(n,15 if form=='before'else 0)[0])]:
  im=Image.new('RGBA',(1536,1024))
  for j,form in enumerate(['before','after']):
   for i,n in enumerate([150,155]):im.alpha_composite(fn(n,form).crop((112,124,208,188)).resize((768,512),Image.Resampling.NEAREST),(i*768,j*512))
  im.save(OUT/f'{name}.png')
 write(OUT/'manifest.json',{'parent':src,'frames':records,'refs':list(bodies),'new_art_sources_only':True,'native_packed':False,'runtime_verified':False});print(json.dumps({'refs':list(bodies),'boundary':{q['ref']:len(q.get('fringe_new_source_links',[]))for q in records}}))
if __name__=='__main__':main()
