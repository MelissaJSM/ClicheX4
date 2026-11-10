"""Publish local review artifacts and activate only verified local build pointers."""
from pathlib import Path
import json,shutil,sys,html
from PIL import Image,ImageDraw
from black_ui import ROOT,H
from src.psx_disc import file_hash

def load(p):return json.loads(p.read_text('utf8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
protected=load(H/'protection_before_black.json')['files'];updates=set();results=load(H/'black_builds.json')
for name,q in protected.items():assert file_hash(ROOT/name)==q['sha256'],name
for b in results:
    mode=b['mode'];d=H/mode;out=ROOT/Path(b['cue']).parent
    assert file_hash(ROOT/Path(b['cue']).with_suffix('.bin'))==b['sha256']
    review=out/'review';review.mkdir(exist_ok=False)
    src=d/('black_proposal' if mode=='ver_rin_nana' else 'prepared_assets_v2')
    for path in src.glob('*.png'):shutil.copyfile(path,review/path.name)
    if mode=='ver_buki_riko':shutil.copyfile(d/'regions_v2/review.png',review/'comparison.png')
    else:shutil.copyfile(d/'black_proposal/review.png',review/'comparison.png')
    shutil.copyfile(d/'black_proposal/cpu_verification.json',review/'cpu_verification.json')
    name='린' if mode=='ver_rin_nana' else '리코'
    page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>블랙 {name} · 대화와 헌터베이스</title>
<style>body{{background:#192331;color:#eff4fc;font:17px/1.6 sans-serif;margin:30px}}a{{color:#b6ddff}}img{{image-rendering:pixelated;max-width:100%}}.grid{{display:flex;flex-wrap:wrap;gap:20px}}figure{{margin:0;background:#253043;padding:12px}}.pair{{display:flex;align-items:end;gap:14px}}.pair img{{max-width:224px}}small{{display:block;color:#cad4e1}}button{{padding:8px 14px;margin:8px}}</style>
<h1>블랙 {name} — 대화창·헌터베이스</h1><p>BIN 자산을 같은 좌표·배율로 복원한 비교입니다. 실제 플레이 캡처가 아닙니다. 일반형(왼쪽) / 블랙(오른쪽).</p>
<p><a href="../{Path(b['cue']).name}">새 CUE</a> · <a href="../../../../docs/BLACK_ILLUSTRATIONS_20261108.md">변경·검사·남은 범위</a></p>'''
    if name=='리코':page+='<p>흰 점이 생기는 단순 반전을 피하려고 외투·안쪽 옷·머리 하이라이트의 인덱스를 분리했습니다. 일반 리코도 일부 어두운 색조가 조정됐습니다. 형태·크기·피부·표정 구조는 유지했습니다. 아래 첫 비교는 이전 일반형 / 조정 일반형 / 블랙입니다.</p>'
    else:page+='<p>일반 린의 그림과 색상표는 그대로입니다. 블랙에서만 적색 강조가 표시됩니다.</p>'
    page+='<img src="comparison.png"><h2>헌터베이스 14그림</h2><div class="grid">'
    for group,count in [('hq',14),('dialogue',3)]:
        if group=='dialogue':page+='</div><h2>대화 3표정</h2><div class="grid">'
        for n in range(count):
            page+=f'<figure><figcaption>{group} {n:02}</figcaption><div class="pair">'
            for var in ['normal','black']:
                fn=f'{group}_{n:02}_{var}.png';assert(review/fn).exists()
                im=Image.open(review/fn);page+=f'<div><img src="{fn}" width="{im.width*2}"><small>{var}</small></div>'
            page+='</div></figure>'
    page+='</div><p>새 CUE 재시작 → 게임 내 메모리카드 불러오기로 블랙 상태의 대화, 눈·입 동작, 헌터베이스 출격과 페이드를 확인해 주세요. 옛 F3는 예전 코드와 그림을 복원할 수 있습니다. 나나·시부키 아머별 헌터베이스 전신 의상은 별도 미완료 범위입니다.</p></html>'
    (review/'index.html').write_text(page,'utf8')
    cp=ROOT/'projects'/mode/'current_build.json';pj=cp.with_name('project.json');old=load(cp);meta=load(pj)
    assert old==load(d/'source.json')['pointer']
    write(d/'current_build_before_black.json',old);write(d/'project_before_black.json',meta)
    new={**old,'task':'illustration_armor_black_20261108','stage':'BLACK_UI_APPLIED_X_HQ_ARMOR_PENDING','build':out.relative_to(ROOT).as_posix(),'cue':b['cue'],'sha256':b['sha256'],'previous_pointer':(d/'current_build_before_black.json').relative_to(ROOT).as_posix(),'status_report':'docs/BLACK_ILLUSTRATIONS_20261108.md','black_ui_report':'docs/BLACK_ILLUSTRATIONS_20261108.md','black_ui_review':(review/'index.html').relative_to(ROOT).as_posix(),'black_ui_runtime_verified':False,'black_ui_user_accepted':False,'black_ui_static_verified':True,'x_hunter_armor_outfits_implemented':False,'current_session':None,'running_bin_sha256':None,'current_runtime_state':'새 CUE 적용. 사용자 실기 확인 대기, 자동 입력 없음.','runtime_verification_scope':'블랙 UI는 정적 조립·MIPS 비교·BIN 재추출 검사 완료. 실제 대화/헌터베이스/페이드 미확인. 나나·시부키 아머별 HQ 전신은 미적용.','next_action':'사용자 블랙 대화·헌터베이스 확인. 나나·시부키 아머별 HQ 전신의 추가 저장/선택 방식 검증.','user_accepted':False}
    write(cp,new);meta.update(active_task=new['task'],active_substage=new['stage'],latest_integrated_build=new['build'],latest_integrated_bin_sha256=new['sha256'],black_ui_report=new['status_report']);write(pj,meta)
    updates.update([cp.relative_to(ROOT).as_posix(),pj.relative_to(ROOT).as_posix()])
    manifest=load(out/'manifest.json');manifest['review']='review/index.html';write(out/'manifest.json',manifest)
for name,q in protected.items():
    if name not in updates:assert file_hash(ROOT/name)==q['sha256'],name
status=ROOT/'docs/STATUS.md';shutil.copyfile(status,H/'STATUS_before_black.md');shutil.copyfile(H/'status_next.md',status)
receipt={'builds':results,'protected_files_unchanged':len(protected)-len(updates),'metadata_updates':[{'file':n,'before':protected[n]['sha256'],'after':file_hash(ROOT/n)}for n in sorted(updates)],'originals_references_releases_saves_preserved':True,'emulator_inputs_sent':False,'F1_F3_used':False,'runtime_verified':False,'x_hunter_armor_outfits_implemented':False}
write(H/'black_application.json',receipt)
print(json.dumps({'builds':results,'protected_files_unchanged':receipt['protected_files_unchanged']}))
