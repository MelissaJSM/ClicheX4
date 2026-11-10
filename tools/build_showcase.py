"""Build deterministic HTML presentation boards from the exact released art.
No generative redraw of pixels. Browser exports produce README PNGs.
"""
from pathlib import Path
from html import escape
import json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/showcase';OUT.mkdir(exist_ok=True)
RIGHTS='스텔라이브 관련 콘텐츠의 권리는 스텔라이브 및 각 권리자에게 있으며 요청 시 삭제될 수 있습니다. 원작 게임의 저작권·소유권은 CAPCOM에 있습니다.'
CHARS=[('shibuki','텐코 시부키','TENKO SHIBUKI','X','시부키 / 리코','#bf9bff','소매와 연결된 버스터 · 오드아이 · 기본 / 포스 / 얼티밋'),('riko','유즈하 리코','YUZUHA RIKO','ZERO','시부키 / 리코','#83e4cc','흰 의상과 청록색 망토 · 검 연결부와 원작 검기 · 블랙 변형'),('nana','하나코 나나','HANAKO NANA','X','나나 / 린','#ff8fba','전용 권총 사랑이 · 원작 차지샷 유지 · 기본 / 포스 / 얼티밋'),('rin','아오쿠모 린','AOKUMO RIN','ZERO','나나 / 린','#83b8ff','메이드 의상과 한쪽 묶음 · 대걸레 자루와 원작 검기 · 아카쿠모 린')]
STYLE='''*{box-sizing:border-box}html,body{margin:0;width:1600px;height:1000px;overflow:hidden}body{font-family:"Malgun Gothic",sans-serif;color:#f1f4ff;background:radial-gradient(ellipse at 75% 20%,#182458,transparent 55%),linear-gradient(120deg,#080f22,#102238)}body:before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 49px,#8dbbf008 50px),repeating-linear-gradient(90deg,transparent,transparent 49px,#8dbbf008 50px);pointer-events:none}.line{position:absolute;left:48px;right:48px;height:2px;background:linear-gradient(90deg,#697cfb,#68dfe7,transparent)}.label{letter-spacing:4px;font-size:16px;font-weight:700;color:#a9bedb}.panel{background:#101e33d9;border:1px solid #42587b;border-radius:16px;box-shadow:0 12px 60px #0003}.pixel{image-rendering:pixelated}footer{position:absolute;left:55px;right:55px;bottom:23px;color:#b7c8e2;font-size:14px;line-height:1.6;border-top:1px solid #4a5c7b;padding-top:13px}h1,h2,p{margin:0}.tag{display:inline-block;border:1px solid #586c99;border-radius:30px;padding:8px 20px;background:#10213c;color:#d9e5ff;font-size:20px}'''
def page(title,body):return '<!doctype html><html lang="ko"><meta charset="utf-8"><title>'+escape(title)+'</title><style>'+STYLE+'</style><body>'+body+'<footer>'+RIGHTS+'<br>CLICHÉX4 · 비공식 팬 모드 · 최종 적용 자원 기반 소개 이미지 / 게임 플레이 캡처 아님</footer></body></html>'
hero='''<div class="line" style="top:32px"></div><p class="label" style="position:absolute;left:60px;top:53px">CLICHÉX4 · CHARACTER REPLACEMENT PROJECT</p><div style="position:absolute;right:60px;top:50px"><span class="tag">PS1</span> <span class="tag">STEAM LEGACY COLLECTION</span></div><p style="position:absolute;top:112px;left:0;width:1600px;text-align:center;color:#ffcf69;font-size:26px;font-weight:800;letter-spacing:6px">스텔라이브 팬 모드</p><img src="../branding/logo.png" style="position:absolute;left:380px;top:137px;width:840px;height:280px;object-fit:contain"><img src="../branding/ensemble.png" style="position:absolute;left:52px;top:359px;width:1496px;height:auto"><div style="position:absolute;left:80px;right:80px;top:864px;display:flex;justify-content:space-between;font-size:22px;font-weight:700"><span>하나코 나나 · 아오쿠모 린</span><span style="color:#8ea9cb;font-size:18px">스프라이트 · 일러스트 · UI · 한글화</span><span>텐코 시부키 · 유즈하 리코</span></div>'''
(OUT/'hero.html').write_text(page('ClichéX4',hero),'utf8')
for key,ko,en,original,mode,color,description in CHARS:
    zero=original=='ZERO';folder=ROOT/'assets/characters'/key
    files=[('대기','normal/bank0_147.png'),('이동','normal/bank0_009.png'),('점프','normal/bank0_023.png'),('대시','normal/bank0_045.png'),('승리','normal/bank1_003.png')]if zero else[('대기','base/000.png'),('이동','base/011.png'),('점프','base/035.png'),('대시','base/069.png'),('승리','base/156.png')]
    boxes=[Image.open(folder/'sprites'/p).getbbox()for label,p in files];boxes=[b for b in boxes if b]
    lo=min(b[0]for b in boxes)-4;top=min(b[1]for b in boxes)-4;hi=max(b[2]for b in boxes)+4;bottom=max(b[3]for b in boxes)+4
    frame_w,frame_h=hi-lo,bottom-top
    thumbnails=''
    for label,p in files:
        image=f'../characters/{key}/sprites/{p}'
        thumbnails+=f'<div style="width:152px;text-align:center"><svg width="152" height="220" viewBox="{lo} {top} {frame_w} {frame_h}" style="image-rendering:pixelated"><image href="{image}" width="384" height="384"/></svg><p style="color:#b6cae4;font-size:18px">{label}</p></div>'
    dlg='normal'if zero else'00';hq='normal'if zero else'00'
    body=f'''<div class="line" style="top:32px"></div><p class="label" style="position:absolute;left:60px;top:54px">CLICHÉX4 · {en}</p><h1 style="position:absolute;left:60px;top:88px;font-size:60px">{ko}</h1><span class="tag" style="position:absolute;right:60px;top:105px;border-color:{color};color:{color}">{original} → {ko}</span><p style="position:absolute;left:64px;top:175px;font-size:22px;color:#b7c9e3">{mode} 모드 · {description}</p>
<section class="panel" style="position:absolute;left:60px;top:235px;width:490px;height:650px"><p class="label" style="position:absolute;left:27px;top:25px;color:{color}">CHARACTER ILLUSTRATION</p><img class="pixel" src="../characters/{key}/illustrations/selection/shared/00.png" style="position:absolute;left:25px;top:75px;width:440px;height:450px;object-fit:contain"><h2 style="position:absolute;left:27px;bottom:68px;font-size:27px">캐릭터 선택 일러스트</h2><p style="position:absolute;left:27px;bottom:30px;font-size:18px;color:#afc2de">최신 패치의 그림·배색·창 테두리</p></section>
<section class="panel" style="position:absolute;left:575px;top:235px;width:965px;height:340px"><p class="label" style="position:absolute;left:28px;top:22px;color:{color}">IN-GAME SPRITES</p><div style="position:absolute;left:35px;right:35px;top:57px;display:flex;justify-content:space-between">{thumbnails}</div></section>
<section class="panel" style="position:absolute;left:575px;top:597px;width:965px;height:288px"><div style="position:absolute;left:28px;top:22px"><p class="label" style="color:{color}">DIALOGUE & HUNTER BASE</p><h2 style="margin-top:28px;font-size:26px">대화와 헌터베이스</h2><p style="margin-top:18px;font-size:18px;line-height:1.8;color:#afc2de">플레이어 외형부터 UI 속 모습까지.<br>표정과 장비 상태에 맞춘 교체 그림.</p></div><img class="pixel" src="../characters/{key}/illustrations/dialogue/{dlg}/00.png" style="position:absolute;left:385px;top:54px;width:220px;height:190px;object-fit:contain"><svg style="position:absolute;left:650px;top:30px;image-rendering:pixelated" width="275" height="235" viewBox="40 0 80 160"><image href="../characters/{key}/illustrations/hunter_base/{hq}/00.png" width="160" height="160"/></svg></section>'''
    (OUT/(key+'.html')).write_text(page(ko,body),'utf8')

# Asset gallery uses relative files and renders frame origins consistently.
cards=[]
for key,ko,*_ in CHARS:
    m=json.loads((ROOT/'assets/characters'/key/'sprites/manifest.json').read_text('utf8'))
    groups={}
    for row in m['frames']:groups.setdefault(row['form'],[]).append(row)
    sections=[]
    for form,rows in groups.items():
        bounds=[Image.open(ROOT/'assets/characters'/key/'sprites'/r['file']).getbbox()for r in rows];bounds=[b for b in bounds if b]
        x=min(b[0]for b in bounds)-5;y=min(b[1]for b in bounds)-5;w=max(b[2]for b in bounds)-x+5;h=max(b[3]for b in bounds)-y+5
        ims=''.join(f'<figure><a href="characters/{key}/sprites/{r["file"]}"><svg width="260" height="240" viewBox="{x} {y} {w} {h}" style="image-rendering:pixelated"><image href="characters/{key}/sprites/{r["file"]}" width="384" height="384"/></svg></a><figcaption>{escape(r["file"])} · {escape(r["group"])}</figcaption></figure>'for r in rows)
        sections.append(f'<details><summary>{form} · {len(rows)}장</summary><div class="grid">{ims}</div></details>')
    art=[]
    for p in sorted((ROOT/'assets/characters'/key/'illustrations').rglob('*.png')):
        rel=p.relative_to(ROOT/'assets').as_posix();art.append(f'<figure><img class="art" loading="lazy" src="{rel}"><figcaption>{escape(p.relative_to(ROOT/"assets/characters"/key/"illustrations").as_posix())}</figcaption></figure>')
    sections.append('<details><summary>일러스트</summary><div class="grid">'+''.join(art)+'</div></details>')
    ui=[]
    for p in sorted((ROOT/'assets/characters'/key/'ui').rglob('*.png')):
        rel=p.relative_to(ROOT/'assets').as_posix();ui.append(f'<figure><img class="art" loading="lazy" src="{rel}"><figcaption>{escape(p.relative_to(ROOT/"assets/characters"/key/"ui").as_posix())}</figcaption></figure>')
    sections.append('<details><summary>HUD · 선택/저장 스프라이트</summary><div class="grid">'+''.join(ui)+'</div></details>')
    cards.append(f'<section id="{key}"><h2>{ko}</h2>'+''.join(sections)+'</section>')
(ROOT/'assets/index.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>ClichéX4 최신 자산</title><style>body{background:#101b2a;color:#e9f1ff;font:16px "Malgun Gothic",sans-serif;margin:40px}a{color:#a9d1ff}summary{padding:20px;cursor:pointer;background:#1e2e46;margin:8px 0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}figure{margin:0;background:#23364d;padding:10px}img{display:block;width:260px;height:240px;object-fit:cover;object-position:41% 41%;image-rendering:pixelated}.art{object-fit:contain;object-position:center}figcaption{font-size:12px;overflow-wrap:anywhere}</style><h1>ClichéX4 · 최신 적용 자산 모음</h1><p>최종 BIN에서 다시 복원한 정적 자료입니다. 실제 플레이 캡처가 아닙니다. PNG의 원점은 고정되어 있습니다.</p><nav>'+ ' · '.join(f'<a href="#{key}">{ko}</a>'for key,ko,*_ in CHARS)+'</nav>'+''.join(cards)+'<p>'+RIGHTS+'</p></html>','utf8')
print('Prepared five HTML boards and asset gallery')
