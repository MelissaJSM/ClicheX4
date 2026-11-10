"""새98 전신을 발바닥 기준 y-1 등록하고 같은 새 머리·다리만 공유한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write

def main():
    o=H/'double_cyclone_ultimate_shared01';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive((H/'prepared_ultimate_wall01/PL02_U.ARC').read_bytes());need(sha(a.data)=='c851fb17b2369281667970c414be63eb31fb1f02fe5641ad667bfb4b5c8507cf','Wrong parent');d=H/'double_cyclone_native02'
    sourcebefore=np.array(Image.open(d/'ultimate_before_098_indices.png'));sourceafter=np.array(Image.open(d/'ultimate_after_098_indices.png'))
    before=np.roll(sourcebefore,-1,axis=0);fresh=np.roll(sourceafter,-1,axis=0)
    yy,xx=np.indices(before.shape);x,y=xx-160,yy-160
    # Preserve each source pixel's size; global registration is sole -1 only.
    hand=(x>=16)&(x<26)&(y>=-13)&(y<=-3)
    moves=[]
    for form,v in(('before',before),('after',fresh)):
        m=hand&(v>0);hy,hx=np.nonzero(m);values=v[hy,hx].copy();v[m]=0;need(not v[hy,hx+1].any(),'Hand overlaps external source');v[hy,hx+1]=values;moves.append({'form':form,'pixels':len(hx),'delta':[1,0]})
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+(((rgb[17:32,None]-rgb[None,1:16])**2).sum(2)).argmin(1)].astype(np.uint8)
    # The top includes the identical raised palms; below that leave the fresh
    # bare forearms and swimsuit front alone. All legs derive from this same
    # new jacket source, never from an older production frame.
    common=(y<=-5)|(y>=9)
    common|=(x>=-16)&(x<14)&(y>=-5)&(y<-2)
    common|=((x<=-9)|(x>=9))&(x>-17)&(x<15)&(y>=-2)&(y<9)&np.isin(before,[2,5,8,14,15])
    after=fresh.copy();after[common]=lut[before][common]
    uncovered=(after>0)&(before==0)
    for name,v,pal,mask in(('before',before,16,15),('after',after,0,0)):
        Image.fromarray(v).save(o/f'{name}_098_indices.png');im=a.rgba(v,pal);im.save(o/f'{name}_098.png');page([('98 parent',a.composite(98,mask)[0]),('new98 shared / sole y22',im)],a.composite(0,mask)[0],o/f'{name}_comparison.png',cols=2,scale=6)
    Image.fromarray(common.astype(np.uint8)*255).save(o/'common_mask.png');Image.fromarray(uncovered.astype(np.uint8)*255).save(o/'uncovered_mask.png');page([('jacket',a.rgba(before,16)),('bare forearms / swimsuit',a.rgba(after,0))],a.composite(0,15)[0],o/'pair.png',cols=2,scale=6)
    coords=np.column_stack(np.nonzero(uncovered));write(o/'report.json',{'passed':not uncovered.any(),'source_art_sha256':sha((H/'double_cyclone_ultimate_costume01/generated.png').read_bytes()),'parent_sha256':sha(a.data),'whole_body_registration':[0,-1],'hand_registration':moves,'common_before_to_after_palette':lut.tolist(),'common_opaque_pixels':int((before[common]>0).sum()),'new_after_pixels_changed_for_shared':int((after!=fresh).sum()),'uncovered_pixels':[[int(px-160),int(py-160),int(after[py,px])]for py,px in coords],'source_after_torso_forearms_preserved_outside_common':True,'old_body_head_limbs_copied':0,'scaling':False,'metrics_before':metrics(a.rgba(before,16)),'metrics_after':metrics(a.rgba(after,0)),'runtime_verified':False,'native_packed':False})
    print(json.dumps({'uncovered':len(coords),'before':metrics(a.rgba(before,16)),'after':metrics(a.rgba(after,0))}))
if __name__=='__main__':main()
