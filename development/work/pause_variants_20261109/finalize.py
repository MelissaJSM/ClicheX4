"""Publish local pause comparison and update active pointers after checks."""
from pathlib import Path
import json,shutil
from PIL import Image
from prepare import ROOT,H,MODES,save_json,entry,aliased_composition,render_static_rgba
from src.psx_disc import file_hash
from scripts.prepare_ui_revision import pause_background
import struct

def load(p):return json.loads(p.read_text('utf8'))
protected=load(H/'protection_before.json')['files'];results=load(H/'builds.json');updates=set()
for name,q in protected.items():assert file_hash(ROOT/name)==q['sha256'],name
for result in results:
    mode=result['mode'];d=H/mode;out=ROOT/Path(result['cue']).parent;review=out/'review'
    assert file_hash(ROOT/Path(result['cue']).with_suffix('.bin'))==result['sha256']
    xname,zname=('하나코 나나','아오쿠모 린') if mode==MODES[0] else ('텐코 시부키','유즈하 리코')
    for name in ['PL00_U.ARC','PL01_U.ARC']:
        old=(d/'originals'/name).read_bytes();c=aliased_composition(struct.pack('<I',4)+entry(old,18),0,10)
        im,_=render_static_rgba(entry(old,0x10007)[12288:],c,{0:struct.unpack_from('<16H',entry(old,17),320)})
        bg=pause_background(old);bg.alpha_composite(im,(32,144));bg.save(review/f'before_{name[:4]}.png')
    page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>{xname} · {zname} 일시정지</title>
<style>body{{background:#18212d;color:#edf3fa;font:17px/1.6 sans-serif;margin:28px}}a{{color:#aeddff}}img{{image-rendering:pixelated;max-width:100%}}.grid{{display:flex;flex-wrap:wrap;gap:18px}}figure{{margin:0;padding:12px;background:#263345}}figure img{{display:block}}small{{color:#c2d1e3}}</style>
<h1>{xname} · {zname} — 일시정지 일러스트</h1>
<p>최신 BIN의 자원을 복원한 비교입니다. 아래 메뉴는 정적 배경과 실제 MIPS 실행이 만든 초상화 표시 결과를 합성했습니다. <strong>실제 플레이 캡처는 아니며 무기 이름·숫자 등 다른 동적 항목은 생략했습니다.</strong></p>
<p><a href="../{Path(result['cue']).name}">최신 CUE</a> · <a href="../../../../docs/PAUSE_VARIANTS_20261109.md">적용 범위·검증·실기 확인 안내</a></p>
<h2>전체 변형</h2><p>기본형 / 머리 / 몸 / 머리+몸 / 얼티밋 전(재킷) / 후(수영복) / 일반 / 블랙 순서입니다.</p><img src="review.png">
<h2>실제 메뉴 영역에 배치</h2><div class="grid">'''
    for file,states in [('PL00',['기본형','머리 파츠','몸 파츠','머리+몸 파츠']),('PL02',['얼티밋 획득 전 — 재킷','얼티밋 획득 후 — 수영복']),('PL01',['일반','블랙'])]:
        for k,label in enumerate(states):
            who=zname if file=='PL01' else xname
            page+=f'<figure><figcaption>{who} · {label}</figcaption><img width="640" src="menu_{file}_{k}.png"></figure>'
    page+='</div><h2>기존 기본형과 위치 비교</h2><div class="grid">'
    for file,who in [('PL00',xname),('PL01',zname)]:
        for fn,label in [(f'before_{file}.png','이전'),(f'menu_{file}_0.png','수정')]:
            page+=f'<figure><figcaption>{who} · {label}</figcaption><img width="640" src="{fn}"></figure>'
    page+='</div><p>64×80 창과 원래 사선 경계, 메뉴 좌표를 유지했습니다. 팔·다리 파츠는 이 얼굴·상반신 그림에 해당 부위가 보이지 않아 머리/몸 조합과 같은 그림을 사용합니다.</p><p>새 CUE로 다시 부팅하고 게임 안의 카드 저장을 불러와 확인해 주세요. 이전 F3는 이전 코드와 그래픽을 복원할 수 있습니다. 나나·시부키의 아머별 헌터베이스 전신 의상은 아직 별도 미완료입니다.</p></html>'
    (review/'index.html').write_text(page,'utf8')
    cp=ROOT/'projects'/mode/'current_build.json';pj=cp.with_name('project.json')
    old=load(cp);meta=load(pj);assert old==load(d/'pointer.json')
    save_json(d/'project_before.json',meta)
    new={**old,'task':'pause_variants_20261109','stage':'PAUSE_VARIANTS_APPLIED_USER_REVIEW',
        'build':out.relative_to(ROOT).as_posix(),'cue':result['cue'],'sha256':result['sha256'],
        'previous_pointer':(d/'pointer.json').relative_to(ROOT).as_posix(),
        'status_report':'docs/PAUSE_VARIANTS_20261109.md','pause_variants_report':'docs/PAUSE_VARIANTS_20261109.md',
        'pause_variants_review':(review/'index.html').relative_to(ROOT).as_posix(),
        'pause_variants_static_verified':True,'pause_variants_runtime_verified':False,'pause_variants_user_accepted':False,
        'current_session':None,'running_bin_sha256':None,'current_runtime_state':'새 CUE 적용. 사용자 일시정지 실기 확인 대기. 자동 입력 없음.',
        'runtime_verification_scope':'두 모드 각각 MIPS 상태 288·다른 위젯 468검사와 전체 BIN 재추출 검증. 이번 일시정지 실기 관찰은 미실행.',
        'next_action':'일시정지에서 파츠/얼티밋 전후/블랙, 위치와 메뉴 가림 확인. X 아머별 헌터베이스 전신은 별도 작업.',
        'x_hunter_armor_outfits_implemented':False,'user_accepted':False}
    save_json(cp,new)
    meta.update(active_task=new['task'],active_substage=new['stage'],latest_integrated_build=new['build'],
        latest_integrated_bin_sha256=new['sha256'],pause_variants_report=new['status_report'])
    save_json(pj,meta);updates.update([cp.relative_to(ROOT).as_posix(),pj.relative_to(ROOT).as_posix()])
    mf=load(out/'manifest.json');mf['review']='review/index.html';save_json(out/'manifest.json',mf)
for name,q in protected.items():
    if name not in updates:assert file_hash(ROOT/name)==q['sha256'],name
save_json(H/'application.json',{'builds':results,'protected_files_unchanged':len(protected)-len(updates),
    'metadata_updates':[{'file':n,'before':protected[n]['sha256'],'after':file_hash(ROOT/n)}for n in sorted(updates)],
    'originals_references_releases_saves_preserved':True,'emulator_input_sent':False,'F1_F3_used':False,
    'runtime_verified':False,'x_hunter_armor_outfits_implemented':False})
print('Activated two verified local builds; protected',len(protected)-len(updates),'files.')
