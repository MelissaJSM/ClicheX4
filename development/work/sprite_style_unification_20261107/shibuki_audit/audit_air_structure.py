"""새 공중 원화 전 단계: 실제 표·공유 스트림·조립 여유를 읽기만 한다."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from src.psx_player import composition_frame,bank_offsets,decode_stream
from src.psx_disc import file_hash
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write

P=H/'prepared_arrival_victory01/PL00_U.ARC'
PSHA='78b329a07d888682c24b440386cb365f826572402346b3ee6620216ce951617e'
O=H/'air_detail_inputs01'

def main():
    data=P.read_bytes();need(sha(data)==PSHA,'Frozen parent changed')
    need(file_hash(SOURCE)==SOURCE_SHA,'Baseline changed')
    exe=read_disc(SOURCE,('SLUS_005.61',))[0]['SLUS_005.61']
    load=struct.unpack_from('<I',exe,0x18)[0]
    table=ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json'
    inventory=json.loads(table.read_text('utf8'));frames=set(range(33,55))|{93,94};sequences=[]
    step_checks=0
    for row in inventory['animations']:
        if not any(s['frame'] in frames for s in row['steps']):continue
        ptr_off=0x800+int(inventory['table_address'],16)+row['id']*4-load
        need(struct.unpack_from('<I',exe,ptr_off)[0]==int(row['address'],16),'Native pointer differs')
        for s in row['steps']:
            off=0x800+int(s['address'],16)-load
            need(exe[off:off+4].hex()==s['bytes'],'Native step differs');step_checks+=1
        sequences.append(row)
    a=Archive(data);starts=bank_offsets(a.c);budgets=[]
    for b in (0,5,6,7,8):
        count=composition_frame(a.c,b,0)['bank_frame_count'];end=starts[b+1] if b+1<len(starts) else len(a.c)
        simulated,slack=repack_parts(a.c,b,{})
        need(all(records(a.c,b,n)==records(simulated,b,n) for n in range(count)),'No-op part semantics changed')
        budgets.append({'bank':b,'fixed_bytes':end-starts[b],'frames':count,'pointer_bytes':count*4,
                        'all_record_bytes':sum(len(records(a.c,b,n)) for n in range(count)),
                        'current_semantic_dedup_slack':slack,'file_written':False})
    groups=[];seen=set()
    for n in sorted(frames):
        f=a.banks[0]['frames'][n];off=f['offset']
        if off in seen:continue
        seen.add(off);refs=[v['index'] for v in a.banks[0]['frames'] if v['offset']==off]
        dec=decode_stream(a.g,off,f['limit'],f['tile_count']*128)
        groups.append({'refs':refs,'compressed_offset':off,'compressed_bytes':dec.end-off,
                       'decoded_bytes':len(dec.data),'tile_count':f['tile_count'],
                       'part_counts':{str(k):{str(b):len(a.layer(k,b)[1]['parts']) for b in (0,5,6,7,8)} for k in refs},
                       'non_air_shared_refs':sorted(set(refs)-frames)})
    pairs=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/air_v1/production05/pairs.json').read_text('utf8'))['frames']
    anchors=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/air_v1/alignment_checks.json').read_text('utf8'))['frames']
    facts={
        'passed':True,'parent_arc_sha256':PSHA,'source_bin_sha256':SOURCE_SHA,'source_executable_sha256':sha(exe),
        'animation_inventory_sha256':sha(table.read_bytes()),'native_pointer_checks':len(sequences),
        'native_step_checks':step_checks,'sequences':sequences,'shared_graphics_groups':groups,'composition_budgets':budgets,
        'source_alignment':anchors,'muzzle_pairs':pairs,
        'art_actual_viewed':['page01_poses.png','accepted_style.png','base_old_air_review.png','fourth_old_air_review.png'],
        'generation_stage':'33/35/39 기본·포스 6그림 입력만 준비. 아직 새 공중 그림 생성 없음.',
        'art_findings':[
            '33/35의 넓고 평평한 귀·뒷머리, 흰 소매와 가슴에 대기보다 중간 명암·옷단 분할이 부족하다.',
            '39/41의 양팔을 올린 자세는 정상이나 머리·소매·허리의 큰 단색 덩어리는 재작화 대상이다.',
            '49/51/53 착지의 짧아지는 높이는 정상 굽힘이다. 단색 뒷머리와 옷 단순화는 별도로 수정한다.'
        ],
        'packing_plan':[
            '원래 같은 스트림을 공유하는 일반·사격을 함께 처리한다. 새 일반 몸체를 유지하고 발사팔만 별도 원화로 정합한다.',
            '파트5 여유4바이트는 그림 삭제 이유가 아니다. 새 구역 공유·동일 조립 레코드 재사용을 먼저 검사하고 부족하면 보고한다.',
            '새 기본/포스의 공통 관절을 맞추고 후드·상의·소매·다리를 의미별로 분리한 후16마스크×양팔을 검사한다.',
            '0/115..119와 이미 동결된 저체력·벽·사다리·등장·승리·귀환·선택은 픽셀 및 의미 레코드 보존한다.'
        ],
        'timer_policy':'duration0=256호출, -1=255호출이다. 60호출/초는 검토 영상의 가정이며 실제 이벤트·중력·충돌은 이 감사가 실행하지 않는다.',
        'no_file_resource_change':True,'runtime_verified':False,'full_style_unification_complete':False
    }
    write(O/'structure_audit.json',facts)
    print(json.dumps({'passed':True,'native_sequences':[r['id'] for r in sequences],
                      'step_checks':step_checks,'slack':{r['bank']:r['current_semantic_dedup_slack'] for r in budgets},
                      'groups':len(groups)}))

if __name__=='__main__':main()
