"""Publish reviewed runtime evidence and the unchanged, blocked art references."""
from pathlib import Path
import hashlib,html,json,shutil,sys
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def artifact(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
out=ROOT/'out/sprite_style_unification_20261107/runtime_checkpoint50';out.mkdir(exist_ok=False)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
runtime=[];viewed=[];body=[]
for name,label in [('br31_shibuki_chaser01','텐코 시부키 · 포스'),('br31_riko_chaser01','유즈하 리코 · 일반'),('rn43_fourth_chaser01','하나코 나나 · 포스'),('rn43_rin_chaser01','아오쿠모 린 · 일반')]:
    p=O/name;e=read(p/'evidence.json');m=read(p/'screen_match.json');assert not e['error'] and e['paused_after'];assert read(ROOT/e['session']/'close.local.json')['exited']
    pages=sorted(p.glob('screen_context_*.png'));assert len(pages)==(len(e['samples'])+3)//4
    for page in pages:
        viewed.append(artifact(page));shutil.copyfile(page,out/f'{name}_{page.name}')
    runtime.append({'character':label,'evidence':artifact(p/'evidence.json'),'framebuffer_comparison':artifact(p/'screen_match.json'),'samples':len(e['samples']),'exact_full_sprite_matches':m['matched_samples'],'reverse_order_matches':m['reverse_order_matched_samples'],'review_pages':[f'{name}_{q.name}'for q in pages]})
    body.append(f'<h2>{label}</h2><p>기록 {len(e["samples"])}표본 / 전체 불투명 픽셀 일치 {m["matched_samples"]}표본. 화면 두 버퍼와 정적 조립을 나란히 표시했습니다.</p>'+''.join(f'<details><summary>비교판 {i+1}</summary><img loading="lazy" src="{name}_{q.name}"></details>'for i,q in enumerate(pages)))
flash=read(O/'rn43_fourth_flash01/fourth_screen_match.json');assert flash['any_full_match'] and flash['opaque_pixels']==798 and flash['extra_armor_pixels']==149
f=O/'rn43_fourth_flash01/capture02_page256.png';viewed.append(artifact(f));shutil.copyfile(f,out/'nana_fourth_flash.png')
blocked=[];boards=[]
for char,tag,label,refs in [('shibuki','br_v31','시부키 Ultimate 등장',[135]),('nana','rn_v43','나나 Ultimate 사다리',[148,149,150,151,152,153,155])]:
    src=read(W/f'staging_{tag}.json')['resources']['PL02_U.ARC'];raw=(ROOT/src['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==src['after'];a=Archive(raw)
    board=Image.new('RGB',(max(2,len(refs)+1)*180,520),'#26313f');d=ImageDraw.Draw(board)
    for row,(form,mask)in enumerate([('획득 전',15),('획득 후',0)]):
        for col,n in enumerate([0]+refs):
            im=a.composite(n,mask)[0].crop((120,104,208,212)).resize((176,216),Image.Resampling.NEAREST);board.paste(im,(col*180,row*260+36),im);d.text((col*180+3,row*260+5),f'{form} '+('대기 기준'if n==0 else f'{n} 기존 보존'),font=font,fill='white')
            blocked.append({'character':char,'form':form,'ref':n,'is_idle_reference':n==0,'rgba_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'source_arc_sha256':src['after']})
    dest=out/f'{char}_preserved_open_items.png';board.save(dest);boards.append(artifact(dest));body.append(f'<h2>{label} · 미완료</h2><p>아래는 현재 BIN에서 추출한 기존 그림입니다. 새 수정안이나 완료 결과가 아닙니다.</p><img src="{dest.name}">')
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>스프라이트 검증 checkpoint50</title><style>body{background:#141b24;color:#e4ebf3;font:17px/1.65 system-ui;margin:24px auto;padding:0 20px;max-width:1280px}a{color:#9ed4ff}img{max-width:100%;image-rendering:pixelated}details{border:1px solid #536175;margin:10px 0;padding:8px}summary{cursor:pointer}h2{margin-top:40px}</style><h1>네 캐릭터 실제 화면 비교 · checkpoint50</h1><p>BR31 / RN43. 이번에는 그림과 BIN을 바꾸지 않고 남아 있던 실기 증거를 보완했습니다. 모든 의상·모든60Hz 프레임의 검증을 뜻하지 않습니다.</p><p><a href="../review_v37/ALL_SPRITES_CURRENT.html">전체 스프라이트 모음집 v37</a> · <a href="../chaser_context49/CHASE_RIDER_REVIEW.html">12폼 체이서 정적 재생판</a></p><p>포스 나나 등장 섬광은 추가 아머149픽셀을 포함한 전체798픽셀이 실제 화면과 일치했습니다.</p><img src="nana_fourth_flash.png">'''+''.join(body)+'''<h2>미완료 사유와 검증 한계</h2><p>시부키135 팔 보정은 이미지 도구 출력 검토의 other 범주, 나나149/151/153 의상 보정은 sexual 범주로 거부되었습니다. 나나의 연결 프레임을 포함한7참조도 보존했습니다. 재시도·우회하지 않았으며 전체 완성으로 세지 않습니다.</p><p>체이서는 포스 시부키·나나와 일반 리코·린의 표본입니다. 블랙·다른 아머 의상 및 모든 부분 아머 실기는 별도입니다. 불일치 표본에는 페이드·전경 가림·RAM/그리기 시점 차이가 있고 원인을 모두 분리한 것은 아닙니다. 나나의 초기 입력은 READY 중이므로 발사·점프 성공으로 계산하지 않습니다.</p></html>'''
(out/'REVIEW.html').write_text(page,'utf8')
report={'checkpoint':50,'builds_unchanged':['BR31','RN43'],'sprite_pixels_changed':False,'new_confirmed_pixel_defects':[],'runtime':runtime,'samples':sum(r['samples']for r in runtime),'full_sprite_matches':sum(r['exact_full_sprite_matches']for r in runtime),'actually_viewed_files':viewed,'flash':{'evidence':artifact(O/'rn43_fourth_flash01/evidence.json'),'screen_match':artifact(O/'rn43_fourth_flash01/fourth_screen_match.json')},'unchanged_art_review':blocked,'unchanged_art_boards':boards,'unchanged_art_boards_actually_viewed':False,'review':artifact(out/'REVIEW.html'),'protection':artifact(W/'protection_checkpoint57.json'),'originals_and_test_cards_unchanged':True,'game_memory_written':False,'F1_F3_sent':False,'all_test_sessions_closed':True,'overall_complete':False}
(O/'checkpoint50_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'samples':report['samples'],'matched':report['full_sprite_matches'],'review':str(out/'REVIEW.html'),'viewed_runtime_pages':len(viewed)}))
