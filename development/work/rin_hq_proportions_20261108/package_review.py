from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
build=json.loads((W/'build.json').read_text('utf8'));out=(ROOT/build['cue']).parent/'review';out.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
cmp=Image.new('RGB',(4*280,450),(32,40,52));d=ImageDraw.Draw(cmp)
for k,(folder,n,label)in enumerate([('current',0,'이전 대기'),('candidate02',0,'수정 대기'),('current',13,'이전 출격'),('candidate02',13,'수정 출격')]):
 im=Image.open(W/folder/f'world_{n:02d}.png').convert('RGBA').crop((76,12,172,140));im=im.resize((288,384),Image.Resampling.NEAREST);cmp.paste(im,(k*280,45),im);d.text((k*280+15,12),label,font=font,fill='white')
cmp.save(out/'comparison.png')
sheet=Image.new('RGB',(7*180,2*300),(32,40,52));d=ImageDraw.Draw(sheet)
for n in range(14):
 path=W/'candidate02'/f'frame_{n:02d}.png';shutil.copyfile(path,out/path.name);im=Image.open(path).convert('RGBA');im=im.crop(im.getbbox());im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);x=n%7*180;y=n//7*300;sheet.paste(im,(x+(180-im.width)//2,y+45),im);label='대기'if n<=5 else '팔 전환'if n==6 else '대화'if n<=12 else '출격';d.text((x+12,y+12),f'{n:02d} {label}',font=font,fill='white')
sheet.save(out/'all14.png')
for source,name in [('generated_v2.png','generated_source.png'),('prompt.txt','initial_prompt.txt'),('shoulder_prompt.txt','final_prompt.txt')]:shutil.copyfile(W/source,out/name)
if (W/'runtime_v2/verification.json').exists():
 for src in (W/'runtime_v2').glob('*.png'):shutil.copyfile(src,out/('actual_'+src.name))
 shutil.copyfile(W/'runtime_v2/verification.json',out/'runtime_verification.json')
print(str(out))
