"""원화 고글의 금색 표본을 기존 금색 팔레트에 의미등록. 새 픽셀/색 추가 없음."""
from pathlib import Path
import sys,json,colorsys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
def main():
    src=H/'vehicle_head_ultimate_native01';d=H/'vehicle_head_ultimate_native02';need(not d.exists(),'등록 보호');d.mkdir();a=Archive((H/'prepared_hover_ultimate01/PL02_U.ARC').read_bytes());rgba=np.array(Image.open(src/'whole64_rgba.png'));idx=np.array(Image.open(src/'whole64_indices.png'));rows=[]
    for y in range(28,30):
        for x in range(27,36):
            rgb=rgba[y,x,:3];h,s,v=colorsys.rgb_to_hsv(*(rgb.astype(float)/255))
            if 28<=h*360<=50 and s>=.25 and v>=.55:
                rows.append({'logical':[x,y],'world':[x-35,y-59],'source_RGB':list(map(int,rgb)),'hue':h*360,'saturation':s,'nearest_index':int(idx[y,x]),'gold_index':7});idx[y,x]=7
    need(len(rows)==10 and sum(r['nearest_index']!=7 for r in rows)==5,'고글 표본10/추가5')
    base=np.zeros((384,384),np.uint8);base[101:165,125:189]=idx;head=np.array(Image.open(src/'184_bank5_indices.png'));oldbase=np.array(Image.open(src/'184_bank0_indices.png'));need(np.array_equal(base>0,oldbase>0),'외곽 보호');need(base[135,156]==oldbase[135,156]==7,'눈 보호')
    Image.fromarray(idx).save(d/'whole64_indices.png');Image.fromarray(base).save(d/'184_bank0_indices.png');Image.fromarray(head).save(d/'184_bank5_indices.png');after=a.rgba(base);before=after.copy();before.alpha_composite(a.rgba(head,16));after.save(d/'after184.png');before.save(d/'before184.png')
    board=Image.new('RGB',(1000,540),'#e8e6df');dr=ImageDraw.Draw(board)
    for row,(form,mask,new) in enumerate((('before',15,before),('after',0,after))):
        y=row*270;dr.text((10,y+4),f'Ultimate {form}: idle | parent13x15 | source-gold registered13x15 | 1x/2x',fill='#202020');idle=a.composite(0,mask)[0].crop((143,132,177,157)).resize((340,250),Image.Resampling.NEAREST);board.paste(idle,(4,y+20),idle)
        for col,im in enumerate((a.composite(184,mask)[0],new)):
            p=im.crop((147,120,167,141)).resize((200,210),Image.Resampling.NEAREST);board.paste(p,(350+col*225,y+40),p)
        p=new.crop((147,120,167,141));board.paste(p,(835,y+80),p);up=p.resize((40,42),Image.Resampling.NEAREST);board.paste(up,(885,y+75),up)
    board.save(d/'comparison.png');r=json.loads((src/'registration.json').read_text('utf8'));r.update(scope='Ultimate 작은 머리의 원화 금색 표본 의미등록 후보. 첫 직접양자화 결과와 별도 보존.',gold_sample_rule={'roi_logical':[27,28,36,30],'hue_degrees':[28,50],'minimum_saturation':.25,'minimum_value':.55,'palette_index':7,'samples':rows,'changed_from_nearest':5,'new_palette_colors':0,'pixels_added_or_removed':0},gold_index7_total=int((base==7).sum()),source_registration_sha256=sha((src/'registration.json').read_bytes()),source_files={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in [src/'registration.json',src/'whole64_rgba.png',src/'whole64_indices.png',src/'184_bank0_indices.png',src/'184_bank5_indices.png',Path(__file__)]},files={p.name:sha(p.read_bytes()) for p in d.glob('*.png')});write(d/'registration.json',r);print(json.dumps({'registration':sha((d/'registration.json').read_bytes()),'gold_samples':len(rows),'changed':5,'total_gold':int((base==7).sum())}))
if __name__=='__main__':main()
