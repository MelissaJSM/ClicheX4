"""작은 머리 전체64격자 직접 양자화와 전후 측면머리 소유 등록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
def main():
    d=H/'vehicle_head_ultimate_native01';need(not d.exists(),'등록 보호');d.mkdir();src=H/'vehicle_head_ultimate_inputs01';parent=H/'prepared_hover_ultimate01/PL02_U.ARC';a=Archive(parent.read_bytes())
    rgba=np.array(Image.open(src/'generated_v1.png').convert('RGBA').resize((64,64),Image.Resampling.NEAREST));table=np.array(a.rgba(np.arange(16,dtype=np.uint8).reshape(1,16)))[0,:,:3].astype('int32');dist=((rgba[:,:,:3,None].transpose(0,1,3,2).astype('int32')-table[None,None,1:])**2).sum(3);idx=(dist.argmin(2)+1).astype('uint8');idx[rgba[:,:,3]<128]=0
    Image.fromarray(rgba).save(d/'whole64_rgba.png');Image.fromarray(idx).save(d/'whole64_indices.png');base=np.zeros((384,384),np.uint8);base[101:165,125:189]=idx;old=a.layer(184,0)[0];oldhead=a.layer(184,5)[0];oldalpha=np.array(a.composite(184,0)[0])[:,:,3]>0;newalpha=base>0
    need(metrics(a.rgba(base))['bbox']==[-10,-37,3,-22],'전체 크기/원점');need(base[135,156]==7,'홍채 색인/좌표');need(int(newalpha.sum())==144,'머리 픽셀 수')
    # 기존 측면 머리 소유창 안의 새 보라색 머리만 before의 파랑4로 표시한다.
    # 새 공통 금색 고글이 들어선1셀은 overlay로 덮지 않는다.
    owner=(oldhead>0)&(base==2);head=np.zeros_like(base);head[owner]=4;need(int(owner.sum())==8,'측면 소유8셀');need(int(((oldhead>0)&~owner).sum())==1,'공통 고글로 바뀐1셀')
    after=a.rgba(base);before=after.copy();before.alpha_composite(a.rgba(head,16));after.save(d/'after184.png');before.save(d/'before184.png');Image.fromarray(base).save(d/'184_bank0_indices.png');Image.fromarray(head).save(d/'184_bank5_indices.png');Image.fromarray(owner.astype('uint8')*255).save(d/'side_hair_owner.png')
    bb=(147,120,167,141);board=Image.new('RGB',(1120,560),'#e8e6df');dr=ImageDraw.Draw(board)
    for row,(form,mask,new) in enumerate((('before',15,before),('after',0,after))):
        y=row*280;dr.text((10,y+4),f'Ultimate {form}: accepted idle | parent184 | new184 | 1x/2x small | internal golden goggles',fill='#202020')
        idle=a.composite(0,mask)[0].crop((143,132,177,157));up=idle.resize((340,250),Image.Resampling.NEAREST);board.paste(up,(4,y+26),up)
        for col,im in enumerate((a.composite(184,mask)[0],new)):
            p=im.crop(bb).resize((200,210),Image.Resampling.NEAREST);board.paste(p,(350+col*225,y+40),p)
        p=new.crop(bb);board.paste(p,(835,y+80),p);up=p.resize((40,42),Image.Resampling.NEAREST);board.paste(up,(875,y+75),up)
        # 동일 고정격자의 alpha 비교만 표시하며 원화에 적용하지 않는다.
        view=Image.new('RGB',(160,168),'#c8c6bd');pixels=view.load()
        for yy in range(21):
            for xx in range(20):
                wy,wx=120+yy,147+xx;v=oldalpha[wy,wx];n=newalpha[wy,wx];color='#67a86e' if v and n else '#db525b' if v else '#4c70db' if n else '#c8c6bd';ImageDraw.Draw(view).rectangle((xx*8,yy*8,xx*8+7,yy*8+7),fill=color)
        board.paste(view,(950,y+65))
    board.save(d/'comparison.png')
    overlays=[]
    for y,x in zip(*np.nonzero(oldhead)):
        overlays.append({'world':[int(x)-160,int(y)-160],'old_overlay':int(oldhead[y,x]),'new_base':int(base[y,x]),'new_overlay':int(head[y,x])})
    write(d/'registration.json',{'scope':'新Ultimate 탑승 머리1고정셀 직접등록. 현재19위치별칭 패킹 전 후보.','parent_sha256':sha(parent.read_bytes()),'generated_sha256':sha((src/'generated_v1.png').read_bytes()),'actual_source_size':[1254,1254],'whole_logical_grid':[64,64],'sampling':'NEAREST whole canvas; alpha >=128; actual CLUT0 opaque15 nearest RGB','translation':[0,0],'per_sprite_scaling':False,'old_head_or_face_overlaid':False,'head_bbox_world':metrics(after)['bbox'],'opaque':144,'eye_world':[-4,-25],'gold_index7_total':int((base==7).sum()),'body_unchanged':True,'alpha_exact':bool(np.array_equal(oldalpha,newalpha)),'alpha_added_world':[[int(x)-160,int(y)-160] for y,x in np.argwhere(newalpha&~oldalpha)],'alpha_removed_world':[[int(x)-160,int(y)-160] for y,x in np.argwhere(oldalpha&~newalpha)],'size_origin_eye_exact':True,'before_side_hair_overlay_cells':8,'old_side_hair_to_common_goggle_cells':1,'ownership_policy':'기존9셀측면머리소유창에서 새보라색2인8셀만 before파랑4로해석.새금색고글1셀은전후공통으로보존.머리전체변형/옛머리덮기없음.','owner_rows':overlays,'author_visual_review_pending':True,'root_art_review_pending':True,'packed':False,'source_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in [src/'generated_v1.png',src/'input_manifest.json',src/'generation.json',Path(__file__)]},'files':{p.name:sha(p.read_bytes()) for p in d.glob('*.png')}})
    print(json.dumps({'registration':sha((d/'registration.json').read_bytes()),'bbox':metrics(after),'alpha_added':np.argwhere(newalpha&~oldalpha).tolist(),'alpha_removed':np.argwhere(oldalpha&~newalpha).tolist()}))
if __name__=='__main__':main()
