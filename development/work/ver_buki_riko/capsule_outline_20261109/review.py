"""Review actual decoded assets using the recorded native animation steps; not gameplay capture."""
import sys,json,base64,io
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
def main():
 build=json.loads((D/'build.json').read_text('utf8'));OUT=(ROOT/build['cue']).parent/'review'
 timeline=json.loads((D/'native_timeline.json').read_text('utf8'));font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
 pal=np.array([(0,0,0,0),(255,255,255,255),(100,220,255,255),(150,175,255,255)]+[(255,110,90,255)]*12,np.uint8)
 cases=[next(c for c in timeline['cases']if c['ultimate']==1 and c['part']==0 and c['facing']==0)]
 for part,bit in [(0,1),(1,2),(3,4),(4,8)]:cases.append(next(c for c in timeline['cases']if c['ultimate']==0 and c['part']==part and c['initial_armor']==15^bit and c['facing']==0))
 snippets=[]
 for k,case in enumerate(cases):
  name='PL02_U.ARC'if case['ultimate']else'PL00_U.ARC';gb=10+[0,1,2,2,3][case['part']]
  old,new=[Archive((D/folder/name).read_bytes())for folder in ['before','prepared']]
  frames=[];durations=[];label='얼티밋 획득 전후'if not k else '포스 '+['머리','몸','팔','다리'][k-1]+' · 다른 세 파츠 보유'
  for row in case['sequence']:
   board=Image.new('RGB',(624,330),'#1c293a');draw=ImageDraw.Draw(board)
   for side,arc in enumerate([old,new]):
    body=arc.composite(row['body_ref'],row['body_mask'])[0];pixels=arc.layer(row['effect_ref'],gb+8,gb)[0]%16
    im=Image.alpha_composite(body,Image.fromarray(pal[pixels])).crop((112,112,208,208)).resize((288,288),Image.Resampling.NEAREST)
    board.paste(im,(side*312,35),im);draw.text((side*312+8,6),('수정 전'if side==0 else'수정 후')+f" · 효과 {row['effect_ref']}",font=font,fill='white')
   frames.append(board);durations.append(max(10,round(row['calls']*1000/60/10)*10))
  path=OUT/f'sequence_{k}.gif';frames[0].save(path,save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False)
  uri='data:image/gif;base64,'+base64.b64encode(path.read_bytes()).decode();snippets.append('<details'+(' open'if not k else'')+'><summary>'+label+'</summary><img src="'+uri+'"></details>')
 def png(name):return '<img src="data:image/png;base64,'+base64.b64encode((OUT/name).read_bytes()).decode()+'">'
 text='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>시부키 캡슐 섬광 비교</title><style>body{background:#131d2a;color:#edf1ff;font:16px/1.6 "Malgun Gothic",sans-serif;max-width:1200px;margin:25px auto;padding:16px}img{max-width:100%;image-rendering:pixelated}summary{cursor:pointer;padding:12px;background:#26394f;margin-top:20px}code{overflow-wrap:anywhere}p{color:#c3d2e7}</style><h1>시부키 캡슐 섬광 비교</h1><p>최종 게임 자원 복원 · 실제 플레이 캡처가 아닙니다. 효과는 흰색/청색 인덱스 구분용 색상이며 실기 반투명 합성은 별도입니다. GIF는 원작 호출 수를 60회/초로 환산했습니다.</p><h2>얼티밋: 수영복 가장자리에 붙는 선</h2><p>현재 파일에서 옛 X 외형이나 후반 텍스처 불일치는 재현되지 않았습니다. 기존 바깥 1픽셀 띠를 현재 수영복의 실제 경계 안쪽으로 옮겼습니다. 4캡슐의 후반9/10참조만 바꿨습니다.</p>'''+png('comparison.png')+'''<h2>포스: 이전 파츠를 무시하던 전신 윤곽 수정</h2><p>기존에는 기본형＋이번 파츠만 기준으로 선을 그렸습니다. 마지막 선은 해당 파츠를 얻은 8가지 의상 모두에서 정확한 실제 외곽 픽셀만 사용합니다. 다른 파츠에 따라 경계가 달라지는 곳에는 잘못된 선을 그리지 않습니다. 새로 얻는 파츠의 원래 스캔·섬광은 보존했습니다.</p>'''+png('force_comparison.png')+''.join(snippets)+'<p>새 CUE: <code>'+build['cue']+'</code><br>BIN SHA-256: <code>'+build['sha256']+'</code></p></html>'
 (OUT/'index.html').write_text(text,'utf8');print(OUT/'index.html')
if __name__=='__main__':main()
