"""Local comparison from verified native GPU output, explicitly a simulation."""
import json,struct,shutil
from pathlib import Path
from PIL import Image,ImageDraw
from runtime import H,ROOT,entry,off,sha
from scripts.inventory_shibuki_ui import background
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from prepare_art import rgba
import numpy as np

def make(mode):
 d=H/mode;out=d/'review';raw=(d/'originals/ST0D_0X.ARC').read_bytes();pal=entry((d/'originals/COL0D_0X.ARC').read_bytes(),5)
 bg=Image.new('RGBA',(512,256));bg.alpha_composite(background(raw,pal,3));bg.alpha_composite(background(raw,pal,4),(256,0));bg=bg.crop((0,16,320,256));bg.save(out/'background.png')
 # Unchanged partner at the native (282,432), camera y272.
 px,size,bb,_=compose_static(entry(raw,0x10102)[75776:],local_composition(aliased_composition(entry(raw,10),3,0)))
 words=struct.unpack_from('<16H',pal,37*32);partner=rgba(np.frombuffer(px,np.uint8).reshape(size[1],size[0]),words);scene=bg.copy();scene.alpha_composite(partner,(282+bb[0],432-272+bb[1]));scene.save(out/'scene.png')
 for state in range(18):
  for frame in [0,3,6,9]:
   dst=scene.copy();dst.alpha_composite(Image.open(out/f'{state:02}'/f'{frame:02}.png').convert('RGBA'),(42-80,416-272-80));dst.save(out/f'scene_{state:02}_{frame:02}.png')
 for name in ['states.png','force_poses.png','ultimate_poses.png','jacket_poses.png']:shutil.copyfile(d/'art'/name,out/name)
 exe=(d/'originals/SLUS_005.61').read_bytes();sequences={}
 for anim in [0,1,2,6]:
  address=struct.unpack_from('<I',exe,off(0x8010e514)+anim*4)[0];cursor=0;seen=set();seq=[]
  while cursor not in seen:
   seen.add(cursor);dur,flags,step,frame=struct.unpack_from('<BBbB',exe,off(address)+cursor*4);assert frame<12 and dur
   seq.append({'frame':frame,'ticks':dur,'event':flags});cursor+=step
  sequences[str(anim)]=seq
 title='하나코 나나'if mode=='ver_rin_nana'else'텐코 시부키'
 labels=['기본형'if n==0 else'+'.join(label for bit,label in [(1,'머리'),(2,'몸'),(4,'팔'),(8,'다리')]if n&bit)for n in range(16)]+['얼티밋 획득 전 · 재킷','얼티밋 획득 후 · 수영복']
 page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>TITLE · 헌터베이스 아머</title>
<style>body{background:#18212d;color:#e8f1ff;font:17px/1.65 sans-serif;margin:28px}img,canvas{image-rendering:pixelated}img{max-width:100%}select,button{font:inherit;padding:7px;background:#304259;color:white;border:1px solid #789}label{display:inline-block;margin:6px}.controls{position:sticky;top:0;background:#18212d;padding:10px;z-index:1}.grid{display:flex;flex-wrap:wrap;gap:16px}figure{margin:0;background:#263345;padding:10px}a{color:#9ed2ff}canvas{width:640px;max-width:100%;background:#000}</style>
<h1>TITLE · 헌터베이스 전신 의상</h1><p>실제 게임의 MIPS 그리기 명령에서 복원한 216개 그림입니다. <strong>아래는 원본 배경과 합성한 시뮬레이션이며 실제 플레이 캡처가 아닙니다.</strong> 게임 좌표 이동·대사·효과음은 재현하지 않습니다.</p>
<div class="controls"><label>상태 <select id="state"></select></label><label>동작 <select id="anim"><option value="0">대기·눈 깜빡임</option><option value="2">대화·손짓</option><option value="6">놀람·대화</option><option value="1">출격 자세 전환</option><option value="manual">프레임 직접 보기</option></select></label><label>프레임 <select id="frame"></select></label><button id="play">일시정지</button></div><canvas id="view" width="320" height="240"></canvas>
<p id="caption"></p><p>기본형 12그림은 기존 표시 픽셀 그대로입니다. 나나는 머리=모자, 몸=드레스 상체, 팔=소매, 다리=구두·흰 치맛단·뒤 베일입니다. 얼티밋 전후는 기존에 확정한 재킷 → 수영복 순서입니다.</p>
<h2>18가지 상태</h2><img src="states.png"><h2>포스 완성형의 12그림</h2><img src="force_poses.png"><h2>얼티밋 획득 전</h2><img src="jacket_poses.png"><h2>얼티밋 획득 후</h2><img src="ultimate_poses.png"><h2>실제 배경 위 배치 비교</h2><div class="grid">FIGURES</div>
<p><a href="../../../../docs/HQ_ARMOR_20261109.md">적용 범위와 검사 기록</a> · <a href="../../../../work/hq_armor_20261109/generation_receipt.json">이미지 생성 입력·프롬프트 기록</a></p>
<script>const labels=LABELS,seq=SEQUENCES;const st=document.querySelector('#state'),an=document.querySelector('#anim'),fr=document.querySelector('#frame'),cv=document.querySelector('#view'),ctx=cv.getContext('2d');let playing=true,step=0,tick=0,last=performance.now();const imgs={};let bg=new Image();bg.src='scene.png';
labels.forEach((v,i)=>st.add(new Option(v,i)));for(let i=0;i<12;i++)fr.add(new Option(i,i));
for(let s=0;s<18;s++)for(let f=0;f<12;f++){let im=new Image();im.src=String(s).padStart(2,'0')+'/'+String(f).padStart(2,'0')+'.png';imgs[s+':'+f]=im;}
function reset(){step=0;tick=0}st.onchange=reset;an.onchange=reset;fr.onchange=()=>{an.value='manual'};document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'일시정지':'재생'};
function draw(now){if(playing&&an.value!='manual'){tick+=(now-last)*60/1000;let q=seq[an.value];while(tick>=q[step].ticks){tick-=q[step].ticks;if(an.value==='1'&&step===q.length-1){tick=0;break}step=(step+1)%q.length}fr.value=q[step].frame}last=now;ctx.clearRect(0,0,320,240);if(bg.complete)ctx.drawImage(bg,0,0);let im=imgs[st.value+':'+fr.value];if(im.complete)ctx.drawImage(im,-38,64);document.querySelector('#caption').textContent=labels[st.value]+' / 프레임 '+fr.value+' / 원래 동작 시간표 60Hz 기준';requestAnimationFrame(draw)}requestAnimationFrame(draw);
</script></html>'''
 figures=''.join(f'<figure><figcaption>{labels[n]}</figcaption><img width="480" src="scene_{n:02}_00.png"></figure>'for n in [0,1,2,4,8,15,16,17])
 page=page.replace('TITLE',title).replace('FIGURES',figures).replace('LABELS',json.dumps(labels,ensure_ascii=False)).replace('SEQUENCES',json.dumps(sequences));(out/'index.html').write_text(page,'utf8');(out/'native_animation_sequences.json').write_text(json.dumps(sequences,indent=2))
 print(mode,'review prepared')
if __name__=='__main__':
 for mode in ['ver_rin_nana','ver_buki_riko']:make(mode)
