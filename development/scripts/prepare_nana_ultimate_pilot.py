"""얼티밋 두 자세 기준안을 실제 팔레트와 눈·발 기준점에 정규화한다. BIN 미수정."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.analyze_nana_ultimate import PARENT,PARENT_SHA,REF,SOURCE_SHA
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.prepare_nana_pilot import normalize
from scripts.extract_zero import save_image
from scripts.project import digest
ART=ROOT/'work/ver_rin_nana/nana_ultimate_armor/pilot_v1'
ANALYSIS=ROOT/'work/ver_rin_nana/nana_ultimate_armor/analysis_v2'
GENERATED_SHA='6952f79ded0e64b862e762bd4aa323568ee69a3341f0c58fc98093ffaabbc959'
REF_SHA='56883cdbf86d44d4fff8d161b89647435a43f2e9a398f8ed952c2724f4f2c67c'

def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'out/ver_rin_nana') and not out.exists(),'Fresh variant preview required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(REF)==REF_SHA and digest(ART/'generated.png')==GENERATED_SHA,'Inputs changed')
    analysis=json.loads((ANALYSIS/'analysis.json').read_text('utf8'));arc=(ANALYSIS/'PL00_U.ARC').read_bytes();require(digest(ANALYSIS/'PL00_U.ARC')==analysis['resources']['PL00_U.ARC']['sha256'],'Reference ARC changed')
    image=Image.open(ART/'generated.png').convert('RGBA');require(image.getchannel('A').getextrema()==(0,255),'Real transparency required')
    words=list(struct.unpack_from('<16H',entry(arc,9)));words=words[:16];words[15]=0x8000|26|(27<<5)|(28<<10)
    colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    out.mkdir(parents=True);frames=[]
    for i,n in enumerate((0,85)):
        crop=image.crop((i*image.width//2,0,(i+1)*image.width//2,image.height));ys,xs=np.nonzero(np.array(crop.getchannel('A'))>=128);box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=crop.crop(box)
        # 토끼귀 때문에 전체를45px로 축소하지 않는다. 눈-발 거리를 우선한다.
        variants=[]
        for h in range(48,54):
            v=normalize(crop,h,colors);ey,ex=np.nonzero((v==14)&(np.indices(v.shape)[0]<h//2))
            if len(ey):variants.append((abs(103-h+float(ey.mean())-68),h,v,ey,ex))
        require(bool(variants),'Eye lost during palette conversion');_,h,v,ey,ex=min(variants,key=lambda q:(q[0],abs(q[1]-50)))
        y=103-h;x=round(76-float(ex.mean()));require(0<=x and x+v.shape[1]<=160,'Outside native canvas')
        canvas=np.zeros((160,160),np.uint8);canvas[y:y+h,x:x+v.shape[1]]=v;native=save_image(canvas.tobytes(),(160,160),words,out/f'ultimate_{n:03}_indexed.png').convert('RGBA');native.save(out/f'ultimate_{n:03}.png');(out/f'ultimate_{n:03}.indices').write_bytes(canvas.tobytes())
        target_eye=[x+float(ex.mean()),y+float(ey.mean())];feet=np.nonzero(canvas[100:103])[1]
        require(abs(target_eye[0]-76)<=0.5 and abs(target_eye[1]-68)<=0.5,'Eye anchor differs');require(native.getbbox()[3]==103,'Sole differs');require(len(set(canvas.flat)-{0})<=15,'Too many colors')
        frames.append({'frame':n,'source_crop':box,'normalized_size':list(v.shape[::-1]),'position':[x,y],'opaque_bbox':list(native.getbbox()),'eye_center':target_eye,'sole_y':102,'foot_center':float(feet.mean()),'used_opaque_colors':len(set(canvas.flat)-{0}),'opaque_pixels':int(np.count_nonzero(canvas)),'body_eye_to_sole':102-target_eye[1],'packing_verified':False})
    (out/'palette.bin').write_bytes(struct.pack('<16H',*words));font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
    board=Image.new('RGB',(960,650),'#242b39');draw=ImageDraw.Draw(board)
    for col,(prefix,label) in enumerate([('accepted_base','수용 나나 기본형'),('accepted_fourth','수용 포스아머'),('ultimate','얼티밋 · 분홍 재킷 시안')]):
        draw.text((col*320+10,10),label,font=font,fill='white')
        for row,n in enumerate((0,85)):
            p=(out if prefix=='ultimate' else ANALYSIS)/f'{prefix}_{n:03}.png';pic=Image.open(p).convert('RGBA').crop((40,48,120,112));top=40+row*280
            big=pic.resize((320,256),Image.Resampling.NEAREST);board.paste(big,(col*320,top),big);draw.line((col*320+8,top+55*4,col*320+312,top+55*4),fill='#526577');board.paste(pic,(col*320+224,top+2),pic)
            draw.text((col*320+12,top+237),'대기 · 1× / 4×' if n==0 else '사랑이 사격 · 1× / 4×',font=small,fill='#d3dfed')
    draw.text((12,614),'정적 기준안 · 실제 게임 미적용 · 눈 Y68 / 발바닥 Y102',font=small,fill='#d3dfed');board.save(out/'review_1x_4x.png')
    background=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z/runtime_framebuffer_0.png';scene=Image.open(background).convert('RGBA')
    for n,x in ((0,220),(85,280)):scene.alpha_composite(Image.open(out/f'ultimate_{n:03}.png').convert('RGBA'),(x-80,195-103))
    scene.save(out/'background_composite_1x.png');board=Image.new('RGB',(960,764),'#242b39');ImageDraw.Draw(board).text((12,9),'게임 배경 위 합성 · 실제 적용 화면 아님',font=font,fill='white');board.paste(scene.resize((960,720),Image.Resampling.NEAREST),(0,44));board.save(out/'background_composite_3x.png')
    report={'task':'ultimate_armor_nana','stage':'ART_PILOT','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'original_sha256':SOURCE_SHA,'reference':REF.relative_to(ROOT).as_posix(),'reference_sha256':REF_SHA,'generated':(ART/'generated.png').relative_to(ROOT).as_posix(),'generated_sha256':GENERATED_SHA,'prompt':(ART/'prompt.txt').relative_to(ROOT).as_posix(),'image_tool':'built_in_imagegen','outfit':'left_pink_jacket','outfit_choice_user_confirmed':False,'frames':frames,'palette_words':words,'game_modified':False,'runtime_verified':False,'art_user_approved':False,'packing_verified':False,'body_scale_rule':'Accepted eye Y68 and sole Y102; extra height from bunny ears','quantization':'Existing Nana RGB555 palette, one light-gray replacement; area-vote no dithering','outstanding':['의상·두 자세 미술 수용','캡슐 전 기본형 이식·파츠5 전신과의 합성','공유 대기 깜빡임·압축 예산','저장52 및 팔레트30/31','노바 본체/광선·캡슐 잔상']}
    write(out/'candidate.json',report)
    protected=json.loads((ANALYSIS/'preservation.json').read_text('utf8'))
    for q in protected['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(REF)==REF_SHA,'Input changed');write(out/'preservation.json',protected);print(json.dumps({'output':str(out),'frames':frames,'game_modified':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
