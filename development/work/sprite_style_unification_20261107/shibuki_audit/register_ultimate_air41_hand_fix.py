"""공중41 새 원화의 잘못된 세 번째 손만 실제 국소 교정 원화로 교체한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
from scipy.ndimage import label
def main():
    source=H/'ultimate_air41_extra_hand_edit01/generated.png';need(sha(source.read_bytes())=='df5073cbfa5ad258670e47d128da42f7248ef978046093a908fd7e4994baf32b','Wrong correction');im=Image.open(source).convert('RGBA');need(im.size==(1536,1024),'Wrong source dimensions');sm=np.array(im.resize((192,128),Image.Resampling.NEAREST));a=Archive((H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes());out=H/'ultimate_air_native02_corrected02';need(not out.exists(),'Fresh output required');out.mkdir();yy,xx=np.indices((384,384));x=xx-160;y=yy-160;region=(x>=5)&(x<10)&(y>=-22)&(y<-16);rows=[]
    for row,(form,mask,pal)in enumerate((('before',15,16),('after',0,0))):
        colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);cell=sm[row*64:(row+1)*64,64:128];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0;newsource=np.zeros((384,384),np.uint8);newsource[124:188,128:192]=q;pics=[]
        for n in(37,41,43):
            old=np.array(Image.open(H/f'ultimate_air_native02/{form}_{n:03}_indices.png'));new=old.copy()
            if n==41:new[region]=newsource[region]
            need(np.array_equal(old[~region],new[~region]),'Outside correction modified');Image.fromarray(new).save(out/f'{form}_{n:03}_indices.png');a.rgba(new,pal).save(out/f'{form}_{n:03}.png');delta=old!=new;lab,_=label(new>0,np.ones((3,3)));components=sorted(np.bincount(lab.ravel())[1:].tolist(),reverse=True);skinold=int((np.isin(old,[10,11,12,13])&region).sum());skinnew=int((np.isin(new,[10,11,12,13])&region).sum())
            if n==41:
                # One bare-forearm edge pixel remains at(5,-17), connected to
                # the real raised arm. The isolated third-hand region has none.
                skinmask=np.isin(new,[10,11,12,13])&region
                need(not np.any(skinmask&~((x==5)&(y==-17))),'Extra-hand skin remains');need(len(components)==1,'Native sprite separated')
            pics.extend([(f'{n} old body',a.composite(n,mask)[0]),(f'{n} corrected new body',a.rgba(new,pal))]);rows.append({'form':form,'ref':n,'changed_pixels_from_new_page':int(delta.sum()),'source_extra_skin_before':skinold,'source_extra_skin_after':skinnew,'connected_components':components,'local_source_pixels_exact':bool(np.array_equal(new[region],newsource[region]))if n==41 else None,'all_other_source_pixels_exact':True,'new_metrics':metrics(a.rgba(new,pal))})
        page(pics,a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
    Image.fromarray(region.astype(np.uint8)*255).save(out/'correction_region.png');write(out/'report.json',{'passed':True,'corrected_source_sha256':sha(source.read_bytes()),'scale':0.125,'alpha_threshold':128,'region_world':[5,-22,10,-16],'rows':rows,'actual_two_real_fists_preserved_outside_region':True,'real_bare_forearm_edge_pixel':[5,-17],'whole_new_art_not_replaced':True,'arc_or_game_written':False});print(json.dumps(rows))
if __name__=='__main__':main()
