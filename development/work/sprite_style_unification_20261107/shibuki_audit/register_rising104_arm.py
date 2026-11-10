"""104의 새 국소 팔만 가져오고 나머지 신규 몸체를 그대로 보존한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write

def main():
    out=H/'rising104_arm_native02';need(not out.exists(),'Fresh output required');out.mkdir()
    source=H/'rising104_arm_correction01/generated.png'
    need(sha(source.read_bytes())=='c036d96febe2d623892533d04a936b54d1ed41afce243759a5d9d8103fccccc2','Source changed')
    im=Image.open(source).convert('RGBA');need(im.size==(1536,1024),'Size changed')
    sampled=np.array(im.resize((192,128),Image.Resampling.NEAREST))
    arc=Archive((H/'prepared_double_cyclone_base01/PL00_U.ARC').read_bytes())
    yy,xx=np.indices((384,384));x=xx-160;y=yy-160
    local=((x>=-21)&(x<=-9)&(y>=-31)&(y<=-19))|((x>=-21)&(x<=-11)&(y>-19)&(y<=-9))|((x>=-21)&(x<=-13)&(y>-9)&(y<=-4))
    rows=[]
    for col,(form,pal,mask)in enumerate([('base',0,0),('fourth',16,15)]):
        cell=sampled[32:96,16+col*96:80+col*96]
        colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[pal:pal+16]],np.int32)
        q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
        v=np.zeros((384,384),np.uint8);v[124:188,128:192]=q
        old=np.array(Image.open(H/f'rising_fire_native02/{form}_104_indices.png'))
        new=old.copy();new[local]=v[local]
        # The generated correction remains one pixel left of the original fist.
        # Register the complete new fist/cuff one pixel right, keeping the ear
        # and lower sleeve fixed. No inserted pixel or stretched connection.
        fist=(((y>=-29)&(y<=-24)&(x>=-18)&(x<=-10))|
              ((y>=-23)&(y<=-22)&(x>=-18)&(x<=-12)))&(new>0)
        sy,sx=np.nonzero(fist);values=new[sy,sx].copy();new[sy,sx]=0
        need(not new[sy,sx+1].any(),'Fist registration would cover another part')
        new[sy,sx+1]=values
        need(np.array_equal(old[~local],new[~local]),'Body outside arm changed')
        Image.fromarray(new).save(out/f'{form}_104_indices.png');arc.rgba(new,pal).save(out/f'{form}_104.png')
        delta=(old!=new);Image.fromarray(delta.astype(np.uint8)*255).save(out/f'{form}_changed_mask.png')
        marks=np.array(arc.rgba(new,pal));marks[delta]=[0,255,255,255]
        page([('104 before local edit',arc.rgba(old,pal)),('104 new arm',arc.rgba(new,pal)),('cyan changed pixels',Image.fromarray(marks))],arc.composite(0,mask)[0],out/f'{form}_comparison.png',cols=3,scale=5)
        skin=np.isin(new,[12,13]if pal==0 else[9])&(x<-8)&(y<-22);sy,sx=np.nonzero(skin)
        rows.append({'form':form,'changed_pixels':int(delta.sum()),'outside_arm_changed':0,
                     'source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source.read_bytes()),
                     'indexed_sha256':sha(new.tobytes()),'bounds':metrics(arc.rgba(new,pal)),
                     'raised_fist_skin_bbox':[int(sx.min()-160),int(sy.min()-160),int(sx.max()+1-160),int(sy.max()+1-160)],
                     'old_head_body_feet_preserved_outside_arm':True,
                     'new_fist_cuff_registration':[1,0],'translated_new_pixels':int(fist.sum()),
                     'destination_nonzero_overwrite':0})
    Image.fromarray(local.astype(np.uint8)*255).save(out/'allowed_arm_mask.png')
    write(out/'report.json',{'source_art_edit':'builtin 국소 팔 교정','rows':rows,'wholebody_scaled':False,
          'native_alpha_threshold':128,'fixed_source_scale':0.125,'arc_written':False,'visual_review_pending':True})
    print(json.dumps(rows))
if __name__=='__main__':main()
