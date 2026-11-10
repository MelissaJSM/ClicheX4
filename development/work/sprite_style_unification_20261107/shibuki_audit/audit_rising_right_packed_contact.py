"""원US 공중 발원점/원효과와 새4의상 실제 재독출을 양방향으로 비교한다.

실제게임 재검증이 아닌 native initializer + 공간 합성 검사다.
"""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from src.psx_disc import file_hash
from src.psx_player import bank_offsets
from audit_cyclone_contact import need,sha,write,translate
from audit_rising_fire_contact_probe import run

def bbox(mask):
    yy,xx=np.nonzero(mask)
    return [int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)] if len(xx) else None
def components(v):
    remain=set(map(tuple,np.column_stack(np.nonzero(v))));sizes=[]
    while remain:
        todo=[remain.pop()];size=0
        while todo:
            y,x=todo.pop();size+=1
            for dy in(-1,0,1):
                for dx in(-1,0,1):
                    p=(y+dy,x+dx)
                    if p in remain:remain.remove(p);todo.append(p)
        sizes.append(size)
    return sorted(sizes,reverse=True)
def mirror_rgba(r):
    out=np.zeros_like(r)
    for c in range(4):out[:,:,c]=translate(r[:,:,c],0,0,True)
    return out
def main():
    out=H/'rising_right_packed_contact01';need(not out.exists(),'Fresh proof');out.mkdir()
    us=ROOT/'MegaMan X4.bin';need(file_hash(us)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','Wrong US source')
    original=read_disc(us,['PL00_U.ARC','SLUS_005.61'])[0];a=Archive(original['PL00_U.ARC']);exe=original['SLUS_005.61']
    oldb=Archive((H/'prepared_rising_fire_base02/PL00_U.ARC').read_bytes());oldu=Archive((H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes())
    newb=Archive((H/'rising_right_base_pack02/PL00_U.ARC').read_bytes());newu=Archive((H/'rising_right_ultimate_pack01/PL02_U.ARC').read_bytes())
    need(sha(newb.data)=='13a29023365419d32475cf5a6551adc4658116c8f03622d962d5b8071744e8b8','Wrong base candidate');need(sha(newu.data)=='d636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d','Wrong Ultimate candidate')
    cases=[run(exe,a,False,1,f)for f in(0,64)]
    forms=[('base',oldb,newb,0),('fourth',oldb,newb,15),('ultimate_before',oldu,newu,15),('ultimate_after',oldu,newu,0)]
    y,x=np.indices((384,384));x=x-160;y=y-160;rows=[];anchors=[];parts=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
    for form,old,new,mask in forms:
        gb0,gb1=old.banks[5],new.banks[5];need(old.g[gb0['base']:gb0['end']]==new.g[gb1['base']:gb1['end']],'Effect graphics bank changed')
        cb0=bank_offsets(old.c);cb1=bank_offsets(new.c);need(old.c[cb0[13]:cb0[14]]==new.c[cb1[13]:cb1[14]],'Effect composition changed')
        actual=np.array(new.composite(104,mask)[0]);oldrgba=np.array(old.composite(104,mask)[0]);skin=np.zeros(x.shape,bool)
        for color in([255,222,189],[238,164,131],[255,180,189],[238,123,131],[238,123,164]):skin|=np.all(actual[:,:,:3]==color,2)
        hand=skin&(actual[:,:,3]>0)&(x>=1)&(x<=8)&(y>=-33)&(y<=-25);need(hand.any(),'No right raised hand')
        for ref in(103,104):
            before=np.array(old.composite(ref,mask)[0]);after=np.array(new.composite(ref,mask)[0]);ny=np.nonzero(after[:,:,3])[0].max();oy=np.nonzero(before[:,:,3])[0].max()
            nx=np.nonzero(after[ny,:,3])[0];ox=np.nonzero(before[oy,:,3])[0]
            sizes=components(after[:,:,3]>0);need(len(sizes)==1,'New disconnected body')
            need(ny==184,'New sole y differs from common world24')
            # Fourth old104 contained a one-pixel lower footwear fringe; align
            # to common base body/current Ultimate soles instead of retaining it.
            need(abs(float(nx.mean()-ox.mean()))<=1,'Sole horizontal anchor drift')
            anchors.append({'form':form,'ref':ref,'new_sole_y':int(ny-160),'old_sole_y':int(oy-160),'new_sole_x_mean':float(nx.mean()-160),'old_sole_x_mean':float(ox.mean()-160),'connected_body_sizes':sizes,'intentional_old_fourth_fringe_removed':bool(form=='fourth'and ref==104 and oy==185)})
        for c in cases:
            flip=bool(c['facing']);r=mirror_rgba(actual)if flip else actual.copy();hm=translate(hand.astype(np.uint8),0,0,flip)>0
            effect=translate(a.layer(c['initial_ref'],13,5)[0],*c['spawn_world'],c['flip_x']);overlap=int((hm&(effect>0)).sum());need(overlap>0,'Raised hand misses native initial flame')
            rows.append({'form':form,'facing':c['facing'],'native_effect_origin':c['spawn_world'],'native_effect_flip':c['flip_x'],'hand_bbox':bbox(hm),'hand_effect_overlap_pixels':overlap,'effect_graphics_composition_exact':True})
            color=np.zeros((384,384,4),np.uint8);color[effect>0]=[35,210,220,140];combined=Image.fromarray(r);combined.alpha_composite(Image.fromarray(color))
            crop=combined.crop((124,116,196,188)).resize((360,360),Image.Resampling.NEAREST);panel=Image.new('RGB',(360,406),(27,32,43));panel.paste(crop,(0,46),crop);dr=ImageDraw.Draw(panel);dr.text((5,4),f'{form}104 facing{c["facing"]}',font=font,fill='white');dr.text((5,24),f'native origin{c["spawn_world"]}; overlap {overlap}',font=font,fill='white');parts.append(panel)
    board=Image.new('RGB',(720,1624),(27,32,43))
    for i,p in enumerate(parts):board.paste(p,(i%2*360,i//2*406))
    board.save(out/'four_forms_native_effect_overlay.png')
    oldproof=json.loads((H/'rising_runtime_followup01/report.json').read_text('utf8'))
    write(out/'report.json',{'passed':True,'scope':'원US initializer4방향 중 공중2방향 실제MIPS 실행 + 네의상104 재독출 공간겹침. 실제게임연속실기는별도.','source_us_bin_sha256':file_hash(us),'candidate_sha256':{'PL00_U.ARC':sha(newb.data),'PL02_U.ARC':sha(newu.data)},'native_initializers':cases,'contact_cases':rows,'anchors':anchors,'alpha_source_registration':{'path':'rising_right_hand_native05/report.json','sha256':sha((H/'rising_right_hand_native05/report.json').read_bytes()),'remaining_enclosed_air_pixels':'원화224에도 존재하는 올린팔과 귀 사이의 공기 틈. 임의채움0. source alpha240 손실37픽셀은복원함.'},'existing_actual_runtime_defect_proof_sha256':sha((H/'rising_runtime_followup01/report.json').read_bytes()),'player_animation_table_unchanged_from_source':'resources-only patch; previous original/v10 EXE range proof remains applicable','normal_ground_231232_and_charge100101102_exact':True,'old_comparison_limitation':oldproof['previous_audit_limitation'],'not_claimed':['full GPU game scene simulation','physics or moving-fire phase timing','fresh emulator confirmation of this candidate'],'native_cpu_initializer':True,'emulator_gameplay_verified':False,'user_accepted':False});print(json.dumps({'contact':rows,'anchors':anchors}))
if __name__=='__main__':main()
