"""98/99의 실제 공유구조와 네 의상 입력을 준비한다. 새 아트/게임 쓰기 없음."""
from pathlib import Path
import json,sys,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from scripts.export_x_consistency import Archive,animation_map
from scripts.prepare_shibuki_ultimate_production import records
from scripts.c01_audio_build import read_disc
from native_pose_pack import need,sha,write,SOURCE,SOURCE_SHA
from src.psx_disc import file_hash

def main():
    o=H/'double_cyclone_inputs02';need(not o.exists(),'Fresh output required');o.mkdir();font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22)
    files={'PL00_U.ARC':H/'prepared_air01/PL00_U.ARC','PL02_U.ARC':H/'prepared_ultimate_wall01/PL02_U.ARC'};arcs={name:Archive(path.read_bytes())for name,path in files.items()}
    forms=[('base','PL00_U.ARC',0),('fourth','PL00_U.ARC',15),('ultimate_before','PL02_U.ARC',15),('ultimate_after','PL02_U.ARC',0)]
    pose=Image.new('RGBA',(1536,1024));idle=Image.new('RGBA',(1536,1024));review=Image.new('RGB',(1536,1024),(28,34,44));dr=ImageDraw.Draw(review);rows=[]
    for i,(form,name,mask)in enumerate(forms):
        a=arcs[name];im=a.composite(98,mask)[0];other=a.composite(99,mask)[0];eq=im.tobytes()==other.tobytes();shifted=np.roll(np.array(im),1,axis=1);difference=int(np.count_nonzero(np.any(shifted!=np.array(other),axis=2)));need(difference==(158 if form=='ultimate_after'else 0),'98/99 registration relationship changed')
        x=i%2*768;y=i//2*512;cut=im.crop((112,124,208,188));cut.resize((768,512),Image.Resampling.NEAREST).save(o/f'{form}_pose.png');a.composite(0,mask)[0].crop((112,124,208,188)).resize((768,512),Image.Resampling.NEAREST).save(o/f'{form}_idle.png')
        pose.alpha_composite(Image.open(o/f'{form}_pose.png'),(x,y));idle.alpha_composite(Image.open(o/f'{form}_idle.png'),(x,y));review.paste(Image.open(o/f'{form}_pose.png'),(x,y),Image.open(o/f'{form}_pose.png'));dr.text((x+16,y+8),form+' / current98',fill='white',font=font)
        arr=np.array(im);yy,xx=np.nonzero(arr[:,:,3]);off=a.banks[0]['frames'][98]['offset'];raw_refs=[q['index']for q in a.banks[0]['frames']if q['offset']==off]
        layers={str(pb):{'same_indexed':np.array_equal(a.layer(98,pb)[0],a.layer(99,pb)[0]),'same_part_records':records(a.c,pb,98)==records(a.c,pb,99),'parts98':len(records(a.c,pb,98))//4,'parts99':len(records(a.c,pb,99))//4}for pb in(0,5,6,7,8)}
        rows.append({'form':form,'arc':name,'mask':mask,'same_98_99_rgba':eq,'99_compared_to_98_shift_x1_changed_pixels':difference,'same_98_99_raw':a.banks[0]['frames'][99]['offset']==off,'raw_group':raw_refs,'layers':layers,'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'rgba_sha256':sha(im.tobytes())})
    pose.save(o/'pose_reference.png');idle.save(o/'idle_style_reference.png');review.save(o/'current_review.png')
    need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed');exe=read_disc(SOURCE,('SLUS_005.61',))[0]['SLUS_005.61'];anims,refs=animation_map(exe);selected=[q for q in anims if any(s['frame']in(98,99)for s in q['steps'])]
    for k in (0,1):
        pd=o/f'page{k+1:02}';pd.mkdir();p=Image.new('RGBA',(1536,1024));s=p.copy()
        for col,(form,_,_)in enumerate(forms[k*2:(k+1)*2]):
            p.alpha_composite(Image.open(o/f'{form}_pose.png'),(col*768,224));s.alpha_composite(Image.open(o/f'{form}_idle.png'),(col*768,224))
        p.save(pd/'pose_reference.png');s.save(pd/'idle_style_reference.png')
    write(o/'structure.json',{'source_bin_sha256':SOURCE_SHA,'source_executable_sha256':sha(exe),'arcs':{name:{'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes())}for name,path in files.items()},'forms':rows,'animations':selected,'known_translation':[1,0],'after_old_material_deviation_pixels':158,'reference_crop_world':[-48,-36,48,28],'page2pose_offset_px':[0,224],'scale':8,'source_art_changed':False,'generation_pending':True})
    print(json.dumps({'forms':rows,'animations':selected},ensure_ascii=False))
if __name__=='__main__':main()
