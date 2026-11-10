"""블랙 변형 입력/출력의 읽기 전용 독립 검사. 증거 파일만 audit에 저장한다."""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.discover_inputs import psx_arc
from scripts.prepare_riko_ui import entry
from scripts import black_variant_palette as candidate
from src.psx_disc import file_hash, write_archive_copies
from src.psx_player import composition_frame
from src.psx_sector import validate_checks, replace_payload

AUDIT = Path(__file__).resolve().parent
WORK = AUDIT.parent
NAMES = ('PL01_U.ARC', 'MOJIPAT.ARC')
EXTRAS = ('LOAD_U.ARC', 'COL0E_U1.ARC', 'COL00_0Z.ARC', 'SLUS_005.61')
CASES = {
    'ver_buki_riko': ('shibuki_riko', 'black_monochrome_riko_20261105_v1',
        '6d9f0310be3df40b5000643a1b19d860cc6ebe4f8c476fb4150210ce189ecf88',
        '852813890c3c9f8e0394026f8c243f6c323f1a9c0f4e1941eaa920b85bdecc4e'),
    'ver_rin_nana': ('rin_nana', 'black_red_rin_20261105_v1',
        '0c019de65ea2b39e46cdd215d13f2d1de3a4cbda5aaac1567eecc16a83be4108',
        'aca6d7839ad1956ea837b07d1105a7609817cd30fd0e6ceffe13e6dd611ad6fe'),
}

def require(value, message):
    if not value:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def refused(label, operation):
    try:
        operation()
    except ValueError as error:
        return {'case': label, 'rejected': True, 'reason': str(error)}
    raise ValueError('Invalid input accepted: ' + label)

def read_words(data):
    return list(struct.unpack('<16H', data))

def inspect_palette(project, normal, revised):
    a, b = read_words(normal), read_words(revised)
    rgb = [(w & 31, w >> 5 & 31, w >> 10 & 31) for w in b]
    require(a[0] == b[0] == 0, 'Transparent index changed')
    require(all((u & 0x8000) == (v & 0x8000) for u, v in zip(a, b)), 'STP changed')
    require(len(set(b[1:])) == 15 and all(w & 0x7fff for w in b[1:]), 'Opaque shades merged/zeroed')
    if project == 'ver_buki_riko':
        require(all(r == g == bl for r, g, bl in rgb), 'Riko is not achromatic')
    else:
        require(a[11:15] == b[11:15], 'Rin white/skin changed')
        require(all(r > g and r > bl for i, (r, g, bl) in enumerate(rgb) if i in (*range(1,11),15)),
                'Rin intended costume/outline not red-dominant')
    return {'normal_words': a, 'black_words': b, 'black_rgb5': rgb,
            'normal_sha256': sha(normal), 'black_sha256': sha(revised),
            'transparent_and_STP_preserved': True, 'all_15_nonzero_shades_distinct': True}

def inspect_paths(assets):
    p = entry(assets['PL01_U.ARC'], 3)
    groups = {}
    for label, bank, frames in [
        ('appearance_warp',0,range(53,61)), ('return_warp',5,range(9,14)),
        ('ride_chaser_character',5,range(14,42)), ('ride_armor_heads',5,range(66,86)),
        ('idle',0,[147]), ('electric_hurt_shared_effect',0,[140,141,143,145])]:
        rows = {str(f): sorted({v['clut'] for v in composition_frame(p,bank,f)['parts']}) for f in frames}
        groups[label] = {'composition_bank': bank, 'frames_clut_offset': rows}
        if label != 'electric_hurt_shared_effect':
            require(all(v == [0] for v in rows.values()), 'Unexpected character CLUT')
    save = composition_frame(assets['MOJIPAT.ARC'], 2, 43)
    require({p['clut'] for p in save['parts']} == {2}, 'Unexpected save frame CLUT')
    col = entry(assets['COL00_0Z.ARC'], 5)
    return {'composition_cluts': groups,
            'save_icon': {'bank':2, 'frame':43, 'all_parts_clut_offset':2,
                          'normal_base':'0x7808', 'normal_final':'0x780A', 'normal_MOJIPAT_row':10,
                          'black_base':'0x784B', 'black_final':'0x784D', 'black_MOJIPAT_row':29,
                          'same_LOAD_bitmap': True},
            'representative_stage_COL00_0Z_palette_hashes':
                {str(r):sha(col[r*32:(r+1)*32]) for r in (2,3,11,13,14,15)},
            'runtime_black_source_row':13, 'runtime_destination_row':0, 'runtime_CLUT':'0x7800'}

def main():
    report = {'passed': False, 'projects': {}, 'runtime_verified': False,
              'original_game_or_user_save_files_opened_for_write': False,
              'scope': '새 변형 두 BIN과 C01 부모의 전 섹터 비교, 준비물 재현, 팔레트 경로 정적 검사'}
    for project, (stem, folder, source_sha, target_sha) in CASES.items():
        source = ROOT/'out'/project/'c01_x6_sfx_20261105_v1'/(stem+'.bin')
        target = ROOT/'out'/project/folder/(stem+'.bin')
        require(file_hash(source) == source_sha, 'Unexpected source hash')
        require(file_hash(target) == target_sha, 'Unexpected target hash')
        all_old, records = read_disc(source, NAMES+EXTRAS)
        all_new, new_records = read_disc(target, NAMES+EXTRAS)
        require(records == new_records, 'Directory metadata changed')
        old = {n:all_old[n] for n in NAMES}
        new = {n:all_new[n] for n in NAMES}
        proposal = json.loads((WORK/'prepared_v1'/project/'proposal.json').read_text('utf8'))
        require(proposal['project'] == project and proposal['baseline_sha256'] == source_sha,
                'Proposal source identity differs')
        require((ROOT/proposal['baseline']).resolve() == source.resolve(), 'Proposal source path differs')
        require(set(proposal['files']) == set(NAMES), 'Proposal resource set differs')
        reproduced, proof = candidate.patch(project, old)
        require(reproduced == new and candidate.patch(project,old)[0] == reproduced, 'Patch reproduction differs')
        positions = {'PL01_U.ARC':2464, 'MOJIPAT.ARC':7716}
        pal_entry = next(e for e in psx_arc(old['PL01_U.ARC']) if int(e['type'],16) == 9)
        menu_palette_base = struct.unpack_from('<I',old['MOJIPAT.ARC'],4)[0]
        require(pal_entry['offset'] + 13*32 == 2464 and menu_palette_base + 29*32 == 7716,
                'Palette layout differs')
        normal = entry(old['PL01_U.ARC'],9)[:32]
        black = new['PL01_U.ARC'][2464:2496]
        palette = inspect_palette(project,normal,black)
        require(black != normal and new['MOJIPAT.ARC'][7716:7748] == black, 'Gameplay/save colors disagree')
        allowed = {}
        files = {}
        for name, at in positions.items():
            require(len(old[name]) == len(new[name]), 'Resource size changed')
            require(old[name][:at] == new[name][:at] and old[name][at+32:] == new[name][at+32:],
                    'Non-target byte changed')
            require(old[name][at:at+32] == normal, 'Parent Black palette not accepted normal color')
            r = proposal['files'][name]
            require(r['before'] == sha(old[name]) and r['after'] == sha(new[name]) and r['record'] == records[name],
                    'Proposal resource metadata differs')
            require((ROOT/r['path']).read_bytes() == new[name], 'Prepared resource differs')
            data_changes = [i for i,(a,b) in enumerate(zip(old[name],new[name])) if a != b]
            require(len(data_changes) == r['changed_bytes'], 'Declared byte count differs')
            files[name] = {'before_sha256':sha(old[name]), 'after_sha256':sha(new[name]),
                           'authorized_range':[at,at+32], 'changed_offsets':data_changes}
            for i in range(at,at+32):
                lba = records[name]['lba']+i//2048
                allowed.setdefault(lba,set()).add(24+i%2048)
        require(entry(new['PL01_U.ARC'],9)[:32] == normal, 'Normal gameplay changed')
        require(new['MOJIPAT.ARC'][menu_palette_base+320:menu_palette_base+352] == normal,
                'Normal save colors changed')
        require(all(all_old[n] == all_new[n] for n in EXTRAS), 'Protected representative resources changed')
        sectors, changed = 0, []
        hs, ht = hashlib.sha256(), hashlib.sha256()
        with source.open('rb') as f, target.open('rb') as g:
            while a := f.read(2352):
                b = g.read(2352)
                require(len(a) == len(b) == 2352, 'Unexpected sector size')
                hs.update(a); ht.update(b)
                if a != b:
                    require(sectors in allowed, 'Unauthorized changed sector')
                    offsets = [i for i,(u,v) in enumerate(zip(a,b)) if u != v]
                    require(all(i in allowed[sectors] or i >= 2072 for i in offsets),
                            'Unauthorized changed raw byte')
                    validate_checks(a); validate_checks(b)
                    want = bytearray(a[24:2072])
                    for name,at in positions.items():
                        for i in range(at,at+32):
                            if records[name]['lba']+i//2048 == sectors:
                                want[i%2048] = new[name][i]
                    require(replace_payload(a,bytes(want)) == b, 'Independent expected sector differs')
                    changed.append({'lba':sectors, 'payload_bytes':sum(24 <= i < 2072 for i in offsets),
                                    'check_bytes':sum(i >= 2072 for i in offsets)})
                sectors += 1
            require(not g.read(1), 'Target grew')
        require(len(changed) == 2 and {v['lba'] for v in changed} == set(allowed), 'Unexpected modified sector set')
        require(hs.hexdigest() == source_sha and ht.hexdigest() == target_sha, 'File changed during audit')
        refused_cases = []
        for label, name, at in [('normal_player','PL01_U.ARC',pal_entry['offset']),
                                ('black_player','PL01_U.ARC',2464), ('normal_save','MOJIPAT.ARC',menu_palette_base+320),
                                ('black_save','MOJIPAT.ARC',7716)]:
            bad = dict(old); data = bytearray(bad[name]); data[at] ^= 1; bad[name] = bytes(data)
            refused_cases.append(refused(label,lambda d=bad:candidate.patch(project,d)))
        refused_cases.append(refused('already_applied',lambda:candidate.patch(project,new)))
        refused_cases.append(refused('extra_resource',lambda:candidate.patch(project,{**old,'UNEXPECTED':b''})))
        refused_cases.append(refused('missing_resource',lambda:candidate.patch(project,{'PL01_U.ARC':old['PL01_U.ARC']})))
        refused_cases.append(refused('invalid_palette_size',lambda:candidate.make_palette(project,normal[:-1])))
        refused_cases.append(refused('source_target_alias',lambda:write_archive_copies(source,source,[],source_sha)))
        never_created = AUDIT/(project+'_wrong_hash_must_not_exist.bin')
        require(not never_created.exists(), 'Unexpected negative-test output already exists')
        refused_cases.append(refused('wrong_source_sha256',lambda:write_archive_copies(source,never_created,[], '0'*64)))
        require(not never_created.exists(), 'Rejected hash wrote an output')
        require(file_hash(source) == source_sha, 'Source changed after negative tests')
        paths = inspect_paths(all_new)
        report['projects'][project] = {'bin_sha256':target_sha, 'source_sha256':source_sha,
            'bin':target.relative_to(ROOT).as_posix(), 'passed':True, 'files':files, 'palette':palette,
            'all_disc_sectors_compared':sectors, 'changed_sectors':changed, 'EDC_ECC_verified':True,
            'all_other_bytes_preserved':True, 'all_bitmaps_compositions_audio_code_COL_LOAD_preserved':True,
            'prepared_and_reproduced_resources_exact':True, 'normal_gameplay_and_save_palette_preserved':True,
            'negative_tests':refused_cases, 'palette_paths':paths,
            'source_readonly_hash_preserved':True, 'runtime_verified':False}
        print(project, target_sha, sectors, len(changed), 'PASS', flush=True)
    report['limitations'] = [
        '이번 검사는 정적 자원/바이트/경로 검사이며 새 팔레트의 실기 수용을 뜻하지 않는다.',
        '대시 잔상은 COL row13~15, 잔기는 COL row11, 사망 구체는 별도 COL 효과 행을 공유하므로 색상을 유지한다.',
        '전기 피격 일부 CLUT offset2와 탑승 기계 자체 색상은 일반형과 공유하며 이번 범위에서 그대로다.',
        '기존 overhaul_black_verify.py는 black==normal 및 normal 렌더를 전제하므로 새 변형 검증에 그대로 사용할 수 없다.',
        '예전 F3 상태는 옛 팔레트를 포함할 수 있다. 새 부팅 또는 인증된 별도 체크포인트가 필요하다.'
    ]
    report['passed'] = True
    (AUDIT/'independent.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')

if __name__ == '__main__':
    main()
