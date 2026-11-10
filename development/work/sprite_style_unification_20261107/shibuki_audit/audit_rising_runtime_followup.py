"""실제 공중 발화 제보를 순정 US의 발사손·원래 초기화와 비교한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent; ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map,page
from src.psx_disc import file_hash
from audit_cyclone_contact import need,sha,write,translate
from audit_rising_fire_contact_probe import run

def bbox(mask):
    y,x=np.nonzero(mask)
    return [int(x.min())-160,int(y.min())-160,int(x.max())-159,int(y.max())-159] if len(x) else None

def main():
    out=H/'rising_runtime_followup01';out.mkdir(exist_ok=True)
    us=ROOT/'MegaMan X4.bin';need(file_hash(us)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','Wrong original US')
    original=read_disc(us,['PL00_U.ARC','SLUS_005.61'])[0];exe=original['SLUS_005.61'];a=Archive(original['PL00_U.ARC'])
    need(sha(a.data)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a','Original graphics changed')
    runtime=ROOT/'work/sprite_style_unification_20261107/runtime';watch=json.loads((runtime/'shibuki_rising10_watch/evidence.json').read_text('utf8'));play=json.loads((runtime/'shibuki_rising10_play/evidence.json').read_text('utf8'))
    live=read_disc(ROOT/watch['disc'],['SLUS_005.61','PL00_U.ARC','PL02_U.ARC'])[0]
    ranges=[(0x80037e4c,0x80037f78),(0x80039570,0x80039860),(0x800951c0,0x800957b0),(0x8010890c,0x80108944),(0x8011ba28,0x8011bb3c),(0x8011c0b0,0x8011c0c8)]
    off=lambda x:x-0x80010000+2048
    for lo,hi in ranges:need(exe[off(lo):off(hi)]==live['SLUS_005.61'][off(lo):off(hi)],'Runtime code/table differs')
    anims,_=animation_map(exe);selected=[q for q in anims if q['id'] in(99,100,101,102,103)]
    initial=[run(exe,a,False,s,f) for s in(0,1) for f in(0,64)]
    y,x=np.indices((384,384));x=x-160;y=y-160
    current={'base':(Archive(live['PL00_U.ARC']),0),'fourth':(Archive(live['PL00_U.ARC']),15),'ultimate_before':(Archive(live['PL02_U.ARC']),15),'ultimate_after':(Archive(live['PL02_U.ARC']),0)}
    pics=[];panels=[];rows=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
    for form,(b,mask)in current.items():
        for n in(103,104):pics.extend([(f'US X {n}',a.composite(n,0)[0]),(f'{form} {n}',b.composite(n,mask)[0])])
        for name,arc,am in [('original_us',a,0),(form,b,mask)]:
            im=arc.composite(104,am)[0];q=np.array(im)
            if name=='original_us':hand=(x>=0)&(x<=10)&(y<=-26)&(q[:,:,3]>0)
            else:hand=(x<-8)&(y<-22)&(q[:,:,3]>0)&(np.all(q[:,:,:3]==[255,222,189],2)|np.all(q[:,:,:3]==[238,164,131],2))
            need(hand.any(),'Raised hand mask empty');hy,hx=np.nonzero(hand)
            c=next(z for z in initial if(z['subtype'],z['facing'])==(1,0));effect=translate(a.layer(5,13,5)[0],*c['spawn_world'],False)
            ey,ex=np.nonzero(effect);d=float(np.sqrt(((np.column_stack([hy,hx])[:,None]-np.column_stack([ey,ex])[None])**2).sum(2).min()))
            row={'form':name,'ref':104,'raised_hand_bbox':bbox(hand),'raised_hand_x_mean':float(hx.mean()-160),'native_effect_origin':c['spawn_world'],'first_effect_nearest_hand_distance':d,'hand_alpha_overlap':int((hand&(effect>0)).sum())};rows.append(row)
            overlay=im.copy();color=np.zeros((384,384,4),np.uint8);color[effect>0]=[30,205,220,155];overlay.alpha_composite(Image.fromarray(color));crop=overlay.crop((124,116,196,188)).resize((360,360),Image.Resampling.NEAREST);panel=Image.new('RGB',(360,400),(27,32,43));panel.paste(crop,(0,40),crop);dr=ImageDraw.Draw(panel);dr.text((4,3),f'{name}104 / native air effect at(6,-12)',font=font,fill='white');dr.text((4,20),'cyan = actual original effect alpha occupancy',font=font,fill='white');panels.append(panel)
    page(pics,a.composite(0,0)[0],out/'original_vs_current_four_forms.png',cols=4,scale=4)
    board=Image.new('RGB',(720,1600),(27,32,43))
    for i,p in enumerate(panels):board.paste(p,(i%2*360,i//2*400))
    board.save(out/'original_effect_contact.png')
    delta=(int(play['record_start_monotonic_ns'])-int(watch['watch_start_monotonic_ns']))/1e9
    observed=[e|{'relative_recording_first_seen':e['first_seen_seconds']-delta}for e in watch['events']if e['frame']in(103,104,231,232)]
    report={'confirmed_art_defect':True,'scope':'일반 공중 라이징파이어 103/104 네 의상. 효과/시간표/성능 수정 없음.','source_us_bin_sha256':file_hash(us),'source_us_arc_sha256':sha(a.data),'runtime_bin_sha256':watch['disc_sha256'],'runtime_arc_sha256':{k:sha(v)for k,v in live.items()if k.endswith('.ARC')},'original_code_table_ranges_exact':[list(map(hex,r))for r in ranges],'native_initializers':initial,'original_player_animations':selected,'hand_comparisons':rows,'actual_runtime_events':observed,'clock_alignment_seconds':delta,'actual_window_reviewed':['jump_right_00.png','jump_right_again_00.png'],'finding':'순정 104는 x+2..+9 오른쪽 위 손을 올리고 원래 subtype1 화염도 x+6,y-12에 생성한다. 시부키는 기존부터 반대쪽 왼손을 올려 화염과 어긋났다. 최근 세밀화도 기존 손 위치를 보존하여 이 결함을 이어받았다.','previous_audit_limitation':'이전 검사는 수정 전 시부키와의 거리 비악화만 비교했다. 원US의 발사손 의미를 비교하지 않아 근본 결함을 놓쳤다. 원래 효과와 일치 검증을 통과했다고 확대해서는 안 된다.','correction_plan':'103 준비손과104 발사손을 올바른 쪽에서 연결하도록 네 의상 국소 재작화. 전신 반전/효과 이동/시간표 변경 금지. 머리·몸·발과 새 상세는 최대 보존.','limitations':['실제 동영상에 양손·효과가 확인되지만 개별 화염 RAM 객체는 이번 watcher가 수집하지 않았다.','청록 합성은 원래 초기화 위치의 공간 비교이며 실기 프레임 전체 재현이 아니다.','차지 상승 및 지상231/232는 별도 동작이며 이번 공중발사손 오류로 수정하지 않는다.'],'source_or_game_written':False}
    write(out/'report.json',report);print(json.dumps({'confirmed_art_defect':True,'hand_comparisons':rows,'clock_alignment':delta},ensure_ascii=False))
if __name__=='__main__':main()
