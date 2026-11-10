"""눈감음의 두 검은 픽셀을 제거하고, 수용된 눈동자 한 픽셀만 피부색으로 등록."""
import json,shutil,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_idle import PILOT,SEQUENCE,TICKS
from scripts.project import digest
from scripts.extract_zero import save_image

def main():
    old=ROOT/'work/ver_rin_nana/idle_production/v1';out=ROOT/'work/ver_rin_nana/idle_production/v2'
    words=struct.unpack('<16H',(PILOT/'candidate_palette.bin').read_bytes());master=Image.open(PILOT/'rin_idle147_indexed.png');blink=bytearray(master.tobytes())
    if blink[10*56+20]!=15 or blink[10*56+19]!=14:raise ValueError('Unexpected eye/skin registration')
    # Imagegen's revised blink intent is imported only at the native iris ROI.
    # Do not accept its unrelated changes to costume or framing.
    blink[10*56+20]=blink[10*56+19]
    prior=json.loads((old/'recipe.json').read_text('utf-8'))
    for n in (0,1,2,146,147):
        path=old/f'idle_{n:03}.png'
        if digest(path)!=prior['frame_sha256'][str(n)]:raise ValueError('Accepted body changed')
        shutil.copyfile(path,out/path.name)
    save_image(bytes(blink),(56,48),words,out/'idle_148.png')
    changed=[i for i,(a,b) in enumerate(zip(master.tobytes(),blink)) if a!=b]
    if changed!=[10*56+20]:raise ValueError('Changed pixels outside iris')
    prior['registration']['blink_roi']=[20,10,21,11]
    prior.update({'parent_recipe':str((old/'recipe.json').relative_to(ROOT)),'imagegen_mode':'built_in_edit','blink_fix_source':'generated_blink_fix.png','blink_fix_source_sha256':digest(out/'generated_blink_fix.png'),'blink_fix_prompt':'prompt_blink_fix.txt','blink_fix':'잘못 지정된 머리카락21/22열 복구. 실제 눈동자(20,10)1픽셀만 인접 피부색으로 치환; 나머지 얼굴/몸 픽셀 보존','native_registration_correction':'생성 프롬프트의 x22 지시는 검사 결과 잘못된 좌표. 실제 인덱스15는 x20,y10 한 픽셀로 확인하여 등록 시 수정','blink_changed_from_open_xy':[[20,10]],'blink_dark_pixels_added':0,'frame_sha256':{n:digest(out/f'idle_{n:03}.png') for n in (0,1,2,146,147,148)}})
    (out/'recipe.json').write_text(json.dumps(prior,ensure_ascii=False,indent=2)+'\n','utf-8')
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);board=Image.new('RGB',(576,208),(35,38,48));draw=ImageDraw.Draw(board)
    for i,(path,label) in enumerate(((PILOT/'rin_idle147_indexed.png','눈 뜸'),(old/'idle_148.png','이전 · 검은 점'),(out/'idle_148.png','수정 · 점 제거'))):
        pic=Image.open(path).convert('RGBA').crop((14,3,30,18)).resize((160,150),Image.Resampling.NEAREST);board.paste(pic,(i*192+16,40),pic);draw.text((i*192+8,8),label,font=font,fill='white')
    board.save(out/'blink_before_after.png')
    seq=[Image.open(out/f'idle_{n:03}.png').resize((224,192),Image.Resampling.NEAREST) for n in SEQUENCE]
    seq[0].save(out/'idle_preview_4x.gif',save_all=True,append_images=seq[1:],duration=[round(t*100/60)*10 for t in TICKS],loop=0,transparency=0,disposal=2,optimize=False)
    print(json.dumps({'output':str(out),'changed_pixels_from_open':len(changed),'dark_pixels_added':0,'other_five_frame_files_preserved':True}))

if __name__=='__main__':main()
