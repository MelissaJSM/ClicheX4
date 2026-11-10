"""Advance evidence coverage to RN18 without repeating frozen asset tests."""
from pathlib import Path
import json,hashlib,copy,html,os,re

ROOT=Path(__file__).resolve().parents[3]
D=Path(__file__).parent
B=D.parent
PREV=D/'full_scope_matrix03/coverage.json'
O=D/'full_scope_matrix04'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
assert sha(PREV)=='ea903784621770753ecc6c54f34126f4988c9d1d64de93069aff709bb84ce01a'
j=read(PREV);old_evidence=copy.deepcopy(j['evidence']);old_zero=[c for c in j['cells']if c['character']in('riko','rin')]
j['previous_snapshot']={'path':PREV.relative_to(ROOT).as_posix(),'sha256':sha(PREV)}
for e in old_evidence.values():assert sha(ROOT/e['path'])==e['sha256'],e['path']
def ev(key,path,purpose,expected=None):
    path=Path(path);h=sha(path)
    if expected:assert h==expected,str(path)
    j['evidence'][key]={'path':path.relative_to(ROOT).as_posix(),'sha256':h,'purpose':purpose}
def st(status,label,refs):return {'status':status,'label':label,'refs':refs}

# Record the three boards actually opened in this turn as a separate static opinion.
N=B/'nana_audit';H=B/'shibuki_audit'
images=[N/'ultimate_hurt_repaint/costume_pair_probe_v4'/f'comparison_{i}.png'for i in(1,2)]
images.append(N/'ultimate_hurt_repaint/aura_contact_probe_v2/comparison.png')
visual={'scope':'Ultimate 피격 공통몸체 비교2판과 오라 비교1판의 실제 view_image 정적 열람',
 'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in images],
 'observations':['106/110의 맨팔 손목·팔꿈치 연결에서 새 확정 단절을 찾지 못했다. 밝은 재킷 소매 잔재의 확정 부위를 이 판에서 찾지 못했다.',
 '233 접힌 다리·234 긴 다리는 무릎과 발목이 이어진다. 대기보다 과하게 가늘어진 확정 결함을 이 판에서 찾지 못했다.',
 '236 귀 위의 작은 흰 오라는 귀에 붙은 연장선이 아니라 별도 조각으로 읽힌다. 새 머리·발 실루엣을 가리지 않는 정적 배치로 보인다.'],
 'limits':['시간순 깜박임·실기·ARC 패킹 검사가 아니다.','원화 출처·색인·조각 픽셀 동일성은 별도 제작/독립 검사 대상이다.'],
 'new_confirmed_art_defects':[],'runtime_verified':False,'user_final_accepted':False}
vp=D/'nana_ultimate_hurt_static_review01.json'
vp.write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf8')

ev('rn18',B/'staging_rn_v18.json','RN18 통합 자원 계획. 별도 실행 증거는 runtime 문서.')
ev('rn18_disc',ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v18/manifest.json','RN18 전체 디스크/EDC·ECC/재추출 검사 기록. 이 집계에서 재실행하지 않음.','5ba0f7f365058af28f84e38535ca91412949eb8ef2ce5ec4e8f121022774ed24')
ev('rn18_native',B/'staging_rn_v18_native_checks.json','RN18 통합 자원의 원MIPS/GPU 검사 기록.','8bdb2ba56cc30ad68f8c003906de060f9b7c73e4c24e61584341594b436e9da3')
ev('nana_hurt18_runtime',B/'runtime/nana_hurt18_summary.json','기본106..114·포스233..236 실제480창/24판, 비동기 미확정0.','a661a9660588aebc766ee733eff1898be4302cf21d04721e1d940d66e0913f5a')
ev('nana_hurt18_views',B/'root_review_checkpoint92.json','루트의 실제24판 열람. 이 집계에서 같은 화면을 재열람한 것은 아님.','b56ab218678ed95da3906b92eee1562769505585ee1c872ba7ef2b236b004186')
ev('nana_hurt_frozen',N/'hurt_repaint/packed_hurt_candidate_v1/FROZEN.json','기본/포스13: 새몸체4와 효과파생9 동결.')
ev('nana_hurt_reader',D/'nana_hurt13_independent01/report.json','제작 함수와 분리한65층·비대상·효과 오라 독립 읽기.','290e224ec21e4d7dcb8716d7eeaad33a7c36d0bf5e3fc470dbdf329194625bb8')
ev('nana_ledger11',N/'scope_summary_v11/manifest.json','최신 제작 장부의 새몸체/효과파생 구분. RN18 실기는 이 스냅샷에서 별도로 연결.')
ev('nana_ultimate_hurt_relations',D/'nana_ultimate_hurt_relations01/report.json','PL02 피격은 PL00과 다른109/CLUT2/오라 출처를 가진다는 읽기 조사.','6a848905f6170e4872cda020ae345a8e5b971718fdfe911906a069d5e7c33059')
ev('nana_ultimate_hurt_art',vp,'새4몸체 전후와 오라의 정적3판 의견. 후보·실기 미검증.')
ev('nana_ultimate_hurt_registration',N/'ultimate_hurt_repaint/costume_pair_probe_v4/manifest.json','새4몸체 전후 의미영역 등록 중간안.')
ev('nana_ultimate_hurt_aura',N/'ultimate_hurt_repaint/aura_contact_probe_v2/registration.json','기존 재킷 오라66/135px의 새몸체 국소 정합 후보.')
ev('shibuki_ledger17',H/'fullform_ledger17.json','Shibuki 최신 제작 장부. 사다리 새준비본은 다음 별도 근거로 추가.')
ev('shibuki_ultimate_ladder_candidate',H/'prepared_ultimate_ladder01/proposal.json','Ultimate14 준비 ARC03a67562, 통합·실기와 분리.','30d7263fc10df85783ebd76089c7c0010a1cf042ef29192ef228811ac0f994ef')
ev('shibuki_ultimate_ladder_reader',D/'shibuki_ultimate_ladder_independent01/report.json','14목표/498비대상raw·448RGBA·209GPU 경계 독립 읽기.','20c6324cbc06f04249614568d3a55618786ac4da57514c7181349a8ccdedf9a5')
ev('shibuki_ultimate_ladder_art',D/'shibuki_ultimate_ladder_independent01/visual_review.json','실제 최종6판의 독립 정적 미술 열람.','97a7b30acc65e8dc7d9ead6f67e1915277a7d23e27efbb483397a06baac87846')
ev('shibuki_ultimate_ladder_root',B/'root_review_checkpoint94.json','루트의 실제 최종6판 열람.','9e5e239fe287b607e84d98e2285200c3370bd1bd1a001523e1ca8dd508f887ee')
ev('shibuki_ladder_route',D/'shibuki_ladder_route01/report.json','기존DATA3 메뉴 로드 근거. 가까운 사다리 동선 미확인.','6ffcc7b6a20696bc6568e67e46950adf9d271fef4f762a24231f6b3dfb666650')
r=read(B/'runtime/nana_hurt18_summary.json')
assert [x['actual_captures']for x in r['runs']]==[160,160,160]
assert [len(x['root_actually_viewed'])for x in r['runs']]==[5,7,12]
assert all(not x['unverified_events'] for x in r['runs'])
assert sorted(set().union(*(set(x['new_references_verified'])for x in r['runs'][:2])))==list(range(106,115))
assert r['runs'][2]['new_references_verified']==list(range(233,237))
assert r['f1_f3_used'] is r['process_memory_written'] is r['active_build_pointers_changed'] is False
for key in ('protection','album','browser_checks'):
    ev('rn18_'+key,ROOT/r[key]['path'],'RN18 기존 '+key+' 근거 연결, 재검사 아님.',r[key]['sha256'])
plan=read(B/'staging_rn_v18.json');disc=read(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v18/manifest.json')
assert disc['modified_bin']['sha256']==r['disc_sha256']
for name,v in plan['resources'].items():assert v['after']==disc['resources'][name]['after']
j['prior_integration']=copy.deepcopy(j['integration'])
j['integration'].pop('rn17')
j['integration']['rn18']={k:plan[k]for k in('output','resources')}
j['integration']['rn18']['bin_sha256']=r['disc_sha256']

for c in j['cells']:
    ch,form,cat=c['character'],c['form'],c['category']
    if ch=='nana':
        c['evidence']+=['nana_ledger11','rn18']
        if cat=='hurt' and form in ('base','fourth'):
            c['states']=[st('integrated_new_art','새 몸체 동결·RN18 통합','106, 110, 233, 234'),
                         st('integrated_derived_effect','새 몸체 기반 효과 파생·RN18 통합','107..109, 111..114, 235..236'),
                         st('needs_redraw','재작화 대상·미착수','120..125')]
            runs=r['runs'][:2]if form=='base'else r['runs'][2:]
            verified=sorted(set().union(*(set(x['new_references_verified'])for x in runs)))
            c['note']=('기본/포스13은 새몸체4·효과파생9로 구분한다. 233..236은 저체력이 아니라 몸통아머 피격표35다. '
                       f"이번 {form} 실제 관측은 {verified}이며 다른폼/다른피해유형까지 전수 실기를 뜻하지 않는다. 저체력120..125 재작화는 남아 있다.")
            c['art_review']='기존 최종 원화·원순서 열람과 독립 reader를 유지. 루트가 RN18 실제 기본12판·포스12판을 열람하여 추가 확정 몸체/효과 단절을 찾지 못했다. 이 집계에서 같은 화면을 다시 보지 않았다.'
            c['runtime_coverage']={'evidence':'nana_hurt18_runtime','runs':[x['name']for x in runs],
                'actual_captures':sum(x['actual_captures']for x in runs),'root_viewed_boards':sum(len(x['root_actually_viewed'])for x in runs),
                'new_references_with_successful_ram_gpu_sample':verified,'unverified_events':[],
                'all_60hz_transitions_verified':False,'all_partial_armor_combinations_verified':False}
            c['evidence']+=['nana_hurt_frozen','nana_hurt_reader','nana_hurt18_runtime','nana_hurt18_views','rn18_native','rn18_protection']
        elif cat=='hurt':
            c['states']=[st('registered_candidate','새4몸체 전후 등록·공통부위 검토','106, 110, 233, 234'),
                         st('derived_candidate','효과·실루엣·오라 파생 후보, 미통합','107..109, 111..114, 235..236'),
                         st('preserve_reviewed','기존 세부 보존 판단','120..125')]
            c['note']='Ultimate 새4몸체 전후의 의미영역과 오라 후보를 작업 중이다.109 양폼 실루엣·112..114 재킷공통CLUT2·235/236 고유오라66/135px를 PL00과 구분한다. 현재 RN18 Ultimate 자원은 기존4132738a이며 새피격은 아직 미통합이다.'
            c['art_review']='새 공통몸체v4 2판과 오라v2 1판을 독립 담당자가 실제 열람. 새 확정 단절은 찾지 못했으나 최종 ARC/원순서/실기와 사용자 수용은 별도다.'
            c['evidence']+=['nana_ultimate_hurt_relations','nana_ultimate_hurt_art','nana_ultimate_hurt_registration','nana_ultimate_hurt_aura']
    elif ch=='shibuki':
        c['evidence']+=['shibuki_ledger17']
        if cat=='ladder' and form in('ultimate_before','ultimate_after'):
            c['states']=[st('prepared_candidate','새14참조 패킹·독립/미술 검토, 통합 전','143..155, 183')]
            c['note']='새14참조03a67562의70층·448RGBA·209GPU 경계와 비대상을 독립 확인했다. 원US 반전4쌍 의미를 유지하나147/148옛overlay 발+1px 예외까지 동일복원하지 않는다.155는149새몸+반동팔 정책이다. 일부 발끝1~2px 차이·사다리 실제 접점은 미검증. BR15 통합 자원에는 아직 없다.'
            c['art_review']='루트94 최종6판과 독립 담당자의 같은6판 실제 열람. 상세·손목·하체에 추가 확정 단절을 찾지 못했다. 원MIPS 통합과 게임 실기 증거는 아직 이 표에 없음.'
            c['evidence']+=['shibuki_ultimate_ladder_candidate','shibuki_ultimate_ladder_reader','shibuki_ultimate_ladder_art','shibuki_ultimate_ladder_root','shibuki_ladder_route']
        elif cat=='ladder':
            c['note']='기본/포스14는 기존 새 원화 통합. 별도 Ultimate14도 새준비본까지 진행했으나 그 실기나 통합 성공을 이 폼에서 추정하지 않는다.'
    c['evidence']=list(dict.fromkeys(c['evidence']))

j['next_work'][0].update(stage='새14 준비본·독립 읽기/최종6판 검토 완료, 원MIPS·최종동결/통합·대표실기 후속',evidence=['shibuki_ultimate_ladder_candidate','shibuki_ultimate_ladder_reader','shibuki_ultimate_ladder_root'])
j['next_work'][1].update(scope='Ultimate 피격106..114/233..236, 기본/포스 저체력120..125',stage='Ultimate 새4몸체 전후·효과/오라 등록 후보. 기본/포스 피격13은RN18대표실기 완료; 저체력은 별도 미제작',evidence=['nana_ultimate_hurt_art','nana_ultimate_hurt_relations','nana_hurt18_runtime','nana_ledger11'])
for p in j['next_work']:
    if p['character']=='shibuki' and 'shibuki_ledger'in p['evidence']:p['evidence'].append('shibuki_ledger17')
    if p['character']=='nana' and 'nana_ledger'in p['evidence']:p['evidence'].append('nana_ledger11')
j['completed_milestones_since_previous']=[{'scope':'RN18 기본/포스 피격13 대표 실기','actual_captures':480,'root_viewed_boards':24,
 'forms_and_refs':{'base':list(range(106,115)),'fourth':list(range(233,237))},'unverified_events':0,
 'evidence':['nana_hurt18_runtime','nana_hurt18_views','rn18_native','rn18_protection'],'limits':r['limits'],'all_gameplay_verified':False}]
j['snapshot_summary']='BR15/RN18 통합 기준. Nana 기본/포스 피격13의 실제 관측 범위를 연결하고 Shibuki Ultimate사다리14 준비본/Nana Ultimate피격 후보를 분리 갱신. 전체 작업은 계속 진행 중.'
j['coverage_limits']+=['RN18 기본106..114와 포스233..236의 성공 표본을 두폼13개씩 전수실기로 확대하지 않는다. 강한 날림의 정확한 폭발 피해원 객체ID는 미확인이다.',
 '새 사다리 준비본03a67562와 Ultimate피격 등록후보는 현재 BR15/RN18 BIN 또는 대표실기 완료 수에 합산하지 않는다.']
assert len(j['cells'])==144 and not j['all_art_complete'] and not j['all_gameplay_verified']
assert [c for c in j['cells']if c['character']in('riko','rin')]==old_zero
for key,e in old_evidence.items():assert j['evidence'][key]==e
for c in j['cells']:
    for k in c['evidence']:assert k in j['evidence']
O.mkdir(exist_ok=True)
(O/'coverage.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
esc=html.escape
def link(k):
    e=j['evidence'][k];href=os.path.relpath(ROOT/e['path'],O).replace('\\','/')
    return '<a href="'+esc(href)+'">'+esc(k)+'</a>'
page=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>전체 폼·모션 범위 BR15 RN18 · 갱신04</title>',
 '<style>body{background:#111820;color:#e9edf2;font:15px system-ui;margin:24px}a{color:#9dcfff}table{border-collapse:collapse;width:100%;margin:18px 0 35px}th,td{border:1px solid #405164;padding:10px;text-align:left;vertical-align:top}th{background:#233547}summary{cursor:pointer}small{color:#b7c5d4}.notice{padding:16px;background:#263547}</style>',
 '<h1>네 캐릭터 · 폼별 모션 범위</h1><p>BR15 / RN18 · 12폼 × 12범주. <b>수정 수는 미술 완료율이 아닙니다.</b></p>',
 '<p class="notice">RN18 기본106..114·포스233..236 피격은 실제480창·루트24판 검토와 업로드 성공 표본을 확보했습니다. 미확정 사건0이며, 모든방향/부분아머/피해원의 전수 실기는 아닙니다. Shibuki Ultimate사다리14는 준비본 검토 단계, Nana Ultimate피격은 등록 후보입니다.</p>',
 '<p><a href="coverage.json">전체 JSON</a> · <a href="../full_scope_matrix03/COVERAGE.html">이전 스냅샷</a> · <a href="../final_endpoint_audit01/ZERO_UI_HQ_SUPPLEMENT.html">Zero UI/HQ 보충판</a> · <a href="../x_endpoint_supplement01/X_UI_HQ_SUPPLEMENT.html">X UI/HQ 보충판</a></p>',
 '<p>최신 대표 실기: '+' · '.join(link(k)for k in('nana_hurt18_runtime','nana_hurt18_views','rn18_native','rn18_protection'))+'</p>',
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
assert sha(PREV)==j['previous_snapshot']['sha256']
v={'passed':True,'cells':len(j['cells']),'evidence_files':len(j['evidence']),'checked_local_links':len(links),'broken_links':0,
 'prior_snapshot_preserved_sha256':sha(PREV),'inherited_evidence_unchanged':len(old_evidence),'zero_cells_unchanged':True,
 'new_gameplay_or_native_tests_performed':False,'browser_test_performed':False,'all_art_complete':False,'game_or_art_modified':False}
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'json_sha256':sha(O/'coverage.json'),'html_sha256':sha(O/'COVERAGE.html'),**v}))
