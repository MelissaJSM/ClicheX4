"""보호 파일·현재 결과·완료된 실기 기록의 독립 읽기 감사. 프로세스 접근 없음."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
from functools import reduce
from operator import xor
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.audit_sprite_consistency_coverage import file_sha,sha,read_assets,unique_entry,write
from scripts.observe_sprite_consistency_runtime import EXPECTED

TASK=ROOT/'work/sprite_consistency_20261105';OUT=TASK/'runtime/final_integrity.json'
def read_json(path):return json.loads(path.read_text('utf8'))
checks=[];errors=[];cache={}
def digest(path):
    path=path.resolve()
    if path not in cache:cache[path]=file_sha(path)
    return cache[path]
def record(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    if not condition:errors.append(name)
def inspect(path,expected,size=None):
    p=ROOT/path
    if not p.is_file():
        record('missing '+path,False);return {'path':path,'exists':False,'passed':False}
    actual=digest(p);actual_size=p.stat().st_size;ok=actual==expected and(size is None or actual_size==size)
    record('hash '+path,ok)
    return {'path':path,'expected_sha256':expected,'actual_sha256':actual,'size':actual_size,'passed':ok}

before=read_json(TASK/'protection_before.json')
record('protection inventory count31',len(before)==31)
preserved=[inspect(p,r['sha256'],r['size'])for p,r in before.items()]
inventory=read_json(TASK/'coverage/runtime_card_inventory.json')
card_entries=[v for rows in read_json(TASK/'runtime/card_clones.json').values()for v in rows.values()]
for n in ('epsxe000.mcr','epsxe001.mcr'):
    original='work/ver_rin_nana/test_cards/idle_v1/'+n
    expected=next(c['sha256']for c in inventory['cards']if c['path']==original)
    card_entries.append({'original':original,'clone':'work/ver_rin_nana/sprite_consistency_review/legacy_cards/'+n,'sha256':expected})
cards=[]
for item in card_entries:
    source=inspect(item['original'],item['sha256'],131072);clone=inspect(item['clone'],item['sha256'],131072)
    data=(ROOT/item['clone']).read_bytes()
    directory_ok=len(data)==131072 and data[:2]==b'MC' and all(reduce(xor,data[i*128:i*128+127],0)==data[i*128+127]for i in range(16))
    record('card header/directory '+item['clone'],directory_ok)
    cards.append({'original':source,'clone':clone,'clone_byte_equal_original':data==(ROOT/item['original']).read_bytes(),'directory_xor16_passed':directory_ok})
record('six card clones checked',len(cards)==6)

builds={};assets={}
for mode,expected in EXPECTED.items():
    pointer=read_json(ROOT/'projects'/mode/'current_build.json');stem='shibuki_riko'if mode=='ver_buki_riko'else'rin_nana'
    path=pointer['build']+'/'+stem+'.bin';builds[mode]=inspect(path,expected)
    record('current pointer SHA '+mode,pointer['sha256']==expected)
    builds[mode]['pointer']=str((ROOT/'projects'/mode/'current_build.json').relative_to(ROOT)).replace('\\','/')
    assets[mode]=read_assets(ROOT/path,['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','SLUS_005.61'])[0]
    builds[mode]['resource_hashes']={n:sha(v)for n,v in assets[mode].items()}

album_build=read_json(TASK/'zero/album/build.json');album_browser=read_json(TASK/'zero/album/browser_verification.json')
album=inspect(album_build['file'],album_build['sha256'],album_build['bytes'])
record('album browser evidence bound to actual HTML',album['actual_sha256']==album_browser['html_sha256'])
isolated=inspect(album_browser['isolated_copy'],album['actual_sha256'])
album.update({'isolated_copy':isolated,'browser_evidence_same_html':album_browser['passed'],
              'browser_reexecuted_by_this_audit':False,'main_references':album_build['main_references'],
              'all_images_embedded_build_claim':album_build['all_images_embedded'],
              'playback_manifest':inspect('work/sprite_consistency_20261105/playback/manifest.json',album_build['playback_manifest_sha256'])})

runtime=[]
specs=[('nana_base_sync','nana','base',set()),
       ('riko_wall_sync','riko','normal',{(0,n)for n in range(38,44)}|{(1,n)for n in(50,51,53,54,56,57,59,61,63,65)}),
       ('shibuki_fourth_special_sync','shibuki','fourth',{(0,n)for n in(101,102,103,104,231,232)}),
       ('rin_wall_sync','rin','normal',set())]
for name,character,form,target in specs:
    folder=TASK/'runtime'/name;sync=read_json(folder/'synchronization.json');e=read_json(folder/'observer/evidence.json');video=read_json(folder/'recording/evidence.json')
    verified={(x['bank'],x['frame'])for x in e['events']if x['verified']}
    attempted={(x['bank'],x['frame'])for x in e['events']}
    record(name+' event-derived verified refs',verified==set(map(tuple,e['verified_bank_frames']))==set(map(tuple,sync['verified_bank_frames'])))
    unverified=[i for i,event in enumerate(e['events'])if not event['verified']]
    record(name+' event-derived unverified indices',unverified==e['unverified_events']==sync['observer_unverified_events'])
    record(name+' source disc',e['disc_sha256']==video['bin_sha256']==EXPECTED[e['project']])
    record(name+' same session/pid',e['session']==video['session'] and e['pid']==video['pid'])
    start=int(e['watch_start_monotonic_ns']);end=int(e['watch_end_monotonic_ns'])
    vstart=int(video['record_start_monotonic_ns']);vend=int(video['record_end_monotonic_ns'])
    contained=start<=vstart<=vend<=end
    record(name+' synchronized input/video inside observer',contained and sync['input_recording_fully_within_observation'])
    record(name+' recording completed',video['error'] is None and sync['recording_error'] is None and video['keys_released'])
    record(name+' actual recording flags',video['actual_window_recording'] and not video['simulated_video'] and not video['memory_written'] and not video['save_keys_sent'])
    ram=(folder/'observer/ram_start.bin').read_bytes();vram=(folder/'observer/vram_start.bin').read_bytes()
    record(name+' saved RAM sha',sha(ram)==e['ram_start_sha256']);record(name+' saved VRAM sha',sha(vram)==e['vram_start_sha256'])
    resident=[]
    for r in e['resident_assets']:
        arc=assets[e['project']][r['archive']];record(name+' actual ARC hash',sha(arc)==r['archive_sha256'])
        for typ,entry in r['entries'].items():
            raw=unique_entry(arc,int(typ));pos=entry['ram_offset']
            ok=raw==ram[pos:pos+len(raw)] and sha(raw)==entry['sha256'] and len(raw)==entry['size']
            record(name+' initial resident '+r['archive']+'/'+typ,ok)
            resident.append({'archive':r['archive'],'entry':int(typ),'actual_disc_equals_initial_RAM':ok})
    playback=folder/'recording/play.webp';capture_times=video['capture_times']
    capture_durations=[max(1,round((b-a)*1000))for a,b in zip(capture_times,capture_times[1:])]+[100]
    capture_boundaries={0};boundary=0
    for duration in capture_durations:boundary+=duration;capture_boundaries.add(boundary)
    encoded=[];first_rgb=None;last_rgb=None
    with Image.open(playback)as im:
        actual_frames=im.n_frames
        for i in range(actual_frames):
            im.seek(i);im.load();encoded.append({'timestamp_ms':im.info['timestamp'],'duration_ms':im.info['duration']})
            if i==0:first_rgb=im.convert('RGB').tobytes()
            if i==actual_frames-1:last_rgb=im.convert('RGB').tobytes()
    encoded_total=sum(x['duration_ms']for x in encoded)
    timeline_ok=encoded_total==sum(capture_durations) and all(x['timestamp_ms']in capture_boundaries and x['timestamp_ms']+x['duration_ms']in capture_boundaries for x in encoded)
    record(name+' recording capture counts',len(capture_times)==video['frames']==sync['recorded_frames'])
    record(name+' WebP retained capture duration',timeline_ok)
    record(name+' WebP bounded frame count',0<actual_frames<=len(capture_times))
    with Image.open(folder/'recording/first.png')as im:record(name+' WebP first frame exact',first_rgb==im.convert('RGB').tobytes())
    with Image.open(folder/'recording/last.png')as im:record(name+' WebP last frame exact',last_rgb==im.convert('RGB').tobytes())
    record(name+' requested revised references observed',target<=verified)
    runtime.append({'name':name,'character':character,'form':form,'project':e['project'],'session':e['session'],
      'observer_evidence_sha256':digest(folder/'observer/evidence.json'),'recording_evidence_sha256':digest(folder/'recording/evidence.json'),
      'synchronization_sha256':digest(folder/'synchronization.json'),'actual_video_sha256':digest(playback),
      'actual_video_frame_count':actual_frames,'recorded_capture_count':len(capture_times),
      'encoded_duration_ms':encoded_total,'expected_capture_duration_ms':sum(capture_durations),
      'encoded_durations_match_contiguous_capture_boundaries':timeline_ok,
      'video_frame_count_note':'lossless WebP encoder can combine unchanged consecutive captures into one longer frame. Source capture durations and encoded timeline/endpoints checked; all original separate intermediate captures were not retained for independent pixel comparison.',
      'input_video_fully_inside_observer':contained,
      'observer_seconds':e['duration_seconds'],'video_seconds':(vend-vstart)/1e9,
      'unique_verified_bank_ref_count':len(verified),'unique_verified_bank_refs':[list(x)for x in sorted(verified)],
      'unique_attempted_bank_ref_count':len(attempted),'distinct_refs_without_any_verified_event':[list(x)for x in sorted(attempted-verified)],
      'transition_event_count':len(e['events']),'unverified_transition_count':len(unverified),
      'unverified_transitions':[{'event_index':i,'bank':e['events'][i]['bank'],'frame':e['events'][i]['frame'],
          'stable_samples':e['events'][i]['stable_samples'],'same_ref_verified_in_another_event':(e['events'][i]['bank'],e['events'][i]['frame'])in verified}for i in unverified],
      'targeted_recent_refs':[list(x)for x in sorted(target)],'targeted_recent_refs_verified':target<=verified,
      'initial_resident_independent_checks':resident,'end_resident_exact_reported_by_observer':e['resident_assets_still_exact'],
      'main_loop_ticks_per_second':e['native_main_loop_counter']['ticks_per_second'],'is_display_fps':False,
      'whole_framebuffer_pixels_independently_compared':False,
      'scope':'관측된 참조의 원래 디코드 바이트→RAM→GPU 업로드. 실제 화면 영상은 별도이며 모든 모션/좌우/최종화면 픽셀 전수 검증을 뜻하지 않음.'})

result={'passed':not errors,'created_utc':datetime.now(timezone.utc).isoformat(),'source_preservation_manifest_sha256':digest(TASK/'protection_before.json'),
        'protected_file_count':len(preserved),'protected_files':preserved,'card_clones':cards,'current_builds':builds,'all_sprites':album,
        'runtime_sessions':runtime,'per_character_verified_reference_counts':{r['character']:r['unique_verified_bank_ref_count']for r in runtime},
        'sum_of_per_character_reference_counts':sum(r['unique_verified_bank_ref_count']for r in runtime),
        'sum_semantics':'각 캐릭터/폼의(bank,ref) 집합 크기를 더한 수. 서로 다른 캐릭터의 번호가 중복되므로 전 게임의 고유 프레임 수라고 부르지 않는다.',
        'checks':checks,'errors':errors,'process_accessed':False,'keys_sent':False,'originals_modified':False,'cards_modified':False,
        'active_pointers_or_global_docs_modified':False,
        'limitations':['31보호파일과지정6사본만보존감사대상이며프로젝트전체파일감사가아니다.',
                       '일부미샘플전환표본은명시했고같은참조의다른안정일치와구분했다.',
                       '전체화면의효과/배경가림까지바이트비교한것이아니며전모션전수실기완료주장이아니다.',
                       '현재포인터의실기상태설명은부모의후속갱신대상이며본감사는빌드경로와SHA만검증했다.']}
write(OUT,result)
print(json.dumps({'passed':result['passed'],'protected':len(preserved),'clones':len(cards),
 'counts':result['per_character_verified_reference_counts'],'sum_per_character':result['sum_of_per_character_reference_counts'],
 'unverified_events':{r['name']:r['unverified_transitions']for r in runtime},'errors':errors},ensure_ascii=False))
