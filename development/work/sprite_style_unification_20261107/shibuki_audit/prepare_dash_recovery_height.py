"""대시 복귀 81/83 고정 셀 교정 입력과 이전 생성 영수증 기록."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw

H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

for n,filename in ((3,'exec-0228b734-7ce9-43ce-935d-2b1c297a494b.png'),(4,'exec-a688b189-7468-486b-ba12-9b88bacfa7f9.png')):
    d=H/f'dash_detail_inputs{n:02}'
    exact=(d/'prompt.txt').read_text('utf8')
    if not (d/'prompt_used.txt').exists():(d/'prompt_used.txt').write_text(exact,encoding='utf8')
    assert (d/'prompt_used.txt').read_text('utf8')==exact
    write(d/'generation_receipt.json',{'tool':'builtin imagegen','generated_sha256':sha(d/'generated.png'),
      'original_tool_filename':filename,'prompt_path':'prompt_used.txt','prompt_sha256':sha(d/'prompt_used.txt'),
      'source_manifest_sha256':sha(d/'manifest.json'),'native_registered':True,'packed':False,
      'status':'높이 국소 교정 대기' if n==3 else '공중 대시 접점 정합 대기'})

d=H/'dash_recovery_height01';d.mkdir(exist_ok=False)
target=H/'dash_detail_inputs03/generated.png';im=Image.open(target).convert('RGBA')
guide=Image.new('RGBA',im.size,(22,26,35,255));guide.alpha_composite(im)
draw=ImageDraw.Draw(guide)
for row in range(2):
    for col,ref,top in ((0,81,14),(1,83,12)):
        x=col*512;y=row*512
        draw.line((x+80,y+top*8,x+416,y+top*8),fill=(70,255,150,255),width=3)
        draw.text((x+32,y+top*8-18),f'{ref} target ear tip y={top}',fill=(70,255,150,255))
        draw.line((x+80,y+472,x+416,y+472),fill=(255,180,70,255),width=3)
        draw.text((x+32,y+476),'target sole last row y=58',fill=(255,180,70,255))
guide.save(d/'height_guide.png')
prompt='''Precise local pose correction of Image 1, the newly detailed FOUR Tenko Shibuki pixel sprites. Keep the same transparent1536x1024 canvas, three512x512 cells per row, two rows; column3 stays empty. Every cell represents a native64x64 window enlarged8x. Image2 is a MEASUREMENT GUIDE ONLY and must not appear in output. Image3 is the accepted idle/air/wall style reference; Image4 gives the old pose and original foot positions ONLY, never copy its coarse face or blank clothing.
Correct the short stature in these recovery poses by straightening the existing compact posture slightly, not by scaling or stretching the entire image and not by enlarging the head. Retain the current precise head/ears SIZE, layered lavender hair, golden eye, ear interior, short neck, two real arms, garment folds, flower and all costume details. Keep the same left-facing angle. Raise the connected head/neck/shoulders while naturally extending the torso and unbending knees only enough to match the guide; maintain the full-bodied short accepted anatomy and continuous joints. Do not make long thin legs or a long torso.
Column1/ref81: broad recovery stance, both fists down, both feet spread. Ear-tip top must be native row14 (=source y112 within each cell), both soles end on native row58 (=source y464..471). Column2/ref83: nearly upright narrow recovery stance, leading fist at collar, other hand down, rather than crouching; ear-tip top must be native row12 (=source y96) and soles end on native row58 (=source y464..471). The first input currently has both heads too low at native row16 and soles at57. Correct81 upward2 native pixels at head and83 upward4; ground soles down1. Keep feet original horizontal contacts in Image4. Face and sleeve detail must stay crisp at native size.
Both rows depict exactly the same two skeletons. Top row BASE: white/light-blue wide sleeves with red trim, red shrine skirt/cord, lavender wraps and white-red shoes. Bottom row FOURTH: black/navy body and cape, purple folded sleeves with gold trim, white fur collar, dark stockings and white/gold shoes. No pale base sleeves in Fourth. Both fully clothed. Preserve the NEW detailed garment and hair rendering from Image1, not the old reference rendering. Transparent background with absolutely no glow, haze, shadow, scenery, weapons, text, lines or guide marks. Complete separate four sprites, exact cells and fixed8x scale, no global resizing.'''
(d/'prompt.txt').write_text(prompt,encoding='utf8')
write(d/'input.json',{'target':str(target),'target_sha256':sha(target),'guide':'height_guide.png','guide_sha256':sha(d/'height_guide.png'),
 'native_target':{'81':{'ear_tip_y':-22,'sole_y':22},'83':{'ear_tip_y':-24,'sole_y':22}},
 'scope':'기본/포스 두 의상 81·83 복귀 높이. 새 머리·의상 세부 보존, 전신 배율 변경 금지.',
 'game_modified':False})
print(d)
