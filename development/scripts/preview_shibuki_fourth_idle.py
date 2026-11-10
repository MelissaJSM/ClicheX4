"""시험 ARC 재읽기로 아머 대기6참조·16조합·양쪽 버스터 색 표를 대조한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_armor import entries
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts

def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);args=p.parse_args();build=args.build.resolve()
 if not build.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Isolated build required')
 manifest=json.loads((build/'manifest.json').read_text());recipe=json.loads((build/'recipe.json').read_text());arc=(build/'modified.arc').read_bytes()
 if manifest['task']!='fourth_armor_shibuki' or sha256(arc)!=manifest['modified_archive_sha256']:raise ValueError('Unexpected trial build')
 artdir=ROOT/recipe['source_art'];es=entries(arc);g,c,pal=es[2],es[3],es[9];bank=graphics_bank(g,0,allow_bank_aliases=True);words=[list(struct.unpack_from('<16H',pal,i*32)) for i in range(3)]
 out=build/'armor_review';out.mkdir(exist_ok=False);pictures={};checks=[]
 for n in recipe['edited_frame_references']:
  f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;layers={}
  for bi in (0,5,6,7,8):
   v=canvas_from_parts(raw,f['tile_count'],composition_frame(c,bi,n));layers[bi]=v
   if bi:
    kind={5:'head',6:'body',7:'arm',8:'leg'}[bi];target=np.array(Image.open(artdir/f'{kind}_{n:03}.png'))
    if not np.array_equal(v,target):raise ValueError('Layer changed after insertion')
  for arm_type in (1,2):
   for mask in range(16):
    pic=save_image(layers[0].tobytes(),(160,160),words[0],out/'base_preview.png').convert('RGBA')
    for bit,bi in ((8,8),(1,5),(4,7),(2,6)):
     if mask&bit:
      wp=words[2 if bi==7 and arm_type==2 else 1];layer=save_image(layers[bi].tobytes(),(160,160),wp,out/'layer_preview.png').convert('RGBA');pic.alpha_composite(layer)
    expected=Image.open(artdir/f'frame_{n:03}_mask{mask:02}.png').convert('RGBA')
    if not np.array_equal(np.array(pic),np.array(expected)):raise ValueError(f'Part combination differs: {n},{mask},{arm_type}')
    checks.append({'frame':n,'mask':mask,'arm_type':arm_type,'raster_equal':True})
    if arm_type==1:pic.save(out/f'frame_{n:03}_mask{mask:02}.png');pictures[n,mask]=pic
 font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
 sheet=Image.new('RGB',(1320,490),'#253546');draw=ImageDraw.Draw(sheet)
 for i,(mask,label) in enumerate(((0,'기본형'),(1,'머리'),(2,'몸통·망토'),(4,'팔'),(8,'다리'),(15,'포스 아머 완성형'))):
  pic=pictures[0,mask];im=pic.crop((55,50,105,110));sheet.paste(im,(i*220+85,53),im);im=im.resize((200,240),Image.Resampling.NEAREST);sheet.paste(im,(i*220+10,135),im);draw.text((i*220+12,15),label,font=font,fill='white')
 draw.text((14,405),'동일 1배·4배 / 패치 ARC 재조립 미리보기 · 실제 게임 실행 화면 아님',font=font,fill='#d4deec')
 draw.text((14,437),'머리·발 기준 유지 / 기본형 보존 / 아머는 대기 6참조만 제작한 시험본',font=font,fill='#d4deec');sheet.save(out/'review_1x_4x.png')
 inv=json.loads((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json').read_text());frames=[];durations=[]
 for step in inv['idle_animation']['steps']:
  pic=pictures[step['frame'],15];bg=Image.new('RGB',(160,160),'#253546');bg.paste(pic,(0,0),pic);frames.append(bg.crop((55,50,105,110)).resize((400,480),Image.Resampling.NEAREST));durations.append(max(20,round((step['duration_ticks']+1)*1000/60)))
 frames[0].save(out/'idle.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2)
 (out/'verification.json').write_text(json.dumps({'source_arc_sha256':sha256(arc),'static_only':True,'runtime_verified':False,'combinations_checked':len(checks),'checks':checks,'scope':'idle six references; other armor motions pending'},indent=2))
 print(json.dumps({'output':str(out),'combinations_checked':len(checks),'runtime_verified':False}))

if __name__=='__main__':main()
