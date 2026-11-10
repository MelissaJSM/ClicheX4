"""Ultimate 새 전후98/99를 동일 native 발원점·원효과 마스크에 대조한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from audit_cyclone_contact import run,translate,need,sha,write,SOURCE,SOURCE_SHA
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_disc import file_hash
def main():
    o=H/'double_cyclone_ultimate_contact01';need(not o.exists(),'Fresh output required');o.mkdir();need(file_hash(SOURCE)==SOURCE_SHA,'Wrong BIN');e=read_disc(SOURCE,['SLUS_005.61'])[0]['SLUS_005.61'];a=Archive((H/'prepared_ultimate_wall01/PL02_U.ARC').read_bytes());b=Archive((H/'double_cyclone_ultimate_pack01/PL02_U.ARC').read_bytes());need(sha(b.data)=='dd6416c8840a1a0e5fd7ff4c73fe33b6ebd90e69b5f86f9be5f9671cc4d53c1d','Candidate changed')
    cases=[run(e,a,c,st,f)for c in(False,True)for st in((0,-128)if c else(0,1))for f in(0,64)];rows=[];panels=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
    for c in(False,True):
        cc=[s for s in cases if s['charged']==c and s['player_facing_flag']==0]
        for mask in(0,15):
            for n in(98,99):
                contact={}
                for version,arc in(('old',a),('new',b)):
                    im=arc.composite(n,mask)[0];pix=np.array(im);contacts=[]
                    for s in cc:
                        native,_=a.layer(s['initial_frame'],16,8);need(np.array_equal(native,b.layer(s['initial_frame'],16,8)[0]),'Effect changed');fx=translate(native,*s['spawn_world'],s['flip_x']);side='left'if s['spawn_world'][0]<0 else'right';hand=np.zeros((384,384),bool)
                        if side=='left':hand[148:164,134:146]=True
                        else:hand[148:164,177:186]=True
                        hand&=pix[:,:,3]>0;hp=np.column_stack(np.nonzero(hand));ep=np.column_stack(np.nonzero(fx));dist=float(np.sqrt(((hp[:,None,:]-ep[None,:,:])**2).sum(2).min()));contacts.append({'side':side,'overlap':int((hand&(fx>0)).sum()),'distance':dist})
                        rgba=np.zeros((384,384,4),np.uint8);rgba[fx>0]=[60,220,230,175];im.alpha_composite(Image.fromarray(rgba))
                    contact[version]=contacts;panel=Image.new('RGB',(380,374),(27,32,43));cut=im.crop((124,124,200,192)).resize((380,340),Image.Resampling.NEAREST);panel.paste(cut,(0,34),cut);dr=ImageDraw.Draw(panel);dr.text((6,3),f'{"charge"if c else"normal"} mask{mask:X} ref{n} {version}',font=font,fill='white');dr.text((6,18),'Native effect mask in diagnostic cyan',font=font,fill='white');panels.append(panel)
                for side in('left','right'):
                    old=next(s for s in contact['old']if s['side']==side);new=next(s for s in contact['new']if s['side']==side);need(new['distance']<=max(1,old['distance']),'New contact is farther');rows.append({'charged':c,'mask':mask,'ref':n,'side':side,'before':old,'after':new})
    board=Image.new('RGB',(1520,1496),(27,32,43))
    for i,p in enumerate(panels):board.paste(p,(i%4*380,i//4*374))
    board.save(o/'initial_effect_overlay.png');write(o/'report.json',{'passed':True,'source_exe_sha256':sha(e),'parent_sha256':sha(a.data),'candidate_sha256':sha(b.data),'native_initializer_cases':cases,'contact_cases':rows,'effect_rgb':'diagnostic cyan only; no runtime CLUT claim','native_effect_gfx8_parts16_preserved':True,'runtime_verified':False,'scope':'원래 초기화 MIPS 발원점/방향/참조를 실행한 뒤 실제 원효과 인덱스의 접점만 검증. 물리/화면 전체 재생 아님.'});print(json.dumps(rows))
if __name__=='__main__':main()
