"""공통 새머리/얼굴은 기본색을 유지하고 포스 장식 donor만 별도 소유 등록."""
from pathlib import Path
import sys,json,colorsys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
from register_vehicle_head_base import quant
def main():
    d=H/'vehicle_head_base_native02';need(not d.exists(),'등록 보호');d.mkdir();src=H/'vehicle_head_base_inputs01';a=Archive((H/'prepared_nova_strike_base01/PL00_U.ARC').read_bytes());whole=np.array(Image.open(src/'generated_v1.png').convert('RGBA').resize((96,96),Image.Resampling.NEAREST));Image.fromarray(whole).save(d/'whole96_rgba.png');oldbase=a.layer(184,0)[0];oldhead=a.layer(184,5)[0];oldalpha=oldbase>0;rgba={};indices={};rows=[]
    for form,x,start in (('base',14,0),('fourth',62,16)):
        cell=whole[32:59,x-6:x+19];worldrgba=np.zeros((384,384,4),np.uint8);worldrgba[117:144,144:169]=cell;rgba[form]=worldrgba;z=np.zeros((384,384),np.uint8);z[117:144,144:169]=quant(a,cell,start);need(not(oldalpha&~(z>0)).any(),'새 원화 내부 결손');extras=[[int(xx)-160,int(yy)-160,int(z[yy,xx])] for yy,xx in np.argwhere((z>0)&~oldalpha)];indices[form]=z;Image.fromarray(z).save(d/f'{form}_source_indices.png');rows.append({'form':form,'source_cell':[x-6,32,x+19,59],'outside_requested_alpha_not_adopted':extras,'old_opaque_without_new_source':0});need(len(extras)==(3 if form=='base' else 5),'외곽 추가 진단')
    base=indices['base'].copy();base[~oldalpha]=0;need(base[135,156]==7,'기본 홍채 색')
    side=np.zeros((384,384),bool);side[127:135,160:163]=True;owner=((oldhead>0)|side)&oldalpha;head=np.where(owner,indices['fourth'],0).astype('uint8');gold=[]
    for y,x in np.argwhere(owner):
        rgb=rgba['fourth'][y,x,:3];h,s,v=colorsys.rgb_to_hsv(*(rgb.astype(float)/255))
        if 28<=h*360<=55 and s>.4 and v>.55:
            gold.append({'world':[int(x)-160,int(y)-160],'source_RGB':list(map(int,rgb)),'nearest_index':int(head[y,x]),'index10':True});head[y,x]=10
    need(len(gold)>0,'포스 금색 표본');need(not head[135,156],'공통 홍채를 포스 팔레트로 덮지 않음')
    newbase=a.rgba(base);newfourth=newbase.copy();newfourth.alpha_composite(a.rgba(head,16));need(np.array_equal(np.array(newbase)[:,:,3],np.array(newfourth)[:,:,3]),'전폼 외곽 동일')
    Image.fromarray(base).save(d/'184_bank0_indices.png');Image.fromarray(head).save(d/'184_bank5_indices.png');Image.fromarray(owner.astype('uint8')*255).save(d/'fourth_owner.png');newbase.save(d/'base184.png');newfourth.save(d/'fourth184.png')
    board=Image.new('RGB',(1000,540),'#e8e6df');dr=ImageDraw.Draw(board)
    for row,(form,mask,new) in enumerate((('base',0,newbase),('fourth',15,newfourth))):
        y=row*270;dr.text((10,y+4),f'{form}: idle | parent13x15 | new common hair / local accessory | 1x/2x',fill='#202020');idle=a.composite(0,mask)[0].crop((143,132,177,157)).resize((340,250),Image.Resampling.NEAREST);board.paste(idle,(4,y+20),idle)
        for col,im in enumerate((a.composite(184,mask)[0],new)):
            im=im.crop((147,120,167,141)).resize((200,210),Image.Resampling.NEAREST);board.paste(im,(350+col*225,y+40),im)
        im=new.crop((147,120,167,141));board.paste(im,(835,y+80),im);up=im.resize((40,42),Image.Resampling.NEAREST);board.paste(up,(885,y+75),up)
    board.save(d/'comparison.png');write(d/'registration.json',{'scope':'기본/포스 작은머리2셀 중 기본의새머리/얼굴공통 + 포스새장식 donor. 기존144alpha 내부만편집.','source_parent_sha256':sha(a.data),'packing_parent_pending_root_hover':True,'generated_sha256':sha((src/'generated_v1.png').read_bytes()),'actual_size':[1254,1254],'logical_grid':[96,96],'method':'전체96 NEAREST/alpha128. 기본CLUT0 직접양자화 새머리 공통. 포스 장식은 기존16소유 + 옆장식world x0..2/y−33..−26창의source를CLUT16등록.머리/얼굴 전체를포스팔레트로바꾸지않음.','forms':rows,'alpha_exact_to_parent':True,'bbox_world':[-10,-37,3,-22],'opaque':144,'eye_world':[-4,-25],'head5_owner_count':int(owner.sum()),'new_head5_delta_pixels':int((head>0).sum()),'fourth_gold_samples':gold,'old_RGB_copied':False,'old_alpha_scope_only':True,'individual_scale_or_translation':False,'first_attempt_note':'native01의전체포스CLUT16 양자화는공통홍채의기본7색을표현하지못해가드에서중단.미채택하며새의미소유방식으로분리.','source_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in [src/'generated_v1.png',src/'generation.json',src/'input_materials_v2.json',H/'register_vehicle_head_base.py',Path(__file__)]},'files':{p.name:sha(p.read_bytes()) for p in d.glob('*.png')},'root_review_pending':True,'packed':False,'runtime_verified':False});print(json.dumps({'registration':sha((d/'registration.json').read_bytes()),'owner':int(owner.sum()),'gold':gold}))
if __name__=='__main__':main()
