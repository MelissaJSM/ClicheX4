"""패킹된 네 폼의 초기 화염 위치를 원래 MIPS 초기화와 대조한다.

차지 이펙트는 공간 진단이며 플레이어/효과의 상대 프레임 위상을 재현하지 않는다.
"""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.export_sprite_playback import parse_sequence
from audit_rising_fire_contact_probe import run
from audit_cyclone_contact import translate,SOURCE,SOURCE_SHA,need,sha,write
from src.psx_disc import file_hash
def flipped(im):
    q=np.array(im);return Image.fromarray(np.stack([translate(q[:,:,c],0,0,True)for c in range(4)],2))
def main():
    o=H/'rising_packed_contact02';need(not o.exists(),'Fresh output required');o.mkdir();need(file_hash(SOURCE)==SOURCE_SHA,'Wrong immutable baseline')
    exe=read_disc(SOURCE,['SLUS_005.61'])[0]['SLUS_005.61'];oldexe=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.exe').read_bytes()
    ranges=[(0x800951c0,0x800957b0),(0x8010890c,0x80108944),(0x8011ba28,0x8011bb3c),(0x8011c0b0,0x8011c0c8)]
    for lo,hi in ranges:need(exe[lo-0x80010000+2048:hi-0x80010000+2048]==oldexe[lo-0x80010000+2048:hi-0x80010000+2048],'Native effect code changed')
    cases=[];contacts=[];images=[];sources={};font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
    for typ,name,parent,candidate,expected in[
        ('base','PL00_U.ARC','prepared_double_cyclone_base01','rising_base_pack_probe01','5e6b8be38f59413938b8515c227b3142a06d4af4c9378645fb696ea145b47a3e'),
        ('ultimate','PL02_U.ARC','prepared_double_cyclone_ultimate01','rising_ultimate_pack_probe01','71d02fe6d965c1fb42cc786766bad62372c792ccd8ecf6d5bc1e40dc8deb8597')]:
        a=Archive((H/parent/name).read_bytes());b=Archive((H/candidate/name).read_bytes());need(sha(b.data)==expected,'Candidate changed');sources[typ]={'parent':sha(a.data),'candidate':sha(b.data)}
        cc=[run(exe,b,c,s,f)for c in(False,True)for s in(0,1)for f in(0,64)];cases.extend([q|{'archive':name}for q in cc])
        forms=[('base',0),('fourth',15)]if typ=='base'else[('ultimate_before',15),('ultimate_after',0)]
        for form,mask in forms:
            panels=[]
            for charged,subtype,ref in[(False,0,232),(False,1,104),(True,0,100),(True,1,101)]:
                for facing in(0,64):
                    c=next(q for q in cc if(q['charged'],q['subtype'],q['facing'])==(charged,subtype,facing));seq=parse_sequence(exe,0x8011c0b0,c['animation'])
                    effectrefs=list(dict.fromkeys(s['frame_ref']for s in seq['steps']));sample=next(n for n in effectrefs if b.layer(n,13,5)[0].any())
                    for n in effectrefs:need(np.array_equal(a.layer(n,13,5)[0],b.layer(n,13,5)[0]),'Effect changed')
                    eff=translate(b.layer(sample,13,5)[0],*c['spawn_world'],c['flip_x']);ep=np.column_stack(np.nonzero(eff))
                    for version,arc in(('parent',a),('candidate',b)):
                        im=arc.composite(ref,mask)[0];im=flipped(im)if facing else im;pix=np.array(im);yy,xx=np.indices(pix.shape[:2]);skin=np.isin(pix[:,:,3],[255])&((np.all(pix[:,:,:3]==[238,164,131],2))|(np.all(pix[:,:,:3]==[255,222,189],2)))
                        # Grounded232 has its own lower fist; the airborne104
                        # hand envelope must not exclude the ground pose skin.
                        hand_bottom=148 if ref==232 else 142
                        skin&=(xx>168 if facing else xx<152)&(yy<hand_bottom);sp=np.column_stack(np.nonzero(skin));distance=float(np.sqrt(((sp[:,None,:]-ep[None,:,:])**2).sum(2).min()))if len(sp)else None
                        row={'form':form,'mask':mask,'ref':ref,'charged':charged,'subtype':subtype,'facing':facing,'version':version,'effect_ref':sample,'fist_skin_pixels':int(skin.sum()),'skin_effect_distance':distance,'skin_effect_overlap':int((skin&(eff>0)).sum()),'whole_body_effect_overlap':int(((pix[:,:,3]>0)&(eff>0)).sum())};contacts.append(row)
                        if facing:continue
                        overlay=im.copy();rgba=np.zeros((384,384,4),np.uint8);rgba[eff>0]=[45,220,235,180];overlay.alpha_composite(Image.fromarray(rgba));crop=overlay.crop((120,104,200,192)).resize((320,352),Image.Resampling.NEAREST);p=Image.new('RGB',(320,390),(27,32,43));p.paste(crop,(0,38),crop);d=ImageDraw.Draw(p);d.text((4,2),f'{form} {ref} {version} / effect{sample}',font=font,fill='white');d.text((4,19),'cyan occupancy; charged phase not simulated',font=font,fill='white');panels.append(p)
            board=Image.new('RGB',(640,1560),(27,32,43))
            for i,p in enumerate(panels):board.paste(p,(i%2*320,i//2*390))
            path=o/f'{form}_spatial.png';board.save(path);images.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':sha(path.read_bytes())})
    normal=[]
    for row in contacts:
        if row['charged']or row['version']!='candidate':continue
        old=next(r for r in contacts if r['version']=='parent'and all(r[k]==row[k]for k in('form','ref','charged','subtype','facing')))
        passed=row['skin_effect_distance']is not None and row['skin_effect_distance']<=max(1,old['skin_effect_distance']);normal.append({'passed':passed,'parent':old,'candidate':row})
    write(o/'report.json',{'passed':all(r['passed']for r in normal),'source_exe_sha256':sha(exe),'sources':sources,'native_initializer_cases':cases,'normal_initial_contact_checks':normal,'contacts':contacts,'images':images,'limitations':['원래 MIPS 초기화/애니메이션 설정16조건 실행. draw/외부 생성 호출은 격리.','일반 지상232/공중104는 원래 발사 참조의 첫 효과 접점이다.','차지100/101은 공간 검사이며 상대 갱신 위상/물리 재생을 입증하지 않는다.','청록색은 점유영역 진단 표시이며 실제 무기 CLUT 색상이 아니다.'],'native_gameplay_test':False,'no_game_or_exe_writes':True})
    print(json.dumps({'passed':all(r['passed']for r in normal),'normal':[(r['candidate']['form'],r['candidate']['ref'],r['candidate']['facing'],r['parent']['skin_effect_distance'],r['candidate']['skin_effect_distance'])for r in normal]}))
if __name__=='__main__':main()
