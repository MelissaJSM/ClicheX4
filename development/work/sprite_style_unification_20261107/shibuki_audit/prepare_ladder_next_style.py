"""고정배율 새 첫 페이지를 다음 그림의 정밀도 참조로 배치한다."""
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent
out=H/'ladder_detail_inputs01';board=Image.new('RGBA',(1536,1024),(0,0,0,0))
for row,name in enumerate(('base','fourth')):
 for col,n in enumerate((143,144,146)):
  im=Image.open(H/f'ladder_page01_detail02/{name}_{n:03}.png');board.alpha_composite(im.crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
board.save(out/'new_page01_native_style.png')
extra='\nAdditional native-detail requirement from the fifth reference: match the newly refined ladder hair at REAL GAME PIXEL scale, with broad lavender midtone lock-separating wedges 1 to 2 native pixels wide (8 to 16 source pixels), not thin high-resolution hairlines that disappear under 8x reduction. Keep a light hair face plus existing lavender midtone and purple shadow groups, clean tapering into the back locks. Do not fill the crown with unbroken pale lavender, thin comb-like repeated lines, black scribbles, or excessive spot noise. Bent shrine sleeves need readable white light, middle-blue fold, and compact blue-violet underfold. All five references concern this same established character; preserve the first image pose anchors.\n'
for n in(2,3):
 src=(out/f'page{n:02}_prompt.txt').read_text('utf8');(out/f'page{n:02}_detail_prompt.txt').write_text(src+extra,'utf8')
print('style input and next prompts ready')
