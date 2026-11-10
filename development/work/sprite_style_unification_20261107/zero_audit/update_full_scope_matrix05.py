"""Link BR16/RN19 and existing runtime evidence; no art/game checks are rerun."""
from pathlib import Path
import copy,hashlib,html,json,os,re
ROOT=Path(__file__).resolve().parents[3]
D=Path(__file__).parent;B=D.parent;N=B/'nana_audit';H=B/'shibuki_audit'
P=D/'full_scope_matrix04/coverage.json';O=D/'full_scope_matrix05'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
assert sha(P)=='786579fde952edd92ea36b9d765c5b06f7cd8a21ea1b10559dc7227cc030ed2e'
j=read(P);old_evidence=copy.deepcopy(j['evidence']);old_zero=copy.deepcopy([c for c in j['cells']if c['character']in('riko','rin')])
j['previous_snapshot']={'path':P.relative_to(ROOT).as_posix(),'sha256':sha(P)}
for e in old_evidence.values():assert sha(ROOT/e['path'])==e['sha256'],e['path']
def ev(key,p,purpose,expected=None):
    h=sha(p)
    if expected:assert h==expected,str(p)
    j['evidence'][key]={'path':p.relative_to(ROOT).as_posix(),'sha256':h,'purpose':purpose}
def st(status,label,refs):return dict(status=status,label=label,refs=refs)

for key,project in [('br16','ver_buki_riko'),('rn19','ver_rin_nana')]:
    tag='br_v16'if key=='br16'else'rn_v19';version=16 if key=='br16'else 19
    planp=B/f'staging_{tag}.json';discpath=ROOT/f'out/{project}/sprite_style_unification_20261107_v{version}/manifest.json'
    plan=read(planp);disc=read(discpath)
    ev(key,planp,'현재 통합 계획. 이 집계는 빌드/게임을 다시 실행하지 않았다.')
    ev(key+'_disc',discpath,'전체 디스크/재추출 기존 빌드 검증 기록.')
    native=B/f'staging_{tag}_native_checks.json';assert read(native)['passed']
    ev(key+'_native',native,'현재 통합 자원의 원 MIPS/GPU 기존 검사 기록.')
    for n,v in plan['resources'].items():assert v['after']==disc['resources'][n]['after']
    if 'prior_integration'not in j:j['prior_integration']=copy.deepcopy(j['integration'])
    if key=='br16':j['prior_integration']=copy.deepcopy(j['integration']);j['integration']={}
    j['integration'][key]={k:plan[k]for k in('output','resources')}
    j['integration'][key]['bin_sha256']=disc['modified_bin']['sha256']

ev('nana_ledger13',N/'scope_summary_v13/manifest.json','최신 제작 장부. 새 원화×폼388·효과파생36은 완료율이 아니다.','982e8676161fc03c7611f1f10a28f4a68a619b484b8a63e121ad87080afaad29')
ev('shibuki_ledger19',H/'fullform_ledger19.json','실제 현재 자원을 다시 읽은 고유키 장부. 앞선 단순 상태갱신 장부와 구분.')
ev('shibuki_unique19',H/'unique_art_keys19.json','고유 표시형태772키의 분류 근거. 새 원화 장수나 완료율이 아니다.')
ev('shibuki_ultimate_ladder_frozen',H/'prepared_ultimate_ladder01/FROZEN.json','사다리14 최종 동결·독립·원 MIPS·실제열람 결속.','71cbe5c072c5e5a2bed46397880feefe1b1c01fc2e5fabf0a3af83fe4239691d')
ev('nana_ultimate_hurt_frozen',N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/FROZEN.json','Ultimate 피격13 최종 동결. 새몸체4·효과파생9 구분.','73771c951309e07a56db31b3da3f887c1374ed219c74365bf7bcaf6b3c88799a')
ev('nana_ultimate_hurt_reader',D/'nana_ultimate_hurt13_independent01/report.json','65목표·1075비대상층·고유효과/66·135px오라·416부분RGBA 독립 읽기.','bb57d92bb2abbbef3c86ff65d8ffeac772b76a4faa4842d2fac687ed7f74b3cf')
ev('nana_ultimate_hurt_final_art',D/'nana_ultimate_hurt13_independent01/visual_review.json','독립 최종5판 실제 열람.','1cd0b4bf7b2c53d995b7747a5725050aa8470342311d68cf2cfbb9abcb6bb78d')
rp=B/'runtime/nana_ultimate_hurt19_summary.json';r=read(rp)
ev('nana_ultimate_hurt19_runtime',rp,'획득 후233..236 실제160창·루트12판, 미확정0. 획득 전/전체13 실기 아님.')
assert r['disc_sha256']==j['integration']['rn19']['bin_sha256']=='383cd66528a25abf1bef08b4791824d52d3ae676b8e09af567fcae36447cea7c'
assert r['asset_sha256']==j['integration']['rn19']['resources']['PL02_U.ARC']['after']
assert r['actual_captures']==160 and r['root_viewed_boards']==12
assert r['verified_new_references']==list(range(233,237)) and not r['unknown_events']
assert r['active_pointer_changed']is r['f1_f3_used']is r['memory_written']is False
for key in('observer','actual_review','root_review','close','protection'):
    e=r[key];ev('nana_hurt19_'+key,ROOT/e['path'],'RN19 기존 실행 증거 '+key,e['sha256'])
assert read(ROOT/r['protection']['path'])['passed']
album=ROOT/'out/sprite_style_unification_20261107/review_v20'
ev('album20',album/'manifest.json','BR16/RN19 실제 BIN 재추출 모음집 4510표시/28폼/2310변경표시. 미술 완료율 아님.')
ev('album20_browser',album/'browser_checks.json','기존 브라우저 검사 기록. 이번 집계는 브라우저를 다시 실행하지 않았다.')
al=read(album/'manifest.json');ab=read(album/'browser_checks.json');assert ab['passed']
assert sum(v['references']for v in al['counts'].values())==4510
assert sum(v['forms']for v in al['counts'].values())==28
assert sum(v['new_changed_references']for v in al['counts'].values())==2310
assert al['sources']['ver_buki_riko']['sha256']==j['integration']['br16']['bin_sha256']
assert al['sources']['ver_rin_nana']['sha256']==j['integration']['rn19']['bin_sha256']
j['current_album']={'evidence':'album20','browser_evidence':'album20_browser','display_records':4510,'forms':28,'changed_display_records':2310,'completion_percentage':None}

ev('nana_ceremony_sources',D/'nana_ultimate_ceremony_sources01/report.json','역사 원화/원타일에서130·131·134·140·157·158 재구성, 현재40표시 실제5판.','142b03a3788078269086f05f884c7e523add8a55e550e1b51b6beb90aba5e4a7')
ev('nana_ceremony_138139',D/'nana_ultimate_ceremony_sources02/coordinate_report.json','후폼153px 차이는 상체·의상, 원US 자세와 역사 Nana −1y 정책 구분.','bbfa5e24c05f9a47f1aab3ad630bba4da05695d3a9e36fa2cd6795ced6ce8a36')
ev('nana_ceremony_new_art',D/'nana_ultimate_ceremony_sources02/visual_review.json','새133/135/136/137 두 의상 초기등록4판과 현재138/139대조1판 실제 정적 열람.','06fe97e4756eed234775948fb6cab71fb41c94b27868d44ce6c464d91b52466b')
ev('nana_ladder_sources',D/'nana_ladder_relations01/report.json','현재 기본/포스14 공유·4반전·사격총구 관계의 읽기 조사.','caa6cb6318a631966d2029edf88f7f8b3158a81ff5b9c9edbf6fc1f3d5e8b4c9')
ev('nana_ladder_registration',B/'root_nana_ladder/contact_registration02/registration.json','루트가 제작 중인8고유몸체×2의상 손발 정합. 미패킹 후보.')
ev('shibuki_hurt_sources',D/'shibuki_hurt_sources01/report.json','두 ARC 실제 효과/실루엣 원자료 읽기; 나나의 규칙과 동일하다고 가정하지 않음.','202898054ae9061a626b1a9088bfde79bf3ef15339963acfc3f4d3d0c49b348c')
ev('shibuki_hurt_first_registration',H/'hurt_native01/report.json','106/110 기본·포스 새 원화 초기등록.')
ev('shibuki_hurt_second_registration',H/'hurt_native02/report.json','233/234 기본·포스 새 원화 초기등록.')
ev('shibuki_hurt_effect_candidate',H/'hurt_effect_probe01/manifest.json','새13 목표층 진단. 최종 패킹/동결과 구분.')

for c in j['cells']:
    ch,form,cat=c['character'],c['form'],c['category']
    if ch in('riko','rin'):continue
    c['evidence']+=['rn19','nana_ledger13']if ch=='nana'else['br16','shibuki_ledger19']
    if ch=='nana' and cat=='hurt' and form.startswith('ultimate'):
        c['states']=[st('integrated_new_art','새몸체4 동결·RN19 통합','106, 110, 233, 234'),st('integrated_derived_effect','새몸체 기반 효과파생9 동결·RN19 통합','107..109, 111..114, 235..236'),st('preserve_reviewed','기존 세부 보존 판단','120..125')]
        c['note']='Ultimate13은 c9e68442로 동결·RN19 통합했다. PL00과 다른109 양폼 실루엣,112..114 공통CLUT2,235/236 오라66/135px를 구분한다. 획득 후233..236만 이번 실기에서 확인했으며 재킷 및106..114 실기는 이번 범위가 아니다.'
        c['art_review']='최종5판 독립 열람과 동결문서의 루트 원순서 검토를 연결한다. RN19 획득 후160실창·루트12판에서 새 몸/오라의 추가 확정 문제를 찾지 못했다. 이 집계에서 게임 화면을 다시 보지 않았다.'
        c['evidence']+=['nana_ultimate_hurt_frozen','nana_ultimate_hurt_reader','nana_ultimate_hurt_final_art','rn19_native']
        c['runtime_coverage']={'evidence':'nana_ultimate_hurt19_runtime','observed_form':'ultimate_after','current_cell_observed':form=='ultimate_after','actual_captures':160 if form=='ultimate_after'else 0,'root_viewed_boards':12 if form=='ultimate_after'else 0,'new_references_with_successful_ram_gpu_sample':r['verified_new_references']if form=='ultimate_after'else[],'unverified_events':[],'all_60hz_transitions_verified':False,'all_partial_armor_combinations_verified':False}
        c['evidence']+=['nana_ultimate_hurt19_runtime','nana_hurt19_root_review','nana_hurt19_protection']
    elif ch=='nana' and cat=='ladder' and form in('base','fourth'):
        c['states']=[st('registered_candidate','새8몸체 정합·4반전 전개 준비','143..149, 151..154, 183'),st('art_in_progress','새 사격팔 제작·등록 중','150, 155')]
        c['note']='루트가8고유몸체×두 의상의 손발을 정합했고 공통층/사격팔을 제작 중이다. 현재978a에는 기존 사다리만 있으며 새14는 아직 미패킹·미동결·미통합이다. 기존 포스 명암10참조 복원은 전신 재작화와 구분한다.'
        c['art_review']='루트의 초기 등록 검토가 진행 중이다. 이 집계는contact_registration02 원화16표시를 새로 열람하지 않았으며, 최종 후보 검토가 남아 있다.'
        c['evidence']+=['nana_ladder_sources','nana_ladder_registration']
    elif ch=='nana' and cat=='ceremony' and form.startswith('ultimate'):
        c['states']=[st('registered_candidate','새4몸체 두의상 초기등록·공통층 정합','133, 135..137'),st('derived_pending','새133 실루엣/구체 연동 필요','130..131, 134'),st('needs_redraw','후속 새몸체/파생 제작 대기','138..139, 204..207'),st('needs_sync'if form=='ultimate_after'else'preserve_reviewed','대기와 몸225px 차이·동기화 필요'if form=='ultimate_after'else'현재 대기+먼지 동일, 보존','141'),st('review_before_decision','기존 상세·파생 규칙 확인 후 판단','156..158'),st('preserve_reviewed','대기 의존 기존 실루엣/사본 보존','140, 142'),st('effect_only','기존 순수 에너지/껍질 보존','126..129, 132, 159..161')]
        c['note']='133교체는130의 옛실루엣·131·134까지 연동해야 한다.136/137의46px 흰 선은 별도 원효과이며 총구 연결을 강제하지 않는다.138→139는 역사 Nana −1y 정책이고 원US 동일 자세 주장이 아니다. 후폼141 구형몸도 추가동기화 대상이다.157/158은156의 후광/에너지 파생이다.'
        c['art_review']='현재40표시5판과 새133/135/136/137 초기등록4판,138/139대조1판을 독립 실제 열람했다. 새 세부 방향은 개선됐으며137 손/권총 모듈 위치와 기존 흰 선 재합성은 별도 검증 필요. 최종 ARC/순서/게임 수용 전이다.'
        c['evidence']+=['nana_ceremony_sources','nana_ceremony_138139','nana_ceremony_new_art']
    elif ch=='shibuki' and cat=='ladder':
        if form.startswith('ultimate'):
            c['states']=[st('integrated_new_art','새14 동결·BR16 통합','143..155, 183')]
            c['note']='03a67562 사다리14는 독립·원MIPS/GPU·최종6판 검토 후 동결하여BR16에 통합했다. 실제 사다리 동선/게임 손발 접점은 아직 미검증이다.155는149새몸+반동팔의 제작정책, 원US155 자체의 동일복원은 아니다.'
            c['art_review']='동결문서의 루트94/96·독립 최종6판 열람과 기존 원MIPS를 계승한다. 추가 게임 미술 열람은 아직 없다.'
            c['evidence']+=['shibuki_ultimate_ladder_frozen','br16_native']
        else:c['note']='기본/포스14의 기존 새원화 통합을 유지한다. 별도Ultimate14도BR16에 통합됐으나 실제 사다리 전폼 검증이 완료된 것은 아니다.'
    elif ch=='shibuki' and cat=='hurt':
        if form in('base','fourth'):
            c['states']=[st('registered_candidate','새4몸체 등록·공통층 후보','106, 110, 233, 234'),st('derived_candidate','효과파생9 목표·패킹 진단 중','107..109, 111..114, 235..236'),st('integrated_new_art','기존 새 저체력 동결·통합','120..125')]
            c['note']='기본/포스 새13 목표층 등록 후 제작 담당이 고정은행 시험패킹 성공을 보고했다.234/235 원오라 뒤에 새공통몸체를 그리는 공유와 타일순열로 용량을 해결했으며, 최종 LOCK/독립검사·미술/동결은 아직이다. 현재BR16에는 기존381d만 있으며 시험후보를 완료 집계에 넣지 않는다.'
            c['evidence']+=['shibuki_hurt_first_registration','shibuki_hurt_second_registration','shibuki_hurt_effect_candidate']
        else:c['note']='Ultimate 피격의 별도 효과/의상 규칙을 읽어 원자료를 분리했다. 새 원화·패킹은 아직 별도 후속이다. 기존 새저체력120..125를 전체피격 완료로 확대하지 않는다.'
        c['evidence']+=['shibuki_hurt_sources']
    c['evidence']=list(dict.fromkeys(c['evidence']))

j['next_work']=[
 dict(owner='overhaul_ui',character='shibuki',scope='기본/포스 피격13, 이후Ultimate 피격13',stage='기본/포스 새4몸체·효과목표 시험패킹 성공 보고, 최종입력잠금/독립/미술검토 대기. Ultimate는 별도 규칙 조사 후 후속 제작',evidence=['shibuki_hurt_sources','shibuki_hurt_effect_candidate','shibuki_ledger19']),
 dict(owner='root',character='nana',scope='기본/포스 사다리143..155/183',stage='8고유몸체×2의상 손발 정합 완료, 공통층·사격팔·최종패킹/독립/미술 검토 남음',evidence=['nana_ladder_registration','nana_ladder_sources']),
 dict(owner='overhaul_audio',character='nana',scope='Ultimate 등장130..142 및 승리204..207·귀환156..158',stage='첫133/135/136/137 등록 중.130/131/134·후폼141 연동 포함,138/139 제작정책과별도효과 구분',evidence=['nana_ceremony_sources','nana_ceremony_new_art','nana_ledger13']),
 dict(owner='root',character='shibuki',scope='BR16 Ultimate 사다리14 대표 실기',stage='새14 동결·통합/원MIPS 완료, 실제 사다리 접근 동선·손발 접점 미검증',evidence=['shibuki_ultimate_ladder_frozen','br16_native','shibuki_ladder_route']),
 dict(owner='overhaul_ui + overhaul_audio',character='shibuki,nana',scope='남은 등장승리귀환·나나 기본/포스 저체력·특수85..99/208..212·차량/호버',stage='캐릭터/폼별 보존·신규제작·추가판단을 장부별 유지. 한 폼의 완료를 다른 폼에 확대하지 않음',evidence=['shibuki_ledger19','nana_ledger13']),
 *[p for p in j['next_work']if p['character']in('riko,rin','all')]]
j['completed_milestones_since_previous']=[
 dict(scope='Shibuki Ultimate사다리14 동결·BR16 통합',evidence=['shibuki_ultimate_ladder_frozen','br16','br16_native'],runtime_verified=False),
 dict(scope='Nana Ultimate피격13 동결·RN19 통합, 획득후233..236대표실기',actual_captures=160,root_viewed_boards=12,verified_new_references=r['verified_new_references'],unverified_events=0,evidence=['nana_ultimate_hurt_frozen','rn19','nana_ultimate_hurt19_runtime','nana_hurt19_root_review'],limits=r['limitations'],all_gameplay_verified=False)]
j['snapshot_summary']='BR16/RN19·review_v20 기준. Ultimate사다리14/피격13 통합과 Nana획득후233..236 대표실기를 연결. 새 Shibuki피격·Nana사다리/등장 후보는 완료 수와 구분. 전체 작업은 계속 진행 중.'
j['coverage_limits']=[x for x in j['coverage_limits']if not x.startswith('새 사다리 준비본03a67562와')]
j['coverage_limits']+=['BR16 새 Ultimate사다리14는 통합·정적/원MIPS까지이며 대표게임 접점은 미검증이다.',
 'RN19 새Ultimate피격13 중 실제관측은 획득후233..236만. 재킷·106..114·모든방향/피해원/60Hz전환 전수는 아니다.',
 'RN19 첫 일시정지 메뉴160기록은 성공근거에서 제외하고 실제플레이approach02의160창만 세었다.',
 '이 스냅샷에서 Zero통과검사·기존게임/MIPS·브라우저를 반복하지 않았다. 근거파일해시와통합자원결속/링크만 확인했다.']
assert len(j['cells'])==144 and not j['all_art_complete'] and not j['all_gameplay_verified']
assert [c for c in j['cells']if c['character']in('riko','rin')]==old_zero
for k,e in old_evidence.items():assert j['evidence'][k]==e
for c in j['cells']:
    for k in c['evidence']:assert k in j['evidence']
O.mkdir(exist_ok=True)
(O/'coverage.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
esc=html.escape
def link(k):
    e=j['evidence'][k];href=os.path.relpath(ROOT/e['path'],O).replace('\\','/')
    return '<a href="'+esc(href)+'">'+esc(k)+'</a>'
page=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>전체 폼·모션 범위 BR16 RN19 · 갱신05</title>',
 '<style>body{background:#111820;color:#e9edf2;font:15px system-ui;margin:24px}a{color:#9dcfff}table{border-collapse:collapse;width:100%;margin:18px 0 35px}th,td{border:1px solid #405164;padding:10px;text-align:left;vertical-align:top}th{background:#233547}summary{cursor:pointer}small{color:#b7c5d4}.notice{padding:16px;background:#263547}</style>',
 '<h1>네 캐릭터 · 폼별 모션 범위</h1><p>BR16 / RN19 · 12폼 × 12범주. <b>수정 수는 미술 완료율이 아닙니다.</b></p>',
 '<p class="notice">Shibuki Ultimate사다리14는 동결·BR16 통합, 게임 접점은 미검증입니다. Nana Ultimate피격13은 RN19 통합했고 획득후233..236 실제160창·루트12판을 확인했습니다. 나머지폼/9참조 실기를 포함하지 않습니다. 새 사다리·등장·Shibuki피격은 제작 중 후보입니다.</p>',
 '<p><a href="coverage.json">전체 JSON</a> · <a href="../full_scope_matrix04/COVERAGE.html">이전 스냅샷</a> · <a href="../final_endpoint_audit01/ZERO_UI_HQ_SUPPLEMENT.html">Zero UI/HQ 보충판</a> · <a href="../x_endpoint_supplement01/X_UI_HQ_SUPPLEMENT.html">X UI/HQ 보충판</a></p>',
 '<p>최신 통합/대표실기: '+' · '.join(link(k)for k in('br16','rn19','album20','nana_ultimate_hurt19_runtime','nana_hurt19_root_review'))+'</p>',
 '<h2>다음 작업</h2><table><tr><th>담당</th><th>범위</th><th>상태</th></tr>']
for p in j['next_work']:page.append('<tr>'+''.join('<td>'+esc(p[k])+'</td>'for k in('owner','scope','stage'))+'</tr>')
page.append('</table>')
for char,name in {'shibuki':'시부키','nana':'나나','riko':'리코','rin':'린'}.items():
    for form,label in j['forms'].items():
        cells=[c for c in j['cells']if c['character']==char and c['form']==form]
        if not cells:continue
        page.append(f'<h2>{name} · {esc(label)}</h2><table><tr><th>범주</th><th>상태·참조</th><th>판단·남은 범위</th><th>실제 열람·근거</th></tr>')
        for c in cells:
            states='<br>'.join(esc(s['label']+': '+s['refs'])for s in c['states'])or'별도 사본 범위'
            page.append('<tr><td>'+esc(j['categories'][c['category']])+'</td><td>'+states+'</td><td>'+esc(c['note'])+'</td><td><small>'+esc(c['art_review'])+'</small><details><summary>근거</summary>'+'<br>'.join(link(k)for k in c['evidence'])+'</details></td></tr>')
        page.append('</table>')
page.append('<h2>한계</h2><ul>'+''.join('<li>'+esc(x)+'</li>'for x in j['coverage_limits'])+'</ul></html>')
(O/'COVERAGE.html').write_text('\n'.join(page),'utf8')
links=re.findall(r'href="([^"]+)"',(O/'COVERAGE.html').read_text('utf8'))
assert all((O/html.unescape(p)).resolve().is_file()for p in links)
assert sha(P)==j['previous_snapshot']['sha256']
v=dict(passed=True,cells=len(j['cells']),evidence_files=len(j['evidence']),checked_local_links=len(links),broken_links=0,
       previous_snapshot_sha256=sha(P),inherited_evidence_unchanged=len(old_evidence),zero_cells_unchanged=True,
       new_gameplay_or_native_tests_performed=False,browser_test_performed=False,all_art_complete=False,game_or_art_modified=False)
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(dict(json_sha256=sha(O/'coverage.json'),html_sha256=sha(O/'COVERAGE.html'),**v)))
