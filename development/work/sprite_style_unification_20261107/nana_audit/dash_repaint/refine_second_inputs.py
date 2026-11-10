"""69의 원화 가닥 연결과75의 새 부츠 교정 원화를 네이티브 후보로 등록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint'),str(D.parent/'wall_repaint'),str(D.parent/'air_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
from register_air_page import crop_count
def eye(crop):
    """낮게 숙인 대시 얼굴도 포함하되 초록 가슴 장식과 구별한다."""
    rgba=np.asarray(crop).astype(np.int16);rgb=rgba[:,:,:3]
    mask=(rgba[:,:,3]>=128)&(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)
    mask[crop.height//2:]=False
    labs,count=label(mask,np.ones((3,3)))
    found=[]
    for i in range(1,count+1):
        yy,xx=np.nonzero(labs==i)
        if len(xx)>=8:found.append((float(yy.mean()),float(xx.mean()),len(xx)))
    need(bool(found),'Source eye')
    sy,sx,_=min(found)
    return sx,sy
def one(crop,q,pal):
    sx,sy=eye(crop);ex,ey=[int(np.floor(v))for v in q['eye']];ar=np.array(crop);Y,X=np.indices(ar.shape[:2]);yy,_=np.nonzero((ar[:,:,3]>=128)&(X<sx+crop.width*.15));crown=float(yy.min());scale=10/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);top=ey-round(split*scale)+1;hu=ey-top+1;hl=q['bbox'][3]-ey-1;native=np.concatenate((register(crop.crop((0,0,crop.width,split)),(width,hu),pal,'area_vote'),register(crop.crop((0,split,crop.width,crop.height)),(width,hl),pal,'area_vote')));ec=round((sx+.5)*width/crop.width-.5);native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14;ox=ex-ec;out=np.zeros((384,384),np.uint8);out[top+160:top+160+len(native),ox+160:ox+160+width]=native
    return out,{'source_eye':[sx,sy],'source_crown':crown,'native_position':[ox,top],'native_width':width,'split':split,'height_above':hu,'height_below':hl,'target_eye':[ex,ey]}
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent');pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);out=D/'basic_second_refined_v3';need(not out.exists(),'Fresh output');out.mkdir();rows=[];proof=[]
    old=np.array(Image.open(D/'basic_second_registered_v1/base_069.png'));new=old.copy();r=json.loads((D/'basic_second_registered_v1/registration.json').read_text('utf8'))['frames'][0];need(r['ref']==69,'Expected69');crop=Image.open(D/'basic_second_registered_v1/source_069.png').convert('RGBA');x,y=0,-2;ox,oy=r['native_position'];lx,ly=x-ox,y-oy;box=(lx*crop.width/r['native_width'],ly*r['split']/r['height_above'],(lx+1)*crop.width/r['native_width'],(ly+1)*r['split']/r['height_above']);ar=np.array(crop);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(float)/255;labels=np.zeros(alpha.shape,np.uint8)
    for sy in range(len(ar)):labels[sy]=1+((rgb[sy,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
    votes=[float(np.array(Image.fromarray(np.where(labels==i,alpha,0).astype(np.float32),'F').resize((1,1),Image.Resampling.BOX,box=box))[0,0])for i in range(1,16)];coverage=sum(votes);color=int(np.argmax(votes))+1;need(.35<=coverage<.5 and color in(5,6,7,8,9),'Authored partial hair strand');need(old[y+160,x+160]==0,'Empty quantized cell');new[y+160,x+160]=color;need(label(new>0,np.ones((3,3)))[1]==1,'Hair connected');Image.fromarray(new).save(out/'base_069.png');a.rgba(new).save(out/'base_069_rgba.png');proof.append({'ref':69,'source_art_sha256':digest(D/'basic_second_v1/generated.png'),'source_cell':list(box),'source_alpha_coverage':coverage,'source_color_votes':votes,'world':[x,y],'value':color,'changed_pixels':1,'reason':'原화의이어진가는가닥이50%alpha양자화에서끊겼음.40%실제소스셀1개만복원.','after_sha256':sha(new.tobytes())});rows.append(('69가닥',[('원등록',a.rgba(old)),('같은원화의연결셀',a.rgba(new)),('대기',a.composite(0)[0])]))
    q=next(q for q in plan['frames']if q['ref']==75);old75,ro=one(Image.open(D/'dash75_edit_target.png').convert('RGBA'),q,pal);crop,box=crop_count(Image.open(D/'dash75_boots_v1/generated.png').convert('RGBA'),0,1);new_source,rn=one(crop,q,pal);Y,X=np.indices(old.shape);mask=(Y>=160+rn['target_eye'][1]+8)&(X>=151)&(X<=176);new75=old75.copy();new75[mask]=new_source[mask];need(np.array_equal(new75[~mask],old75[~mask]),'New upper unchanged');need(label(new75>0,np.ones((3,3)))[1]==1,'No detached boot');need(np.nonzero(new75)[0].max()==182,'Foot y');Image.fromarray(old75).save(out/'source_original_075.png');Image.fromarray(new_source).save(out/'source_edited_075.png');Image.fromarray(new75).save(out/'base_075.png');a.rgba(new75).save(out/'base_075_rgba.png');crop.save(out/'source_075.png');proof.append({'ref':75,'original_source_art_sha256':digest(D/'basic_second_v1/generated.png'),'edited_source_art_sha256':digest(D/'dash75_boots_v1/generated.png'),'source_crop':box,'original_registration':ro,'edited_registration':rn,'mask_world':[-9,rn['target_eye'][1]+8,17,23],'upper_exact':True,'components_8':1,'after_sha256':sha(new75.tobytes())});rows.append(('75부츠',[('원등록결함',a.rgba(old75)),('새다리/부츠만',a.rgba(new75)),('원래게임',a.composite(75)[0])]))
    for n in(77,81):
        q=np.array(Image.open(D/f'basic_second_registered_v1/base_{n:03}.png'));Image.fromarray(q).save(out/f'base_{n:03}.png');a.rgba(q).save(out/f'base_{n:03}_rgba.png')
    helper.grid(rows,out/'comparison.png',10);write(out/'registration.json',{'frames':proof,'source_arc_sha256':sha(a.data),'scope':'원화기반국소등록 후보.비선택옛게임그림덮기없음.','native_packed':False,'runtime_verified':False});print(json.dumps({'out':str(out),'refs':[69,75,77,81]}))
if __name__=='__main__':main()
