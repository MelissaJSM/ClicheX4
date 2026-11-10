"""現동결 탑승 작은머리와 대기장식의 위치·색·공유를 읽는다. 아트변경 없음."""
from pathlib import Path
from collections import defaultdict
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
from src.psx_player import composition_frame,bank_offsets
PBS=(0,5,6,7,8);REFS=range(184,204)
def main():
    d=H/'vehicle_head_accessory_read01';need(not d.exists(),'새읽기폴더');paths={'base':H/'prepared_nova_strike_base01/PL00_U.ARC','ultimate':H/'prepared_nova_strike_ultimate01/PL02_U.ARC'};ars={k:Archive(p.read_bytes())for k,p in paths.items()};d.mkdir();forms=[('base','base',0),('fourth','base',15),('ultimate_before','ultimate',15),('ultimate_after','ultimate',0)];report=[];out=Image.new('RGB',(1000,4*260),'#eae9e4');dr=ImageDraw.Draw(out);allshares={}
    for kind,a in ars.items():
        owners=defaultdict(list)
        for pb in range(len(bank_offsets(a.c))):
            for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
                for p in composition_frame(a.c,pb,n)['parts']:owners[p['record_offset']].append([pb,n])
        rows=[]
        for n in REFS:
            f=a.banks[0]['frames'][n];layers=[]
            for pb in PBS:
                z,rec=a.layer(n,pb);layers.append({'bank':pb,'opaque':int((z>0).sum()),'index_counts':{str(v):int((z==v).sum())for v in np.unique(z)if v},'parts':rec['parts'],'outside_record_owners':{str(p['record_offset']):owners[p['record_offset']]for p in rec['parts']if any(not(b in PBS and nn in REFS)for b,nn in owners[p['record_offset']])}})
            rows.append({'ref':n,'raw_stream_offset':f['offset'],'tile_count':f['tile_count'],'raw_owners':[v['index']for v in a.banks[0]['frames']if v['offset']==f['offset']],'layers':layers})
        allshares[kind]=rows
    for row,(form,kind,mask)in enumerate(forms):
        a=ars[kind];im=a.composite(184,mask)[0];bb=im.getbbox();small=im.crop(bb);master=np.array(small);aliases=[];colors={};rgba=np.array(im);rgb,ct=np.unique(rgba[rgba[:,:,3]>0],axis=0,return_counts=True)
        for rgbv,c in zip(rgb,ct):colors[','.join(map(str,rgbv))]=int(c)
        for n in REFS:
            cur=a.composite(n,mask)[0];b=cur.getbbox()
            if n==198:need(b is None,'198빈상태변경');continue
            need(np.array_equal(np.array(cur.crop(b)),master),'작은머리 별도형상');aliases.append({'ref':n,'bbox_world':[v-160 for v in b],'delta_from184':[b[0]-bb[0],b[1]-bb[1]],'same_cropped_RGBA':True})
        small.save(d/f'{form}_small184.png');idle=a.composite(0,mask)[0];idle.save(d/f'{form}_idle0.png');head=idle.crop((143,132,177,157));head.save(d/f'{form}_idle_head_crop.png');dr.text((8,row*260+8),f'{form} / original 13x15 head; no resizing in resources',fill='#121212');out.paste(head.resize((272,200),Image.Resampling.NEAREST),(12,row*260+36),head.resize((272,200),Image.Resampling.NEAREST));out.paste(small.resize((130,150),Image.Resampling.NEAREST),(330,row*260+36),small.resize((130,150),Image.Resampling.NEAREST));out.paste(small,(488,row*260+42),small)
        # 4 pixel-high internal forehead rows are displayed as existing texels, not edited.
        for yy in range(small.height):
            for xx in range(small.width):
                col=master[yy,xx];x=540+xx*23;y=row*260+30+yy*14
                if col[3]:dr.rectangle((x,y,x+21,y+12),fill=tuple(col[:3]));dr.text((x+1,y),f'{a.layer(184,0)[0][bb[1]+yy,bb[0]+xx]:X}',fill='#000000')
        report.append({'form':form,'mask':mask,'metrics':metrics(im),'normalized_RGBA_sha256':sha(master.tobytes()),'distinct_colors':colors,'aliases':aliases,'opaque_198':0,'small_crop_sha256':sha((d/f'{form}_small184.png').read_bytes()),'idle_head_crop_world':[-17,-28,17,-3]})
    out.save(d/'four_forms_existing_head.png');write(d/'report.json',{'scope':'현재동결자원184..203의작은머리/대기 비교와전체조립소유 읽기.새원화·후보·패킹없음.','parents':{k:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for k,p in paths.items()},'forms':report,'raw_and_composition_ownership':allshares,'existing_production_rule':{'path':'scripts/register_shibuki_ultimate_production.py','sha256':sha((ROOT/'scripts/register_shibuki_ultimate_production.py').read_bytes()),'line':81,'rule':'당시 작은머리는 base색인4/10/11에 overlay4를 적용했다. 현재그림 전체가 이옛함수로만 재현됨을 아직증명하지 않음.'},'costume_reuse_history':{'path':'scripts/overhaul_sprites_costume.py','sha256':sha((ROOT/'scripts/overhaul_sprites_costume.py').read_bytes()),'line':130,'rule':'옛Ultimate후폼 작업에서 탑승머리는 재킷없음을 이유로 기존머리재사용.'},'files':{p.name:sha(p.read_bytes())for p in sorted(d.glob('*.png'))},'new_art_created':False,'resources_modified':False,'runtime_verified':False,'decision_pending_visual':True});print(json.dumps({'report':sha((d/'report.json').read_bytes()),'forms':[{k:q[k]for k in('form','metrics')}for q in report]}))
if __name__=='__main__':main()
