"""기본/포스 작은머리의 요청된 내부 편집만 현재144alpha에 등록한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
def quant(a,rgba,start):
    rgb=np.array(a.rgba(np.arange(16,dtype=np.uint8).reshape(1,16),start))[0,:,:3].astype('int32');dist=((rgba[:,:,:3,None].transpose(0,1,3,2).astype('int32')-rgb[None,None,1:])**2).sum(3);out=(dist.argmin(2)+1).astype('uint8');out[rgba[:,:,3]<128]=0;return out
def main():
    d=H/'vehicle_head_base_native01';need(not d.exists(),'등록 보호');d.mkdir();src=H/'vehicle_head_base_inputs01';p=H/'prepared_nova_strike_base01/PL00_U.ARC';a=Archive(p.read_bytes());whole=np.array(Image.open(src/'generated_v1.png').convert('RGBA').resize((96,96),Image.Resampling.NEAREST));Image.fromarray(whole).save(d/'whole96_rgba.png');forms={};rows=[]
    for form,x,mask,start in (('base',14,0,0),('fourth',62,15,16)):
        # 25×27固定창은 source exterior도 진단에 남긴다. 그림별 bbox 확대/축소는 없다.
        cell=whole[32:59,x-6:x+19];idx=quant(a,cell,start);world=np.zeros((384,384),np.uint8);world[117:144,144:169]=idx;source_alpha=world>0;old=np.array(a.composite(184,mask)[0]);oldalpha=old[:,:,3]>0;need(not(oldalpha&~source_alpha).any(),'새 원화가 보호된머리안을 비웠음')
        wanted=world.copy();wanted[~oldalpha]=0;need(int((wanted>0).sum())==144 and wanted[135,156]==7,'크기/눈 보호');forms[form]=wanted;Image.fromarray(world).save(d/f'{form}_source_indices.png');Image.fromarray(wanted).save(d/f'{form}_registered_indices.png');a.rgba(wanted,start).save(d/f'{form}_184.png')
        extras=[[int(xx)-160,int(yy)-160,int(world[yy,xx])] for yy,xx in np.argwhere(source_alpha&~oldalpha)];rows.append({'form':form,'fixed_cell_source':[x-6,32,x+19,59],'world_placement':[144,117],'original_head_alpha_applied_to_new_source':True,'old_RGB_copied':False,'old_opaque_without_new_source':0,'out_of_scope_extra_source_pixels_not_adopted':extras,'expected_extra_count':3 if form=='base' else 5,'bbox_world':metrics(a.rgba(wanted,start))['bbox'],'opaque':144,'eye_world':[-4,-25]});need(len(extras)==rows[-1]['expected_extra_count'],'범위밖 외곽 진단')
    base=forms['base'];fourth=forms['fourth'];bg=np.array(a.rgba(base));fg=np.array(a.rgba(fourth,16));common=np.all(bg==fg,axis=2);head=np.where(common,0,fourth).astype('uint8');Image.fromarray(base).save(d/'184_bank0_indices.png');Image.fromarray(head).save(d/'184_bank5_indices.png');got=a.rgba(base);got.alpha_composite(a.rgba(head,16));need(got.tobytes()==a.rgba(fourth,16).tobytes(),'포스 합성 exact')
    board=Image.new('RGB',(1000,540),'#e8e6df');dr=ImageDraw.Draw(board)
    for row,(form,mask,start) in enumerate((('base',0,0),('fourth',15,16))):
        y=row*270;dr.text((10,y+4),f'{form}: accepted idle | parent13x15 | new inside original alpha13x15 | 1x/2x',fill='#202020');idle=a.composite(0,mask)[0].crop((143,132,177,157)).resize((340,250),Image.Resampling.NEAREST);board.paste(idle,(4,y+20),idle)
        new=a.rgba(forms[form],start)
        for col,im in enumerate((a.composite(184,mask)[0],new)):
            im=im.crop((147,120,167,141)).resize((200,210),Image.Resampling.NEAREST);board.paste(im,(350+col*225,y+40),im)
        im=new.crop((147,120,167,141));board.paste(im,(835,y+80),im);up=im.resize((40,42),Image.Resampling.NEAREST);board.paste(up,(885,y+75),up)
    board.save(d/'comparison.png');write(d/'registration.json',{'scope':'기본/포스 작은머리의 전체96격자 직접 양자화 후 요청된 내부편집만 기존144alpha에 등록.','source_parent_sha256':sha(p.read_bytes()),'packing_parent_pending_root_hover':True,'generated_sha256':sha((src/'generated_v1.png').read_bytes()),'actual_size':[1254,1254],'whole_logical_grid':[96,96],'method':'NEAREST whole canvas; alpha128; actual CLUT0/16 nearest opaque15 RGB. 기존alpha 안에 source모두존재하므로 옛RGB채움없음.','forms':rows,'full_target_RGBA_exact':True,'head5_delta_pixels':int((head>0).sum()),'gold_goggles_added':False,'resource_written':False,'root_review_pending':True,'source_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in [src/'generated_v1.png',src/'generation.json',src/'input_materials_v2.json',Path(__file__)]},'files':{p.name:sha(p.read_bytes()) for p in d.glob('*.png')}});print(json.dumps({'registration':sha((d/'registration.json').read_bytes()),'delta_head5':int((head>0).sum()),'forms':rows}))
if __name__=='__main__':main()
