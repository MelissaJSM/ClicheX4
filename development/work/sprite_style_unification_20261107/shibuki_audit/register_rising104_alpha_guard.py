"""비정상 배경 alpha와 실제 스프라이트 외곽을 연결성으로 구분한다.

색/그림을 추가하지 않는다. alpha224의 유일한 큰 몸체 성분을 그대로 보존하고
멀리 분리된 생성 배경 잔여만 제외한다. alpha240의 몸체 손실을 별도 보고한다.
"""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_fill_holes
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
def main():
    out=H/'rising_right_hand_native05';need(not out.exists(),'Fresh output');out.mkdir()
    a=Archive((H/'prepared_rising_fire_base02/PL00_U.ARC').read_bytes());src=H/'rising104_height_edit01/generated.png'
    need(sha(src.read_bytes())=='79be1132c68ca74d4d41ab0f5d46adaa08af6a3ba487be08c146357a5875a819','Original edit changed');im=Image.open(src).convert('RGBA');rows=[]
    for col,form,mask,pal in ((0,'base',0,0),(1,'fourth',15,16)):
        cell=np.array(im.crop((col*768,128,(col+1)*768,896)).resize((64,64),Image.Resampling.NEAREST));rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
        q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<224]=0
        labs,num=label(q>0,np.ones((3,3)));sizes=np.bincount(labs.ravel());sizes[0]=0;body=int(sizes.argmax());need(int(sizes[body])==(907 if form=='base' else 908),'Unexpected body component')
        removed=[]
        for part in range(1,num+1):
            if part==body:continue
            yy,xx=np.nonzero(labs==part);removed.append({'pixels':len(xx),'bbox':[int(xx.min()-32),int(yy.min()-36),int(xx.max()+1-32),int(yy.max()+1-36)]})
            need(len(xx)<=11,'Unexpected second body')
        q[labs!=body]=0;v=np.zeros((384,384),np.uint8);v[124:188,128:192]=q
        old240=np.array(Image.open(H/f'rising_right_hand_native04/{form}_104_indices.png'));need(not np.any((old240>0)&(v!=old240)),'Existing240 body differs')
        restored=[[int(px)-160,int(py)-160,int(v[py,px])]for py,px in zip(*np.nonzero((old240==0)&(v>0)))]
        Image.fromarray(v).save(out/f'{form}_104_indices.png');new=a.rgba(v,pal);new.save(out/f'{form}_104.png')
        for suffix in('_indices.png','.png'):(out/f'{form}_103{suffix}').write_bytes((H/f'rising_right_hand_native04/{form}_103{suffix}').read_bytes())
        page([('104 alpha240 edge loss',a.rgba(old240,pal)),('104 source224 actual body',new)],a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=6)
        rows.append({'form':form,'metrics':metrics(new),'source_threshold':224,'body_components':1,'removed_disconnected_background':removed,'restored_source_edge_pixels':restored,'restored_count':len(restored),'remaining_holes':[[int(px)-160,int(py)-160]for py,px in zip(*np.nonzero(binary_fill_holes(v>0)&(v==0)))],'new_pixels_painted':0})
    write(out/'report.json',{'passed':True,'source_sha256':sha(src.read_bytes()),'rows':rows,'registration':'fixed64 crop,1/12, originalpalette nearest,alpha224,unique largest connected body only','body_source_texels_all_exact':True,'candidate_not_gameplay':True});print(json.dumps(rows))
if __name__=='__main__':main()
