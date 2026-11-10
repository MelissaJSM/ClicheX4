"""최종 보관 자료의 입력 보존·공간 절감·출처 색인을 기록한다. 게임 파일은 변경하지 않는다."""
import hashlib,importlib.metadata,json,os,platform,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.compact_builds import digest
D=ROOT/'work/maintenance/final_20261028';R=ROOT/'out/ver_buki_riko/final_v1_0_0'
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf-8')

def references():
    paths={}
    def walk(x,source):
        if isinstance(x,dict):
            for v in x.values():walk(v,source)
        elif isinstance(x,list):
            for v in x:walk(v,source)
        elif isinstance(x,str):
            s=x.replace('\\','/');prefix=ROOT.as_posix()+'/'
            if s.lower().startswith(prefix.lower()):s=s[len(prefix):]
            if s.startswith(('work/','out/','character/','config/','projects/','docs/')) and '\n' not in s:
                paths.setdefault(s,set()).add(source)
    for p in list((ROOT/'projects').rglob('*.json'))+list((ROOT/'config').glob('*.json')):
        walk(json.loads(p.read_text('utf-8')),p.relative_to(ROOT).as_posix())
    records=[]
    for s,sources in sorted(paths.items()):
        p=ROOT/s
        if p.is_dir():state='directory_preserved'
        elif p.is_file():state='file_preserved'
        elif p.with_suffix(p.suffix+'.delta.zip').is_file():state='bin_archived_restore_before_use'
        else:state='historical_missing_or_not_a_file_path'
        records.append({'path':s,'status':state,'referenced_by':sorted(sources)})
    save(R/'production_sources/source_registry.json',records)
    hud=R/'sprites/ui_hud/provenance.json';v=json.loads(hud.read_text('utf-8'));v['notes']='사용자 수용 HUD의 실제 after PNG와 편집 인덱스. 비교용 before는 복사하지 않음.';save(hud,v)
    page=R/'sprites/index.html';s=page.read_text('utf-8')
    if 'ui_hud/' not in s:s+='<details><summary>최종 HUD 엠블럼</summary><p>수용된 제작 PNG. 해당 그래픽 자원은 최종 BIN과 일치함을 검사했습니다.</p>'+''.join(f'<img src="ui_hud/{p.name}">' for p in sorted((R/'sprites/ui_hud').glob('*_69_after.png')))+'<a href="ui_hud/provenance.json">출처와 검사</a></details>'
    page.write_text(s,'utf-8')
    groups=[('최종·운영',['FINAL_','STATUS','NEXT_','PRODUCTION_','COMMANDS','DECISIONS','TEST_','STORAGE','PROJECT_']),('기술·스타일',['VERSION_','RESEARCH','SPRITE_','ART_']),('리코',['RIKO_']),('시부키·아머',['SHIBUKI_']),('공통 UI·한글·음향',['CLICHE_','KOREAN_','HUD_','LOADING_','UI_'])]
    lines=['# 제작 자료 색인','','현재 기준은 [FINAL_RELEASE.md](FINAL_RELEASE.md)다. 아래 상세 문서의 당시 미완료/후보/다음 작업은 역사 기록이며 현재 완료 상태를 덮어쓰지 않는다.','','## 경로 안내','','| 자료 | 위치 |','| --- | --- |','| 최종 BIN·차이 백업·자원·스프라이트 | `out/ver_buki_riko/final_v1_0_0/` |','| 후보와 원래 승인 기록 | `projects/ver_buki_riko/*.json` |','| 아트 기준·팔레트·자원 매핑 | `config/*.json` |','| 제작 원본·검증·실행 증거 | `work/ver_buki_riko/`와 과거 `out/ver_buki_riko/` |','| 기존 포인터에서 찾은 제작 자료 목록 | [source_registry.json](../out/ver_buki_riko/final_v1_0_0/production_sources/source_registry.json) |','| 마지막 장기 상태 일지 | [STATUS_before_final_20261028.md](history/STATUS_before_final_20261028.md) |','','자료 목록의 `bin_archived_restore_before_use`는 삭제로 유실된 것이 아니라 같은 경로의 `.bin.delta.zip`에 보관된 BIN이다. `historical_missing_or_not_a_file_path`는 이번 정리로 없는 자료라고 단정하지 않는다. 오래된 계획 문자열과 이미 없던 경로도 포함한다.']
    used=set()
    for title,prefixes in groups:
        lines+=['',f'## {title}','']
        for p in sorted((ROOT/'docs').glob('*.md')):
            if p.name in used or not any(p.stem.startswith(x) for x in prefixes):continue
            used.add(p.name);head=next((x.strip('# ') for x in p.read_text('utf-8').splitlines() if x.startswith('# ')),p.stem)
            lines.append(f'- [{p.stem}]({p.name}) — {head}')
    (ROOT/'docs/REFERENCE_INDEX.md').write_text('\n'.join(lines)+'\n','utf-8')
    save(R/'environment.json',{'python':sys.version,'platform':platform.platform(),'packages':{k:importlib.metadata.version(k) for k in ['Pillow','numpy']},'voice_environment_note':'title_voice_env가 voice_env의 CUDA 의존성을 공유. work/tools의 환경·모델 캐시를 보존함.','ffmpeg_and_voice_pins_document':'docs/CLICHE_TITLE_VOICE.md','third_party_license_index':'docs/RESEARCH.md'})
    print(json.dumps({'source_references':len(records),'states':{x:sum(r['status']==x for r in records) for x in sorted({r['status'] for r in records})}}))

def inventory():
    total=0;count=0;dirs={};links=0
    for base,sub,files in os.walk(ROOT,followlinks=False):
        sub[:]=[d for d in sub if not (Path(base)/d).is_symlink()]
        for name in files:
            p=Path(base)/name
            if p.is_symlink():links+=1;continue
            size=p.stat().st_size;total+=size;count+=1;first=p.relative_to(ROOT).parts[0];dirs[first]=dirs.get(first,0)+size
    return {'total_bytes':total,'files':count,'top_level':dirs,'symlink_files_skipped':links}

def audit():
    protected=json.loads((D/'protected_before.json').read_text('utf-8'));result=[]
    for rec in protected:
        p=ROOT/rec['path'];same=p.is_file() and p.stat().st_size==rec['size'] and digest(p)==rec['sha256']
        result.append({'path':rec['path'],'unchanged':same})
    save(D/'protected_after.json',result)
    if not all(x['unchanged'] for x in result):raise ValueError('Protected input changed')
    final=json.loads((ROOT/'projects/ver_buki_riko/final_release.json').read_text('utf-8'))
    if digest(R/'game/shibuki_riko.bin')!=final['bin_sha256']:raise ValueError('Final game changed')
    old=json.loads((D/'inventory_before.json').read_text('utf-8'));new=inventory();save(D/'inventory_after.json',new)
    compact=json.loads((D/'compact_summary.json').read_text('utf-8'))
    summary={'before_bytes':old['total_bytes'],'after_bytes':new['total_bytes'],'net_saved_bytes':old['total_bytes']-new['total_bytes'],'bin_compaction':compact,'protected_files':len(result),'all_protected_unchanged':True,'final_bin_sha256':final['bin_sha256'],'originals_and_saves_removed':False,'gameplay_changes_this_turn':False,'new_runtime_tests':False,'partial_export_preserved':'work/maintenance/final_20261028/partial_export_before_canvas_fix','partial_export_note':'재귀 삭제가 자동 정책 검토에서 차단되어 첫 미완성 추출 폴더는 유지. 최종 모음과 분리함.'}
    summary['cache_policy']='재제작 의존성이 있는 로컬 환경·모델 및 원래 아트·캡처·로그 보존'
    save(D/'completion.json',summary)
    print(json.dumps(summary,ensure_ascii=False))

def documents():
    m=json.loads((D/'completion.json').read_text('utf-8'));c=m['bin_compaction'];g=1024**3
    text=f'''# 최종 보관과 공간 정리 검사

2026-10-28. 사용자 요청에 따라 첫 버전을 완성본으로 고정하고 제작 자료를 정리했다. 게임 내용은 마지막 수용본과 바이트 동일하다.

## 용량

| 항목 | 결과 |
| --- | ---: |
| 정리 전 프로젝트 | {m['before_bytes']/g:.3f} GiB |
| 정리 후 측정값 | {m['after_bytes']/g:.3f} GiB |
| 순절감 | {m['net_saved_bytes']/g:.3f} GiB |
| 정리한 과거 전체 BIN | {c['count']}개 / {c['before']:,} bytes |
| 같은 BIN의 차이 백업 | {c['after']:,} bytes / {c['after']/1024**2:.2f} MiB |
| 원래 BIN 복원 해시 일치 | 123/123 |
| 원본·설정화·에뮬레이터·저장 보호 파일 | {m['protected_files']}개 / 전부 해시 동일 |

파일의 논리적 길이 합계이며 링크 파일은 제외했다. 기록·코드 스냅샷을 쓰면서 소량 늘어날 수 있다. 최종 실행용 사본·스프라이트·기록 추가분을 차감한 순절감이다. 근거는 [completion.json](../work/maintenance/final_20261028/completion.json), `inventory_before.json`, `inventory_after.json`이다.

## 지운 것과 남긴 것

각 과거 BIN을 먼저 원본과 비교하여 변경된 **2352바이트 원시 섹터 전체**를 ZIP에 넣고, 원본+ZIP으로 복원한 전체 해시가 기존 manifest와 동일할 때만 해당 BIN 하나를 제거했다. 실제 EDC/ECC와 XA 섹터 바이트까지 그대로 복구한다. 과거 폴더의 CUE·manifest·그림·로그는 남겼으므로 예전 CUE 실행 전에 BIN을 복원해야 한다.

유지한 전체 BIN은 `final_v1_0_0/game`, 마지막 제작 빌드 `cliche_title_voice_20261028T071319364977Z`, 직전 복구 빌드 `shibuki_voice_mute_20261028T064914983985Z`다. 새 `final_release.json`과 최신 통합 포인터를 정리 도구의 보호 목록에 추가해, 오래된 기능별 포인터 때문에 최종본을 지우지 않게 했다.

미국판·일본판 게임, CUE, 설정화, BIOS·제공 에뮬레이터, 모든 저장 카드/상태, 작업 기준 사본은 보존했다. 모든 기존 아트·캡처·로그도 남겼다. 로컬 모델·가상환경은 타이틀 음성 재제작 의존성이 있어 유지한다. 과거 Voice Conversion 환경을 이름만 보고 지우면 현재 TTS의 CUDA 공유 의존성도 깨질 수 있다.

첫 스프라이트 추출에서 정적 합성 캔버스가 일부 조립 사각형보다 작아 중단됐다. 자동 정책 검토가 그 임시 폴더의 재귀 삭제를 차단했으므로 `work/maintenance/final_20261028/partial_export_before_canvas_fix`에 분리 보존했다. 최종 exporter는 전체 원래 사각형의 합집합으로 캔버스를 계산해 재실행 완료했으며, 최종 모음은 이 미완성 폴더를 참조하지 않는다.

## 검사 범위

- 압축/복원·경로/해시·손상/덮어쓰기/링크 거부·최종본 보호와 시트 검사 **16개 통과**. [targeted_tests.log](../work/maintenance/final_20261028/targeted_tests.log).
- 123개 백업 각각 복원 해시 검사 후 삭제. [compact_results.jsonl](../work/maintenance/final_20261028/compact_results.jsonl).
- 최종 BIN은 원래 수용본과 동일. 별도 복원 ZIP은 1,873,212 bytes, 변경 섹터 1,763개이며 전체 복원 해시 일치. [recovery.json](../out/ver_buki_riko/final_v1_0_0/recovery.json).
- 보호 입력 269개 전후 해시 동일. [protected_after.json](../work/maintenance/final_20261028/protected_after.json).
- 최종 변경 ARC/실행 파일 91개와 출처/해시 기록. [resource_manifest.json](../out/ver_buki_riko/final_v1_0_0/resources/resource_manifest.json).
- 최종 PNG 인덱스 시트 13그룹 왕복, 아머 2자원 각각7,296정적 조합 범위 검사. [sprites/manifest.json](../out/ver_buki_riko/final_v1_0_0/sprites/manifest.json). 대표 미리보기도 직접 열어 확인했다.
- 실제 재부팅·새 플레이 검사는 이번 정리에서 반복하지 않았다. 새 게임 내용 변경 없이 이전 사용자 수용을 보존한 작업이다.

## 복원 방법

지원 원본 `MegaMan X4.bin`과 해당 `.bin.delta.zip`을 프로젝트에 두고 루트에서 실행한다. 원본 SHA-256은 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`여야 한다.

실제로 실행한 최종 차이 백업 검증:

```powershell
python scripts/compact_builds.py verify --archive out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin.delta.zip
```

전체 BIN이 없을 때의 복원 절차(구현된 `restore`; 기존 파일이 있으면 덮어쓰기를 거부):

```powershell
python scripts/compact_builds.py restore --archive out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin.delta.zip
```

예전 빌드도 해당 폴더의 ZIP 경로를 넘기면 ZIP에 기록된 원래 BIN 위치로 복원된다. 출력 SHA-256을 그 폴더 manifest와 확인한 다음 CUE를 연다. 원본이나 ZIP을 잃으면 복원할 수 없으므로 둘 다 보존한다. ZIP도 공개용으로 자동 승인된 자료가 아니다.

고정 보관 폴더의 `code_snapshot.zip`에는 코드·설정·프로젝트 포인터·문서의 로컬 사본이 있고, `release_manifest.json`/`checksums.sha256`에는 보관 파일 해시가 있다. 오래된 제작 체인을 모두 재실행하지 않아도 원본+최종 차이 ZIP만으로 동일 최종 게임을 복구할 수 있다. 스프라이트를 새로 편집·빌드하는 경로는 역사 제작 자료와 별도로 연결한다.
'''
    (ROOT/'docs/FINAL_ARCHIVE_AUDIT.md').write_text(text,'utf-8')
    status=f'''# 프로젝트 상태

**2026-10-28 — 시부키 / 리코 모드 v1.0.0 사용자 수용 기준 완료, 제작 인계와 정리 완료.** 기존 제작 단계는 `EXPANSION`, 완료 상태는 `USER_ACCEPTED_COMPLETE`, 활성 제작 작업은 없음. 다음은 사용자 버그 제보 또는 나나 / 린 제작 요청이다.

## 기준과 승인

- 플랫폼: PS1 미국판 `SLUS_005.61`. 원본 `MegaMan X4.bin` SHA-256 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`.
- 최종 BIN SHA-256 `{m['final_bin_sha256']}`. [고정 CUE](../out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.cue).
- 사용자 “그럼 이제 부키 / 리코 모드는 완성한걸로 치자”를 완료 수용으로 기록. 이후 버그 제보 시 별도 수정본을 만든다.
- 이번 승인: 시행착오·팁·최종본 정리, 스프라이트 수집, 불필요한 중간 파일 정리. 외부 공개·업로드와 나나 / 린 대량 제작은 실행하지 않았다.

## 결과와 근거

- [완료 범위·실행·스프라이트 안내](FINAL_RELEASE.md), [기계 판독 최종 포인터](../projects/ver_buki_riko/final_release.json).
- [스프라이트 모음](../out/ver_buki_riko/final_v1_0_0/sprites/index.html): 최종 자원 재추출, 원래 크기/원점/팔레트·파츠 보존. 리코 몸체266+정적2, 기본/아머228참조씩. 참조 수와 고유 자세 수는 구분한다.
- [시행착오](PRODUCTION_LESSONS.md), [나나 / 린 작업 순서](NEXT_VARIANT_PLAYBOOK.md), [문서·자료 색인](REFERENCE_INDEX.md).
- [공간 정리 검사](FINAL_ARCHIVE_AUDIT.md): 약 {m['before_bytes']/g:.1f}→{m['after_bytes']/g:.1f} GiB, 약 {m['net_saved_bytes']/g:.1f} GiB 절감. 과거 BIN123개 복원 해시 확인 후 차이 백업 보관. 보호 파일269개 전부 동일.
- 관련 검사16개 통과, 시트13그룹 왕복·아머 정적 조립 검사 완료. 게임 내용이 동일하므로 이번에는 새 실기 테스트를 추가하지 않았다.

## 남은 범위와 다음 작업

현재 승인 범위에서 제작 차단 요인 없음. 영상 교체는 범위 밖. 별도 블랙 팔레트, 전체 한글543페이지·엔딩·모든 게임 상황의 전수 검수는 완료로 주장하지 않는다. 상세 한계는 완료 안내와 기존 검사 기록에 있다.

`ver_rin_nana`는 제작 준비 문서만 완료했다. 후속 요청 시 풀네임·제작 순서·부분 파츠·음성 정책 등을 해당 버전에서 결정한다. 두 버전의 출력과 승인 상태를 합치지 않는다.

기존 `current_build.json`/기능별 candidate는 역사적 제작 포인터일 수 있다. 현재 기준은 `project.json.latest_integrated_build`와 `final_release.json`이다. 긴 상태 일지는 원형 그대로 [history/STATUS_before_final_20261028.md](history/STATUS_before_final_20261028.md)에 보존했다.
'''
    (ROOT/'docs/STATUS.md').write_text(status,'utf-8')
    (R/'README.md').write_text('''# ClichéX4 시부키 / 리코 v1.0.0

사용자 수용 기준 완성본. 실행은 `game/shibuki_riko.cue`, 스프라이트 열람은 `sprites/index.html`입니다.

- `game/`: 마지막 수용본의 동일 BIN/CUE, 실제 디코딩 타이틀 콜 WAV, 원본 기반 차이 백업.
- `sprites/`: 최종 인덱스 PNG·시트·원점·팔레트·파츠와 정적 합성. `ui_hud/`도 포함.
- `resources/`: 최종 게임에서 추출한 변경 ARC·실행 파일과 출처 목록.
- `production_sources/`: 역사적 Riko 편집 마스터 사본과 원래 제작 자료243곳의 색인. 최종 그림과 구별하세요.
- `code_snapshot.zip`: 코드·설정·문서의 로컬 보관 사본. 공개용으로 정리한 패키지가 아닙니다.
- `release_manifest.json`, `checksums.sha256`: 최종 자료 목록·해시. `recovery.json`: 게임 복원 백업의 검증 기록.

[자세한 완료 안내](../../../docs/FINAL_RELEASE.md) · [나나 / 린 인계](../../../docs/NEXT_VARIANT_PLAYBOOK.md) · [시행착오](../../../docs/PRODUCTION_LESSONS.md) · [복원](../../../docs/FINAL_ARCHIVE_AUDIT.md)

원본 게임·이 폴더·설정화·저장 파일을 그대로 GitHub에 업로드하지 않습니다. 공개할 자료는 출처/권리/개인 경로를 확인해 별도로 선택합니다. 이번 작업에서 업로드는 하지 않았습니다.
''','utf-8')
    print('Wrote final status, archive audit, release README')

def snapshot():
    selected=[]
    for name in ['src','scripts','tests','config','projects','docs']:
        selected += [p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.json','.md','.toml','.txt','.yaml','.yml')]
    selected += [ROOT/p for p in ['README.md','AGENTS.md','.gitignore']]
    dest=R/'code_snapshot.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,9) as z:
        for p in sorted(set(selected)):z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for p in set(selected):assert hashlib.sha256(z.read(p.relative_to(ROOT).as_posix())).hexdigest()==digest(p)
    records=[]
    for p in sorted(R.rglob('*')):
        if p.is_file() and p.name not in ['checksums.sha256','release_manifest.json']:
            records.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)})
    save(R/'release_manifest.json',{'version':'1.0.0','final_pointer':'projects/ver_buki_riko/final_release.json','local_only':True,'files':records,'source_snapshot_file_count':len(set(selected)),'snapshot_verified_against_source':True})
    (R/'checksums.sha256').write_text(''.join(f'{r["sha256"]}  {r["path"]}\n' for r in records),'utf-8')
    print(json.dumps({'files':len(records),'snapshot_files':len(set(selected)),'snapshot_bytes':dest.stat().st_size}))

if __name__=='__main__':
    {'references':references,'audit':audit,'documents':documents,'snapshot':snapshot}[sys.argv[1]]()
