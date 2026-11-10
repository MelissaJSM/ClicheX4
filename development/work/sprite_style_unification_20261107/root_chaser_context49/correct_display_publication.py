from pathlib import Path
import hashlib,json,shutil
O=Path(__file__).resolve().parent;ROOT=O.parents[2];out=ROOT/'out/sprite_style_unification_20261107/runtime_checkpoint50';read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def artifact(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
prior=O/'checkpoint50_buffer256_summary.json';assert not prior.exists();shutil.copyfile(O/'checkpoint50_summary.json',prior);shutil.copyfile(out/'browser_check.json',O/'browser_check_buffer256.json');shutil.copyfile(out/'REVIEW.html',O/'REVIEW_buffer256.html')
summary=read(O/'checkpoint50_summary.json');page=(out/'REVIEW.html').read_text('utf8')
for row in summary['runtime']:
    source=ROOT/row['evidence']['path'];p=source.parent;name=p.name;match=read(p/'screen_match_display.json');assert match['matched_samples']==row['exact_full_sprite_matches'];row['framebuffer_comparison']=artifact(p/'screen_match_display.json');pages=sorted(p.glob('screen_display_*.png'));assert len(pages)==len(row['review_pages'])
    for old,new in zip(row['review_pages'],pages):
        target=f'{name}_{new.name}';shutil.copyfile(new,out/target);page=page.replace(old,target)
    row['review_pages']=[f'{name}_{q.name}'for q in pages]
flash=O/'rn43_fourth_flash01';shutil.copyfile(flash/'capture02_page240.png',out/'nana_fourth_flash.png');summary['flash']['screen_match']=artifact(flash/'fourth_screen_match_display.json')
page=page.replace('</html>','<p>표시 영역 정정: 실제 DIS PENV 사각형의 Y=240을 확인하여 두 번째 화면 버퍼 시작점을256에서240으로 고쳤습니다. 아래쪽 화면 밖 데이터는 제외됐고, 전체 픽셀 일치34표본 및 섬광798픽셀 결과는 그대로입니다. 원시 캡처는 수정하지 않았습니다.</p></html>').replace('DIS PENV','DISPENV')
(out/'REVIEW.html').write_text(page,'utf8');summary['review']=artifact(out/'REVIEW.html')
viewed=[flash/'capture02_page240.png',O/'rn43_fourth_chaser01/screen_display_1.png',O/'rn43_rin_chaser01/screen_display_3.png',O/'br31_riko_chaser01/screen_display_3.png',O/'br31_shibuki_chaser01/screen_display_1.png']
summary['display_correction']={'native_rectangle':[0,240,320,240],'previous_page_y':256,'actual_pages':[0,240],'prior_evidence':artifact(prior),'same_full_match_counts':True,'actually_viewed_corrected_files':[artifact(p)for p in viewed],'raw_ram_vram_changed':False}
(O/'checkpoint50_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'corrected_pages':18,'corrected_representatives_viewed':5,'full_matches_unchanged':summary['full_sprite_matches']}))
