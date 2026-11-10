"""138의 가는 종아리/옅은 그늘을 국소 원화로 보완하는 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write
def main():
 a=Archive((N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC').read_bytes());out=D/'settle_legs_inputs_v1';out.mkdir(exist_ok=False)
 target=Image.new('RGBA',(1536,1024));guide=target.copy();style=Image.new('RGBA',(1536,1024));frames=[]
 for i,(form,pal,mask)in enumerate((('before',16,15),('after',0,0))):
  p=D/f'common_hands_probe_v1/{form}_138.png';z=np.array(Image.open(p));pic=a.rgba(z,pal).crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST);target.paste(pic,(i*768,0));guide.paste(pic,(i*768,0));dr=ImageDraw.Draw(guide)
  for box in((-17,4,15,21),(-7,-7,4,4)):
   x0,y0,x1,y1=box;dr.rectangle((i*768+(x0+48)*8,(y0+64)*8,i*768+(x1+48)*8,(y1+64)*8),outline=(0,220,255,255),width=3)
  dr.text((i*768+25,25),f'138 {form}: calf shadows / side contour only',fill=(0,220,255,255))
  for j,(name,im)in enumerate((('ACCEPTED IDLE',a.composite(0,mask)[0]),('ACCEPTED PREVIOUS137',a.rgba(np.array(Image.open(D/f'common_hands_probe_v1/{form}_137.png')),pal)))):
   pic=im.crop((128,120,192,184)).resize((384,384),Image.Resampling.NEAREST);style.paste(pic,(i*768+j*384,300));ImageDraw.Draw(style).text((i*768+j*384+10,270),f'{form} {name}',fill='white')
  frames.append({'form':form,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'whole_cell_origin':[48,64],'native_cell':[96,128]})
 target.save(out/'edit_target.png');guide.save(out/'edit_guide.png');style.save(out/'style_reference.png')
 # Same-world crop board: no helper recentering of already-cropped inputs.
 board=Image.new('RGB',(6*288,420),'#b8c2c9');dr=ImageDraw.Draw(board)
 for i,(name,z)in enumerate([('idle',a.layer(0)[0]),('old138',a.layer(138)[0])]+[(f'new{n}',np.array(Image.open(D/f'common_hands_probe_v1/after_{n:03}.png')))for n in(135,136,137,138)]):
  im=a.rgba(z).crop((142,160,178,184)).resize((288,192),Image.Resampling.NEAREST);board.paste(im,(i*288,50),im);dr.text((i*288+10,10),name,fill='black');small=a.rgba(z).crop((136,120,184,184));board.paste(small,(i*288+115,280),small)
 board.save(out/'lower_body_comparison.png')
 prompt='''Use case: precise-object-edit. Edit Image1, keeping its EXACT1536x1024 canvas and two full-body sprites in the same two fixed768x1024 cells. Left is the adult heroine wearing her pink jacket, right is the identical adult heroine in her accepted black-and-pink athletic costume. These are neutral full-body game animation sprites, not a portrait or anatomy close-up.
Change only the lower-leg volume and shadow contour, plus the small torso-side shadow identified by the cyan boxes in Image2. Image3 is a REFERENCE ONLY for the established small sprite's calf fullness and readable dark shadow clusters. The current138 has calves that taper too narrowly and have almost no dark separation beneath the knees. Restore modest normal calf volume matching the reference at this exact scale, keeping the same knees, ankles, feet, stance and body length. Preserve the natural knee-to-calf bend. Keep the two legs clearly separate. Strengthen the shadow-facing side of each calf and knee with a few clean dark peach/brown and near-black pixel clusters as seen in the accepted reference. The lit front skin remains light. Do not draw a uniform thick black outline around all skin. Preserve the white/gray shoes with lime-green ankle bands, their current size, floor and exact toe locations. The two costume versions must use identical leg geometry and shading.
This is pixel art on a96x128 logical grid per cell, enlarged8x. Every silhouette or shadow cluster should survive reduction to that native grid: use deliberate pixel-size color blocks, not single high-resolution hairline strokes. Keep the small side-of-waist shadow clean and connected to the original costume without narrowing the torso. Do not change thighs, body height, torso pose, costume design or coverage.
Everything else is LOCKED: detailed pink hair and both ear accessories, green eye and face, head dimensions, raised screen-left arm with compact pink pistol pointing upward above the head, opposite arm and hand, jacket or athletic top, belt and shorts, hip/foot positions and all empty padding. Do not lower the weapon, resize or shift the sprite, add another gun, or redraw the face. Output only the corrected TWO full figures on true transparent background, in exactly the same positions. No cyan markings, labels, glow, shadow, ground, checkerboard or background.'''
 (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'frames':frames,'policy':'새 원화 국소 보완. 전신 스케일/옛몸 복사/코드 임의 윤곽 추가 없음.','files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in sorted(out.iterdir())if p.is_file()]});print(out)
if __name__=='__main__':main()
