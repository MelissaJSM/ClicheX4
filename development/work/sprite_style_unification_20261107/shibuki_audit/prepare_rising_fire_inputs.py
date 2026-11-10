"""수용된 라이징파이어6자세/232흔들림과 네 폼의 미술 입력을 준비한다."""
from pathlib import Path
import sys,struct,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map,page,metrics
from native_pose_pack import need,sha,write,SOURCE,SOURCE_SHA
from src.psx_disc import file_hash

def main():
    o=H/'rising_fire_inputs01';need(not o.exists(),'Fresh output required');o.mkdir();need(file_hash(SOURCE)==SOURCE_SHA,'Wrong base BIN');exe=read_disc(SOURCE,['SLUS_005.61'])[0]['SLUS_005.61'];need(sha(exe)=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616','Wrong EXE');origexe=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.exe').read_bytes();off=lambda p:p-0x80010000+2048
    ranges=[(0x80037e4c,0x80037f78),(0x80039570,0x80039860)]
    for start,end in ranges:need(exe[off(start):off(end)]==origexe[off(start):off(end)],'Player rising-fire code changed')
    oldarc=read_disc(ROOT/'MegaMan X4.bin',['PL00_U.ARC'])[0]['PL00_U.ARC'];need(sha(oldarc)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a','Wrong original archive');original=Archive(oldarc)
    paths={'PL00_U.ARC':H/'prepared_double_cyclone_base01/PL00_U.ARC','PL02_U.ARC':H/'prepared_double_cyclone_ultimate01/PL02_U.ARC'};arcs={k:Archive(p.read_bytes())for k,p in paths.items()};expected={'PL00_U.ARC':'61495a2aaf002efc32492a4e12c3724a77c82b3f42464538ae1e2cc855da74c0','PL02_U.ARC':'dd6416c8840a1a0e5fd7ff4c73fe33b6ebd90e69b5f86f9be5f9671cc4d53c1d'}
    for name,a in arcs.items():need(sha(a.data)==expected[name],'Current parent changed')
    refs=[100,101,102,103,104,231,232];forms=[('base','PL00_U.ARC',0),('fourth','PL00_U.ARC',15),('ultimate_before','PL02_U.ARC',15),('ultimate_after','PL02_U.ARC',0)];rows=[]
    for form,name,mask in forms:
        a=arcs[name];page([(f'{n} current',a.composite(n,mask)[0])for n in refs],a.composite(0,mask)[0],o/f'{form}_review.png',cols=3,scale=4)
        for n in refs:
            offset=a.banks[0]['frames'][n]['offset'];group=[f['index']for f in a.banks[0]['frames']if f['offset']==offset];im=a.composite(n,mask)[0];arr=np.array(im);yy,xx=np.nonzero(arr[:,:,3]);raised=(arr[:,:,3]>0)&(np.indices(arr.shape[:2])[1]<155)&(np.indices(arr.shape[:2])[0]<148);hy,hx=np.nonzero(raised)
            rows.append({'form':form,'ref':n,'raw_aliases':group,'metrics':metrics(im),'upper_left_hand_region_bbox':([int(hx.min()-160),int(hy.min()-160),int(hx.max()+1-160),int(hy.max()+1-160)]if len(hx)else None),'note':'왼상단 후보 영역은 주먹/소매/머리를 함께 포함할 수 있으므로 의미별 최종 접점은 실제효과로 검증한다.'})
    pageinfo=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19)
    for pair,fs in enumerate((forms[:2],forms[2:])):
        for group,rr in enumerate(([100,101,102],[103,104,231])):
            index=pair*2+group+1;d=o/f'page{index:02}';d.mkdir();pose=Image.new('RGBA',(1536,1024));idle=pose.copy();detail=pose.copy();review=Image.new('RGB',(1536,1024),(27,32,43));dr=ImageDraw.Draw(review);slots=[]
            for row,(form,name,mask)in enumerate(fs):
                a=arcs[name]
                for col,n in enumerate(rr):
                    ox,oy=col*512,row*512
                    for board,ref in((pose,n),(idle,0),(detail,98)):
                        im=a.composite(ref,mask)[0];box=(128,124,192,188);outside=np.array(im)[:,:,3].copy();outside[124:188,128:192]=0;need(not outside.any(),'Input crop clips pose');small=im.crop(box).resize((512,512),Image.Resampling.NEAREST);board.alpha_composite(small,(ox,oy))
                    im=pose.crop((ox,oy,ox+512,oy+512));review.paste(im,(ox,oy),im);dr.text((ox+8,oy+8),f'{form} / {n}',fill='white',font=font);slots.append({'form':form,'ref':n,'page_origin':[ox+256,oy+288],'palette':16 if mask else 0,'crop_world':[-32,-36,32,28],'scale':8})
            pose.save(d/'pose_reference.png');idle.save(d/'idle_reference.png');detail.save(d/'accepted_new98_detail.png');review.save(d/'layout_review.png');pageinfo.append({'page':index,'slots':slots})
    anims,_=animation_map(exe);selected=[a for a in anims if any(s['frame']in refs for s in a['steps'])];need([a['id']for a in selected]==[99,100,101,102,103],'Animation domain changed')
    comparison=[]
    for form,name,mask in forms:
        a=arcs[name];x=np.array(a.composite(231,mask)[0]);y=np.array(a.composite(232,mask)[0]);comparison.append({'form':form,'accepted_231_to232_translation':[0,1],'current_rgba_difference_after_translation':int(np.any(np.roll(x,1,axis=0)!=y,axis=2).sum())})
    source_diff={str(pb):int((np.roll(original.layer(231,pb)[0],1,axis=0)!=original.layer(232,pb)[0]).sum())for pb in(0,5,6,7,8)}
    write(o/'structure.json',{'source_bin_sha256':SOURCE_SHA,'source_exe_sha256':sha(exe),'resources':{k:{'path':p.relative_to(ROOT).as_posix(),'sha256':expected[k]}for k,p in paths.items()},'refs':refs,'new_art_keys':[100,101,102,103,104,231],'derived232':{'basis':'현재 수용된 기본231→232의 1px 하강 관계를 네 폼에 통일. 순정X 두포즈가 같았다는 주장이 아님.','translation':[0,1],'actual_current_comparison':comparison,'original_us_index_differences_after_y1':source_diff,'original_us_arc_sha256':sha(oldarc)},'forms':rows,'pages':pageinfo,'animations':selected,'player_native_code_ranges_original_exact':[list(map(hex,q))for q in ranges],'motion_roles':{'99':'일반 라이징파이어 지상','100':'일반 라이징파이어 공중','101':'차지 지상 시작/상승','102':'차지 공중 시작/상승','103':'차지 상승 이후 별도 복귀'},'limitations':['물리·충돌·event에 따른 종료를 실제게임에서 검증한 자료 아님.','231/232는 수용본 동작 관계 유지이며 원작 포즈 복원 아님.','신원화 아직 생성하지 않음; 기존 전체도트 단순 리사이즈나 재색상 후보가 아님.'],'generation_pending':True})
    print(json.dumps({'pages':len(pageinfo),'new_keys':6,'forms':4,'source_original_differences':source_diff}))
if __name__=='__main__':main()
