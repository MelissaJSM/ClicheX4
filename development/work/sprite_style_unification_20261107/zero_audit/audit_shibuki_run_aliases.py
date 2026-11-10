"""Independent read-only alias/consumed-tile inventory for Shibuki run prep."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import Archive
from src.psx_player import bank_offsets,graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage
D=Path(__file__).parent;O=D/'shibuki_run_alias_audit01';O.mkdir(exist_ok=True)
P=ROOT/'work/sprite_style_unification_20261107/shibuki_audit/prepared_dash_base01/PL00_U.ARC'
arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b'
a=Archive(arc);g,c=entry(arc,2),entry(arc,3);layers=(0,5,6,7,8)
frames=graphics_bank(g,0,allow_bank_aliases=True)['frames']
streams=collections.defaultdict(list)
for gb in range(len(bank_offsets(g,allow_aliases=True))):
    for f in graphics_bank(g,gb,allow_bank_aliases=True)['frames']:
        streams[f['offset']].append({'bank':gb,'ref':f['index'],'tiles':f['tile_count']})
record_owners=collections.defaultdict(list);comps={}
for pb in range(len(bank_offsets(c,allow_aliases=True))):
    count=composition_frame(c,pb,0)['bank_frame_count']
    for n in range(count):
        cp=composition_frame(c,pb,n);comps[pb,n]=cp
        for p in cp['parts']:record_owners[p['record_offset']].append((pb,n))

def decode(f):return decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
def consumed(cp):return sorted({p['tile'] for p in cp['parts']})
rows=[]
for n in range(33):
    f=frames[n];raw=decode(f);layer_rows=[]
    for pb in layers:
        cp=comps[pb,n];offs=[p['record_offset'] for p in cp['parts']]
        same=[m for m in range(len(frames)) if [p['record_offset'] for p in comps[pb,m]['parts']]==offs]
        owners=sorted({v for off in offs for v in record_owners[off]})
        pixels,meta=a.layer(n,pb)
        layer_rows.append({'parts_bank':pb,'records':offs,'part_count':len(offs),'exact_same_record_list_refs':same,'all_overlapping_record_owners':[list(x)for x in owners],
                           'consumed_tiles_including_hidden':consumed(cp),'indexed_sha256':sha(pixels.tobytes()),'opaque_pixels':int(np.count_nonzero(pixels%16)),
                           'parts':[{'flags':p['flags'],'tile':p['tile'],'x':p['x'],'y':p['y']}for p in cp['parts']]})
    non_targets=[x['ref'] for x in streams[f['offset']] if x['bank']==0 and x['ref'] not in range(1,33)]
    protected_tiles=sorted({t for m in non_targets for pb in layers for t in consumed(comps[pb,m])})
    rows.append({'ref':n,'stream_offset':f['offset'],'tile_count':f['tile_count'],'decoded_sha256':sha(raw),'all_physical_stream_owners':streams[f['offset']],
                 'non_target_main_stream_owners':non_targets,'non_target_consumed_tiles':protected_tiles,'layers':layer_rows})
first=[]
for n in (1,2):
    row={'ref':n,'against_idle0':[]}
    for pb in layers:
        p,m=a.layer(0,pb);q,mq=a.layer(n,pb)
        row['against_idle0'].append({'parts_bank':pb,'indexed_pixels_exact':bool(np.array_equal(p,q)),'different_world_pixels':int(np.count_nonzero(p!=q)),
                                     'old_idle_tiles':consumed(comps[pb,0]),'run_tiles':consumed(comps[pb,n])})
    first.append(row)
raw_groups=[];seen=set()
for n in range(33):
    f=frames[n]
    if f['offset']in seen:continue
    seen.add(f['offset'])
    raw_groups.append({'representative':n,'offset':f['offset'],'all_owners':streams[f['offset']]})
result={'passed':True,'source':str(P.relative_to(ROOT)),'sha256':sha(arc),'scope':'ref0/1/2 및3..32의 실제 압축 스트림과 조립 레코드 공유를 읽었다. 패킹/아트 변경은 하지 않았다.',
        'raw_groups':raw_groups,'frames':rows,'idle_comparison':first,
        'constraints':[
            'idle0의 압축 스트림은 main142와 공유한다. 0 보존은142도 함께 포함하며, 같은 raw 위에서 눈에 안 보이는 타일을 임의 삭제하지 않는다.',
            '1/2는21타일 동일 스트림을 공유한다. 조립 head5/body6/leg8은1/2가 같은 레코드를 사용하므로 한쪽 파츠 레코드 변경이 다른 쪽에도 적용된다.',
            '1을0의 수용 폼으로 맞추더라도0과1의 물리 타일 번호는 서로 다른 스트림 안의 주소다. 원시 tile번호만 복사해서 동기화할 수 없다.',
            '2의 새 사격 팔은7층/기본층의 소비 타일과 최종 그림을 같이 만족해야 한다. 바뀌지 않는1의 모든 소비 타일(가려진 타일 포함)을 보호하거나 두 참조를 한 공동스트림으로 새로 패킹한다.',
            '3..32는 아래 raw_groups/records의 실제 owners를 기준으로 공동 처리한다. 같은 그림처럼 보인다는 이유만으로 스트림/parts를 분리하거나 합치지 않는다.',
            '정해진 은행 끝과32타일 한도를 보존하고 tile0/16 첫열 및 flipY 첫행 새 침범을 검사한다. 이 읽기 목록 자체는 새 그림 패킹 성공 증거가 아니다.'
        ],'producer_functions_called':False,'game_or_original_modified':False,'runtime_verified':False}
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'first3':[{'ref':r['ref'],'stream_owners':r['all_physical_stream_owners'],'layer_aliases':[(q['parts_bank'],q['exact_same_record_list_refs'])for q in r['layers']]}for r in rows[:3]],'run_groups':raw_groups}))
