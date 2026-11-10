"""생성 원화의 실제 중간톤 점유율을 추적해 native 다수결 손실을 비교한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write

def main():
 source=H/'ladder_detail_inputs01/generated_page01.png';need(sha(source.read_bytes())=='03ce1cca705a9b1ea6073a86d339a2d5108c7b8c6c306e03584902f5dce949af','Source changed');im=Image.open(source).convert('RGBA');a=Archive((H/'prepared_wall_front01/PL00_U.ARC').read_bytes());out=H/'ladder_detail_vote_probe01';need(not out.exists(),'Output exists');out.mkdir();records=[];reviews={0:[],15:[]}
 for row,(form,mask,start)in enumerate((('base',0,0),('fourth',15,16))):
  rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.int32)
  for col,n in enumerate((143,144,146)):
   sourcecell=im.crop((col*512,row*512,(col+1)*512,(row+1)*512));rgba=np.array(sourcecell);labels=np.zeros((512,512),np.uint8)
   for y in range(512):labels[y]=np.argmin(((rgba[y,:,:3].astype(np.int32)[:,None,:]-rgb[1:][None,:,:])**2).sum(2),axis=1)+1
   votes=np.stack([np.where(labels==k,rgba[:,:,3],0).astype(float).reshape(64,8,64,8).sum((1,3))/(64*255)for k in range(16)])
   v=np.array(Image.open(H/f'ladder_native_page01/{form}_{n:03}_indices.png'));small=v[128:192,128:192];yy,xx=np.indices((64,64));x=xx-32;y=yy-32
   hair=(x>=-10)&(x<=10)&(y>=-24)&(y<=-1)
   if n==143:hair=(x>=-11)&(x<=8)&(y>=-20)&(y<=-5)
   # Only native texels already classified as hair/cloth are considered;
   # silhouette, eyes, gold, skin, outline and ornaments cannot change.
   transitions=[(5,14),(14,8)]if start==0 else[(6,5),(5,4)]
   for threshold in(.12,.20,.28):
    w=small.copy();changes=[]
    for light,mid in transitions:
     chosen=hair&(small==light)&(votes[mid]>=threshold)
     for py,px in zip(*np.nonzero(chosen)):changes.append({'world':[int(px-32),int(py-32)],'from':light,'to':mid,'actual_source_coverage':float(votes[mid,py,px]),'region':'hair'})
     w[chosen]=mid
    if n==143 and start==0:
     sleeve=(x>=-15)&(x<=-1)&(y>=-1)&(y<=10)
     for light,mid in((9,6),(6,3)):
      chosen=sleeve&(small==light)&(votes[mid]>=threshold)
      for py,px in zip(*np.nonzero(chosen)):changes.append({'world':[int(px-32),int(py-32)],'from':light,'to':mid,'actual_source_coverage':float(votes[mid,py,px]),'region':'sleeve'})
      w[chosen]=mid
    target=v.copy();target[128:192,128:192]=w;need(np.array_equal(target>0,v>0),'Alpha changed');Image.fromarray(target).save(out/f'{form}_{n:03}_coverage{round(threshold*100):02}_indices.png');pic=a.rgba(target,start);pic.save(out/f'{form}_{n:03}_coverage{round(threshold*100):02}.png');reviews[mask].append((f'{n} src tone >= {threshold:.0%}',pic));records.append({'form':form,'ref':n,'source_coverage_threshold':threshold,'changed_pixels':len(changes),'source_evidence':changes})
   # Direct high-resolution crop beside the native majority and 20% candidate.
   world=(-12,-25,13,1)if n!=143 else(-16,-21,13,11);srcbox=tuple((q+32)*8 for q in world);nativebox=tuple(q+160 for q in world);full=sourcecell.crop(srcbox);old=a.rgba(v,start).crop(nativebox).resize(full.size,Image.Resampling.NEAREST);candidate=Image.open(out/f'{form}_{n:03}_coverage20.png').crop(nativebox).resize(full.size,Image.Resampling.NEAREST);board=Image.new('RGB',(full.width*3,full.height+24),'#1a202b');dr=ImageDraw.Draw(board)
   for i,(label,pic)in enumerate((('source generated',full),('majority native',old),('source middle-tone coverage',candidate))):board.paste(pic,(i*full.width,24),pic);dr.text((i*full.width+4,5),label,fill='white')
   board.save(out/f'{form}_{n:03}_source_loss.png')
 for mask,name in((0,'base'),(15,'fourth')):page(reviews[mask],a.composite(0,mask)[0],out/f'{name}_comparison.png',cols=3,scale=4)
 write(out/'analysis.json',{'source_sha256':sha(source.read_bytes()),'records':records,'proposal_not_final':True,'new_black_lines_drawn':False,'old_head_or_body_copied':False,'full_image_color_or_scale_change':False,'alpha_preserved':True,'principle':'원화에 실제 존재하나8×8다수결에서 소실된 기존 팔레트 중간톤의 점유율만 검토한다. 스스로 새로운 선을 그린 것이 아니며 모든 후보는 미패킹이다.'});print([(r['form'],r['ref'],r['source_coverage_threshold'],r['changed_pixels'])for r in records])

if __name__=='__main__':main()
