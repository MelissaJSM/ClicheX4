"""復帰高さの新規生成物を固定1/8で登録。既存キャラクター画素の転記なし。"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
D=H/'dash_recovery_height01';O=H/'dash_recovery_height_native01'
SOURCE_SHA='28f6376f4b942cc4e16e1ff2611c2014dd6428ccc85025c52b664e3eb20b79e8'
def main():
    need(not O.exists(),'Fresh output required');O.mkdir()
    parent=H/'prepared_rising_right_base01/PL00_U.ARC';raw=parent.read_bytes()
    need(sha(raw)=='13a29023365419d32475cf5a6551adc4658116c8f03622d962d5b8071744e8b8','Wrong parent')
    a=Archive(raw);source=D/'generated.png';need(sha(source.read_bytes())==SOURCE_SHA,'Wrong source')
    im=Image.open(source).convert('RGBA');need(im.size==(1536,1024),'Wrong fixed size')
    sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));rows=[]
    for row,(form,mask,pal)in enumerate((('base',0,0),('fourth',15,16))):
        colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);items=[]
        for col,n in enumerate((81,83)):
            cell=sample[row*64:(row+1)*64,col*64:(col+1)*64]
            q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
            arr=np.zeros((384,384),np.uint8);arr[124:188,128:192]=q
            name=f'{form}_{n:03}';Image.fromarray(arr).save(O/f'{name}_indices.png');rgba=a.rgba(arr,pal);rgba.save(O/f'{name}.png')
            yy,xx=np.nonzero(arr);lab,ncomp=label(arr>0,np.ones((3,3),int));components=sorted([int((lab==i).sum())for i in range(1,ncomp+1)],reverse=True)
            old=a.composite(n,mask)[0];previous=Image.open(H/f'dash_detail_native03/{name}.png').convert('RGBA')
            rows.append({'form':form,'ref':n,'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'foot_y':int(yy.max()-160),'connected_components':components,'old_pixels_reused':0})
            items.extend([(f'{n} old game',old),(f'{n} first candidate - short',previous),(f'{n} corrected fixed-scale',rgba)])
        page(items,a.composite(0,mask)[0],O/f'{form}_comparison.png',cols=3,scale=6)
    write(O/'registration.json',{'source_sha256':SOURCE_SHA,'parent_sha256':sha(raw),'scale':0.125,'alpha_threshold':128,'rows':rows,'whole_body_resize':False,'game_modified':False,'partial_owner_and_pack_pending':True})
    (D/'prompt_used.txt').write_text((D/'prompt.txt').read_text('utf8'),encoding='utf8')
    write(D/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':'exec-e4c604a3-fab9-4f5c-83f0-63325fbf730c.png','sha256':SOURCE_SHA,'prompt_sha256':sha((D/'prompt_used.txt').read_bytes()),'registration':'dash_recovery_height_native01/registration.json','packed':False})
    print(json.dumps(rows))
if __name__=='__main__':main()
