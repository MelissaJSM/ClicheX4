"""오른쪽 발사손 후보와 원래 공중 화염의 최초 점유 교차검사. 연속실기 아님."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from audit_cyclone_contact import need,sha,write,translate
def main():
    out=H/'rising_right_hand_native01';a=Archive((H/'prepared_rising_fire_base02/PL00_U.ARC').read_bytes());o=Archive(read_disc(ROOT/'MegaMan X4.bin',['PL00_U.ARC'])[0]['PL00_U.ARC']);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);panels=[];rows=[];yy,xx=np.indices((384,384));effect=translate(o.layer(5,13,5)[0],6,-12,False)
    for form,mask,pal in [('base',0,0),('fourth',15,16)]:
        for version,im in [('originalUS',o.composite(104,0)[0]),('current_wrong_hand',a.composite(104,mask)[0]),('fresh_right_hand',Image.open(out/f'{form}_104.png').convert('RGBA'))]:
            r=np.array(im);skin=(r[:,:,3]>0)&(yy<139)
            if version=='originalUS':skin&=(xx>=160)&(yy<135)
            else:skin&=(np.all(r[:,:,:3]==[255,222,189],2)|np.all(r[:,:,:3]==[238,164,131],2))
            ey,ex=np.nonzero(effect);py,px=np.nonzero(skin);distance=float(np.sqrt(((np.column_stack([py,px])[:,None]-np.column_stack([ey,ex])[None])**2).sum(2).min()))
            rows.append({'form':form,'version':version,'hand_bbox':[int(px.min()-160),int(py.min()-160),int(px.max()+1-160),int(py.max()+1-160)],'hand_x_mean':float(px.mean()-160),'distance':distance,'effect_hand_overlap_pixels':int((skin&(effect>0)).sum())})
            color=np.zeros((384,384,4),np.uint8);color[effect>0]=[35,220,220,120];combined=im.copy();combined.alpha_composite(Image.fromarray(color));crop=combined.crop((128,108,192,192)).resize((320,420),Image.Resampling.NEAREST);board=Image.new('RGB',(320,460),(27,32,43));board.paste(crop,(0,40),crop);dr=ImageDraw.Draw(board);dr.text((4,3),f'{form}104 {version}',font=font,fill='white');dr.text((4,21),f'hand/effect d={distance:.2f}; xmean={px.mean()-160:.2f}',font=font,fill='white');panels.append(board)
    canvas=Image.new('RGB',(960,920),(27,32,43))
    for i,p in enumerate(panels):canvas.paste(p,(i%3*320,i//3*460))
    canvas.save(out/'original_effect_comparison.png');write(out/'effect_contact.json',{'passed_spatial':all(r['effect_hand_overlap_pixels']>0 for r in rows if r['version']=='fresh_right_hand'),'cases':rows,'runtime_or_sequence':False,'registration_and_partial_armor_pending':True,'height_note':'원US장갑보다 작은 시부키 주먹. 새손의위쪽-25는 기존시부키-27보다2px낮아 추가미술검토 필요.'});print(json.dumps(rows))
if __name__=='__main__':main()
