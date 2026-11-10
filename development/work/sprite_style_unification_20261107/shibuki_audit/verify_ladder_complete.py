"""사다리14참조 무손실 재현·반전·부분아머·총구·비대상·입력거부 검사."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame,decode_stream,indexed_atlas
from src.psx_disc import file_hash
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from register_ladder_parts import compose
import prepare_ladder_complete as maker

EXPECTED='76f19a188ad58dd447eec058b669f8d62a4b8c00f957de3b229aeaa67f37495b'

def main():
    need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');sources=read_disc(SOURCE,('PL00_U.ARC','SLUS_005.61'))[0]
    out=H/'prepared_ladder_wall_front02';data=(H/'prepared_wall_front01/PL00_U.ARC').read_bytes();actual=(out/'PL00_U.ARC').read_bytes();need(sha(actual)==EXPECTED,'Output changed')
    desired=maker.targets();rebuilt,repro=maker.pack(data,desired);need(rebuilt==actual,'Reproduction differs');a=Archive(actual);p=Archive(data);original=Archive(sources['PL00_U.ARC'])
    layers=parts=masks=0
    for n in sorted(maker.SELECTED):
        f=a.banks[0]['frames'][n];need(f['tile_count']==32,'Allocation changed');raw=decode_stream(a.g,f['offset'],f['limit'],4096).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256);need(not atlas[:,0].any()and not atlas[16:32,0:16].any(),'GPU page-edge tile not blank')
        for b in(0,5,6,7,8):
            need(np.array_equal(a.layer(n,b)[0],desired[n][b]),'Actual indexed target differs');layers+=1
            for q in composition_frame(a.c,b,n)['parts']:
                t=q['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                need(t<32 and t!=16,'Unsafe tile allocation');need(t%16!=0 or not tile[:,0].any(),'GPU U underflow');need(not q['flip_y']or t//16%16!=0 or not tile[0].any(),'GPU V underflow');parts+=1
        for m in range(16):
            for arm in(1,2):need(a.composite(n,m,arm)[0].tobytes()==compose(a,desired[n],m).tobytes(),'Partial arm target differs');masks+=1
    stable=0
    for n in(*range(55,67),*range(120,126),156,157,158):
        for m in range(16):
            for arm in(1,2):need(a.composite(n,m,arm)[0].tobytes()==p.composite(n,m,arm)[0].tobytes(),'Frozen earlier group changed');stable+=1
    barrels=nonarm=0
    for n,rect in((150,(-25,-12,-15,-4)),(155,(-22,-16,-12,-8))):
        bb=tuple(v+160 for v in rect);goal=original.composite(n,0)[0].crop(bb).tobytes()
        for m in range(16):
            for arm in(1,2):need(a.composite(n,m,arm)[0].crop(bb).tobytes()==goal,'Original barrel changed');barrels+=1
        edit=np.array(Image.open(H/f'ladder_shots_registered01/{n:03}_arm_mask.png'))>0;edit[bb[1]:bb[3],bb[0]:bb[2]]=True
        for b in(0,5,6,7,8):need(np.array_equal(a.layer(n,b)[0][~edit],a.layer(149,b)[0][~edit]),'Shooting nonarm body differs');nonarm+=1
    ui=(out/'ST0E_U1.ARC').read_bytes();need(ui==(H/'prepared_wall_front01/ST0E_U1.ARC').read_bytes(),'Selection changed')
    rejected=[]
    def reject(name,fn):
        try:fn()
        except(ValueError,AssertionError,KeyError):rejected.append(name)
        else:raise AssertionError('Invalid input accepted: '+name)
    reject('original_baseline_not_parent',lambda:maker.pack(sources['PL00_U.ARC'],desired))
    reject('changed_parent',lambda:maker.pack(bytes([data[0]^1])+data[1:],desired))
    reject('truncated_parent',lambda:maker.pack(data[:-1],desired))
    reject('missing_ref',lambda:maker.pack(data,{n:v for n,v in desired.items()if n!=143}))
    reject('extra_ref',lambda:maker.pack(data,{**desired,142:desired[143]}))
    for name,ref,b,change in [('invalid_index',143,0,lambda v:v.__setitem__((160,160),16)),('outside_staging',143,0,lambda v:v.__setitem__((0,0),1)),('wrong_mirror_alias',145,0,lambda v:v.__setitem__((160,160),int(v[160,160])^1))]:
        bad={n:{k:v.copy()for k,v in ls.items()}for n,ls in desired.items()};change(bad[ref][b]);reject(name,lambda:maker.pack(data,bad))
    for name,v in(('wrong_shape',np.zeros((16,16),np.uint8)),('wrong_dtype',np.zeros((384,384),np.int16))):
        bad={n:{k:q.copy()for k,q in ls.items()}for n,ls in desired.items()};bad[143][0]=v;reject(name,lambda:maker.pack(data,bad))
    meta=json.loads((H/'ladder_detail_inputs01/manifest.json').read_text('utf8'));exe=sources['SLUS_005.61'];load=struct.unpack_from('<I',exe,0x18)[0];steps=0
    def panel(n):
        board=Image.new('RGB',(1024,340),'#1a202b');d=ImageDraw.Draw(board)
        for col,(label,arc,mask)in enumerate((('base current',p,0),('base new',a,0),('Fourth current',p,15),('Fourth new',a,15))):
            im=arc.composite(n,mask)[0].crop((128,120,192,200)).resize((256,320),Image.Resampling.NEAREST);board.paste(im,(256*col,20),im);d.text((256*col+4,4),f'{label} ref{n}',fill='white')
        return board
    for row in meta['animations']:
        for s in row['steps']:
            off=0x800+int(s['address'],16)-load;need(exe[off:off+4].hex()==s['bytes'],'Actual EXE timing differs');steps+=1
        frames=[panel(s['frame'])for s in row['steps']];dur=[round(s['duration_calls_uninterrupted']*1000/60)for s in row['steps']]
        for slow in(1,4):frames[0].save(out/f'animation{row["id"]:03}_{slow}x.webp',save_all=True,append_images=frames[1:],duration=[v*slow for v in dur],loop=0,lossless=True)
    write(out/'sequences.json',{'kind':'native_step_order_review_not_gameplay','actual_executable_sha256':sha(exe),'actual_step_records_checked':steps,'animations':meta['animations'],'calls_per_second_assumption':60,'events_executed':False,'ladder_physics_simulated':False,'terminal_policy':'검토 영상은 스텝표를 한 번 표시한 뒤 반복한다. 실제 말단 유지·이동·종료 이벤트는 재현하지 않는다.','loop31_32_frames_and_durations_exact':True})
    report={'passed':True,'source_bin_sha256':SOURCE_SHA,'source_parent_sha256':sha(data),'reproduced_sha256':sha(actual),'selection_sha256':sha(ui),'indexed_layer_checks':layers,'partial_mask_arm_checks':masks,'gpu_part_checks':parts,'original_barrel_checks':barrels,'new_nonarm_body_checks':nonarm,'frozen_previous_group_mask_arm_checks':stable,'source_exe_step_checks':steps,'decoded_references':repro['decoded_references'],'nonselected_composites':repro['nonselected_composites'],'preserved_part_records':repro['preserved_part_records'],'rejected_inputs':rejected,'source_unchanged_after':file_hash(SOURCE)==SOURCE_SHA,'all_old_game_body_head_excluded':True,'emulator_test':False,'not_complete_all_art_style':True}
    write(out/'repro_and_rejections.json',report);print(json.dumps(report))

if __name__=='__main__':main()
