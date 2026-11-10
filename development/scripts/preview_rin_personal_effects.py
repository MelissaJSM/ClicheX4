"""게임 자산을 팔레트대로 복원한 효과 색상 비교. 실기 영상이 아니다."""
import sys,struct,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_idle import entry
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition

def main():
    folder=ROOT/'work/ver_rin_nana/personal_effects/v1';before=(ROOT/'out/ver_rin_nana/rin_specials_20261028T235513740858Z/modified.arc').read_bytes();after=(folder/'modified.arc').read_bytes()
    v=(ROOT/'work/ver_rin_nana/live_poc/20261028T235732680981Z/vram.bin').read_bytes();board=Image.new('RGB',(1100,1240),(35,38,48));draw=ImageDraw.Draw(board)
    for row,arc in enumerate((before,after)):
        g=entry(arc,2)[1];p=entry(arc,3)[1];words=struct.unpack_from('<16H',entry(arc,9)[1]);draw.text((10,row*620+8),'BEFORE' if row==0 else 'RIN COLORED',fill='white')
        for col,(bi,n) in enumerate(((0,55),(0,58),(1,11))):
            f=graphics_bank(g,bi)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;px,size,*_=compose_launch(raw,f['tile_count'],composition_frame(p,0 if bi==0 else 5,n));im=save_image(px,size,words,folder/f'warp_{row}_{bi}_{n}.png').convert('RGBA');im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST);board.paste(im,(col*220,row*620+45),im)
        for col,n in enumerate((105,108,113),3):
            c=composition_frame(p,1,n);px,size,*_=compose_static(entry(arc,0x10206)[1],local_composition(c));offset=480*2048+(2+c['parts'][0]['clut'])*32;pal=struct.unpack_from('<16H',v,offset);im=save_image(px,size,pal,folder/f'orb_{row}_{n}.png').convert('RGBA');im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST);board.paste(im,(660+(col-3)*140,row*620+90),im)
    board.save(folder/'comparison.png');print(str(folder/'comparison.png'))

if __name__=='__main__':main()
