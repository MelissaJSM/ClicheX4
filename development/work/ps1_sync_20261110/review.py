"""Build an after-only review gallery from the verified PS1 reconstructions."""
import html
import json
from PIL import Image,ImageDraw,ImageFont
from sync import ROOT,D,save

build=json.loads((D/'build.json').read_text('utf8'))
out=(ROOT/build['cue']).parent
folder=out/'review'
files=sorted(folder.glob('*.png'))
names=['select_00.png','dialogue_00.png','dialogue_01.png','dialogue_03.png',
       'dialogue_08.png','dialogue_09.png','pause_0_00.png','pause_3_00.png',
       'pause_4_00.png','pause_5_00.png','hq_00_00.png','hq_01_00.png',
       'hq_15_00.png','hq_16_00.png','hq_17_00.png','hq_15_02.png']
board=Image.new('RGB',(1200,920),'#1c2636')
draw=ImageDraw.Draw(board)
for i,name in enumerate(names):
    im=Image.open(folder/name).convert('RGBA')
    scale=min(3,276//im.width,192//im.height)
    scale=max(1,scale)
    im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
    x=i%4*300;y=i//4*230
    draw.text((x+8,y+6),name,fill='white')
    board.paste(im,(x+(300-im.width)//2,y+28),im)
board.save(folder/'overview.png')
sections=[]
for prefix,label in [('select_','캐릭터 선택'),('dialogue_','대화·스테이지별 사본'),('pause_','일시정지 의상'),('hq_','헌터베이스 18상태')]:
    cells=[]
    for p in files:
        if p.name.startswith(prefix):
            cells.append(f'<figure><a href="{p.name}"><img src="{p.name}" loading="lazy"></a><figcaption>{html.escape(p.stem)}</figcaption></figure>')
    sections.append(f'<details open><summary>{label}</summary><div class="grid">'+''.join(cells)+'</div></details>')
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>PS1 최신화 그림 확인</title>
<style>body{background:#172131;color:#eef3fa;font:16px system-ui;max-width:1440px;margin:32px auto;padding:0 20px}a{color:#a9d5ff}p{line-height:1.7}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}figure{margin:0;padding:16px;background:#26354a;min-height:240px}img{image-rendering:pixelated;max-width:100%;width:280px;object-fit:contain;height:230px}figcaption{font-size:13px;overflow-wrap:anywhere}summary{font-size:22px;padding:24px 0}</style>
<h1>시부키·리코 PS1 최신화</h1><p>수정 BIN 자원으로 준비한 조립 그림입니다. 실기 캡처와 구별하며, Steam 수용본과 픽셀·좌표 일치를 검사했습니다. 시부키는 본인 오른눈 청회색 / 왼눈 금색입니다. 선택 화면의 리코 등 비대상 그림도 보존 확인용으로 포함됩니다.</p>
<p>나나·린은 비교 결과 새로 이식할 스프라이트 수정이 없어 기존 최신 BIN을 유지합니다. 두 모드의 선택·대화·일시정지·헌터베이스 전체 기존 모음집은 <a href="../../../illustration_review_20261109/일러스트_모음집.html">이전 모음집</a>을 참고하세요. 그 모음집의 시부키 눈은 수정 전입니다.</p>'''+''.join(sections)+'</html>'
(folder/'index.html').write_text(page,'utf8')
print('Saved review',folder/'index.html')
