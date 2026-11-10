"""원화의 손/권총을 목표 위치에 강체 배치한 새 팔 그리기 입력. 최종 그림 아님."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write
# Source sleeve semantic polygons deliberately stop BEFORE braid / green neck ornament.
CONFIG={
68:{'shift':(-5,0),'module_x':103,'cut':[(0,102),(80,102),(101,126),(177,144),(200,143),(201,188),(0,190)]},
70:{'shift':(-4,2),'module_x':100,'cut':[(0,100),(80,100),(102,126),(166,144),(199,141),(199,179),(0,188)]},
72:{'shift':(-5,-2),'module_x':170,'cut':[(0,145),(125,145),(165,184),(258,201),(300,214),(350,214),(350,260),(0,271)]},
76:{'shift':(-3,-3),'module_x':177,'cut':[(0,130),(128,130),(171,179),(273,198),(322,209),(379,211),(379,257),(0,266)]},
78:{'shift':(-8,-3),'module_x':82,'cut':[(0,80),(74,80),(82,102),(135,111),(155,114),(155,150),(0,155)]},
80:{'shift':(-4,-2),'module_x':82,'cut':[(0,80),(72,80),(84,102),(143,113),(178,114),(178,150),(0,158)]},
82:{'shift':(-6,2),'module_x':81,'cut':[(0,96),(71,96),(84,117),(144,119),(178,120),(178,151),(0,161)]},
84:{'shift':(-6,2),'module_x':82,'cut':[(0,94),(73,94),(84,116),(144,117),(179,119),(179,151),(0,157)]}}
def folder(n):return'basic_firing_a_registered_v1'if n<72 else'basic_firing_lowreach_registered_v1'if n<78 else'basic_firing_b_registered_v1'
def main():
    out=D/'arm_reach_edit_inputs_v1';need(not out.exists(),'Fresh output');out.mkdir();plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());proof=[];edited=[];original=[]
    for n,cfg in CONFIG.items():
        parent=D/folder(n);r=next(r for r in json.loads((parent/'registration.json').read_text('utf8'))['frames']if r['ref']==n);im=Image.open(parent/f'source_{n:03}.png').convert('RGBA');ar=np.array(im);cut=Image.new('L',im.size);ImageDraw.Draw(cut).polygon(cfg['cut'],fill=255);mask=np.array(cut)>0
        # Translate just hand, pistol and cuff. Body, face and proximal shoulder remain exact.
        dx=round(cfg['shift'][0]*im.width/r['native_width']);dy=round(cfg['shift'][1]*(im.height-r['split'])/r['height_below']);module=ar.copy();Y,X=np.indices(ar.shape[:2]);module[~(mask&(X<=cfg['module_x'])),3]=0;rest=ar.copy();rest[mask,3]=0
        ox=140;oy=70;canvas=Image.new('RGBA',(im.width+280,im.height+140));canvas.alpha_composite(Image.fromarray(rest),(ox,oy));canvas.alpha_composite(Image.fromarray(module),(ox+dx,oy+dy));canvas.save(out/f'target_{n:03}.png')
        old=Image.new('RGBA',canvas.size);old.alpha_composite(im,(ox,oy));old.save(out/f'source_{n:03}.png');edited.append((n,canvas));original.append((n,old));cut.save(out/f'edit_mask_{n:03}.png');proof.append({'ref':n,'source':(parent/f'source_{n:03}.png').relative_to(ROOT).as_posix(),'source_sha256':digest(parent/f'source_{n:03}.png'),'semantic_cut_source':cfg['cut'],'forearm_module_max_x':cfg['module_x'],'native_shift':cfg['shift'],'rigid_source_shift':[dx,dy],'source_body_unchanged_outside_cut':True,'input_only':True})
    def page(items,path):
        sheet=Image.new('RGBA',(1536,1536));d=ImageDraw.Draw(sheet)
        for k,(n,im) in enumerate(items):
            scale=min(700/im.width,680/im.height);size=tuple(round(v*scale)for v in im.size);p=im.resize(size,Image.Resampling.NEAREST);xy=(k%2*768+(768-p.width)//2,k//2*768+(768-p.height)//2);sheet.alpha_composite(p,xy)
        sheet.save(path)
    for i in range(2):page(edited[i*4:i*4+4],out/f'target_{i+1}.png');page(original[i*4:i*4+4],out/f'detail_{i+1}.png')
    write(out/'manifest.json',{'frames':proof,'scope':'builtin 국소 편집용 접점 입력. 빈 구간은 새 상완/팔꿈치를 그릴 자리. 이 합성 입력을 최종 스프라이트로 사용하지 않음.','native_packed':False});print(str(out))
if __name__=='__main__':main()
