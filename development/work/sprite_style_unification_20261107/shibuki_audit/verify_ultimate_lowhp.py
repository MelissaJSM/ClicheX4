"""재현·입력 거부·원시간표·32타일과 양방향 합성을 검증한다."""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from pack_ultimate_lowhp import pack,P,PSHA,O,SELECTED
from prepare_ultimate_lowhp_targets import targets
from native_pose_pack import sha,need,write,SOURCE,SOURCE_SHA
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map
from src.psx_disc import file_hash
from src.psx_player import composition_frame,decode_stream,indexed_atlas

def main():
    source=P.read_bytes();_,before,after,_=targets()
    result,proof=pack(source,before,after)
    need(result==(O/'PL02_U.ARC').read_bytes(),'Reproduction mismatch')
    a=Archive(result);gpu=combos=0
    for n in sorted(SELECTED):
        f=a.banks[0]['frames'][n];need(f['tile_count']==32,'Expected32 tiles')
        raw=decode_stream(a.g,f['offset'],f['limit'],4096).data
        atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
        for b in (0,5,6,7,8):
            for p in composition_frame(a.c,b,n)['parts']:
                t=p['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                need(t%16!=0 or not tile[:,0].any(),'GPU firstcolumn opaque')
                need(not (p['flip_y'] and t//16%16==0 and tile[0].any()),'GPU firstrow opaque')
                gpu+=1
        for mask in range(16):
            for arm in (1,2):
                im=np.array(a.composite(n,mask,arm)[0]);want=np.array(a.rgba(before[n],16)if mask&1 else a.rgba(after[n],0))
                for flip in (False,True):
                    need(np.array_equal(im[:,::-1]if flip else im,want[:,::-1]if flip else want),'Mask/arm/direction display mismatch');combos+=1
    for values in (before,after):
        for n in sorted(SELECTED):
            need(np.array_equal(values[n][178:],values[120][178:]),'Feet drift')
        for n in (120,122,124):
            y,x=np.nonzero(values[n]!=values[n+1]);need(len(x)==1,'Mouth changes outside1px')
            need([int(x[0])-160,int(y[0])-160]==[-5,-7-(n-120)//2],'Mouth anchor wrong')
            need(int(values[n][y[0],x[0]])==13 and int(values[n+1][y[0],x[0]])==11,'Mouth colors changed')
    tests=[]
    tests.append(('wrong_source',lambda:pack(source[:-1]+bytes([source[-1]^1]),before,after)))
    tests.append(('missing_ref',lambda:pack(source,{n:v for n,v in before.items()if n!=120},after)))
    bad={n:v.copy()for n,v in after.items()};bad[120][130,130]=5
    tests.append(('after_alpha_outside_before',lambda:pack(source,before,bad)))
    wrong={n:v.copy()for n,v in before.items()};wrong[120][150,150]=16
    tests.append(('palette_overflow',lambda:pack(source,wrong,after)))
    shape={n:v.copy()for n,v in before.items()};shape[120]=shape[120][:-1]
    tests.append(('wrong_canvas',lambda:pack(source,shape,after)))
    dtype={n:v.copy()for n,v in before.items()};dtype[120]=dtype[120].astype(np.float32)
    tests.append(('wrong_dtype',lambda:pack(source,dtype,after)))
    rejects=[]
    for name,call in tests:
        try:call()
        except ValueError as e:rejects.append({'case':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError(name)
    need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN modified')
    exe=read_disc(SOURCE,('SLUS_005.61',))[0]['SLUS_005.61']
    need(sha(exe)=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616','Source EXE changed')
    actual=animation_map(exe)[0][6]
    recorded=json.loads((H/'ultimate_lowhp_inputs01/analysis.json').read_text('utf8'))['native_animation']
    need(actual==recorded,'Native animation6 changed')
    simulation=json.loads((H/'ultimate_lowhp_targets01/provenance.json').read_text('utf8'))['simulation']['frame_durations']
    need([(q['frame'],q['duration_ticks'])for q in actual['steps']]==[tuple(q)for q in simulation],'Simulation sequence differs')
    report={'passed':True,'reproduced_sha256':sha(result),'byte_identical':True,'source_bin_preserved':True,'gpu_parts_checked':gpu,'mask_arm_direction_combinations':combos,'mouth_pairs_checked':6,'native_animation_id':6,'native_animation_steps':actual['steps'],'native_animation_byte_identity':True,'source_executable_sha256':sha(exe),'rejections':rejects,'actual_arc_sheets_viewed':['before/actual.png','after/actual.png'],'all_target_source_pixels_preserved':True,'body_size':{'new':[[28,48],[28,49],[28,50]],'old':[[24,46],[24,47],[24,48]],'idle_height':47},'runtime_verified':False,'game_written':False}
    report['review_scope']='새 12개 폼 표시를 대기 옆에서 직접 열람. 발 고정과 목·몸통·무릎 연결을 확인했다.'
    report['palette_constraints']='의상 CLUT의 1/4/11 색 차이 때문에 같은 새 머리 일부는 가장 가까운 기존 색으로 변환한다. 팔레트 자체는 보존한다.'
    report['body_size']['explanation']='새 기준 자세48px와 기존2px 호흡 변위를 유지했다. 전신 축소 또는 개별 bbox 리사이즈를 하지 않았다.'
    write(O/'repro_and_rejections.json',report)
    print(json.dumps({'passed':True,'sha256':sha(result),'gpu_parts':gpu,'combinations':combos,'rejections':len(rejects)}))

if __name__=='__main__':main()
