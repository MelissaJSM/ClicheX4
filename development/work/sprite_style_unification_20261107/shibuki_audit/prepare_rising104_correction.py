"""새104 원화의 팔 접점 교정 입력. 원화 몸체는 변형하지 않는다."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent
def main():
    out=H/'rising104_arm_correction01';assert not out.exists();out.mkdir()
    source=H/'rising_fire_inputs01/page02/generated.png'
    image=Image.open(source).convert('RGBA');assert image.size==(1536,1024)
    board=Image.new('RGBA',(1536,1024));guide=board.copy()
    for row in range(2):
        crop=image.crop((512,row*512,1024,(row+1)*512))
        board.alpha_composite(crop,(128+row*768,256))
    board.save(out/'edit_input.png');guide=board.copy();draw=ImageDraw.Draw(guide)
    # These guides show the original native fist location, not newly painted anatomy.
    for col in range(2):
        ox=128+col*768;oy=256
        draw.rectangle((ox+144,oy+72,ox+184,oy+104),outline=(0,255,255,255),width=3)
        draw.line((ox+160,oy+56,ox+160,oy+120),fill=(0,255,255,255),width=2)
    guide.save(out/'target_guide.png')
    data={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'cells':[{'form':'base','source_crop':[512,0,1024,512],'destination':[128,256]},
                   {'form':'fourth','source_crop':[512,512,1024,1024],'destination':[896,256]}],
          'source_scale_unchanged':True,'correction_native_fist_translation':[3,-1],
          'reason':'새104 주먹이 원불꽃에서 더 멀어져 팔 국소 교정 입력을 준비했다. 몸 전체 이동·팔 가로 늘임 없음.',
          'generation_pending':True}
    (out/'input.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
if __name__=='__main__':main()
