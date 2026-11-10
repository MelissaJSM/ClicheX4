"""호흡3자세 전체 재제작 원화를 같은 팔레트·발 기준점으로 정규화한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_nana_fourth_pilot import require,write
from scripts.extract_zero import save_image
from scripts.project import digest


def prepare(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_fourth_armor') and not out.exists(),'Fresh armor work folder required')
    source=ROOT/'work/ver_rin_nana/nana_fourth_armor/idle_redraw_v1/generated.png'
    require(digest(source)=='4272b16031b6f29f830d2c4abd9c630bdae0333850b40b9c9ef220fa60da9f09','Generated art changed')
    im=Image.open(source).convert('RGBA');require(im.getchannel('A').getextrema()==(0,255),'True alpha required')
    words=struct.unpack('<16H',(ROOT/'out/ver_rin_nana/nana_fourth_pilot_v2/palette.bin').read_bytes())
    pal=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
    out.mkdir(parents=True);frames=[];board=Image.new('RGB',(3*256,384),'#303841');draw=ImageDraw.Draw(board)
    for i,(n,height) in enumerate(((0,45),(115,44),(119,46))):
        crop=im.crop((i*im.width//3,0,(i+1)*im.width//3,im.height));ys,xs=np.nonzero(np.array(crop.getchannel('A'))>=128)
        box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));v=normalize(crop.crop(box),height,pal,width=28)
        x=68;y=103-height
        canvas=np.zeros((160,160),np.uint8);canvas[y:y+height,x:x+28]=v
        pic=save_image(canvas.tobytes(),(160,160),words,out/f'master_{n:03}.png').convert('RGBA')
        zoom=pic.crop((56,52,100,108)).resize((264,336),Image.Resampling.NEAREST);board.paste(zoom,(i*256,32),zoom)
        draw.text((i*256+4,4),str(n),fill='white');frames.append({'frame':n,'crop':box,'height':height,'width':28,'x':x,'y':y})
    board.save(out/'review.png');write(out/'source.json',{'source':source.relative_to(ROOT).as_posix(),'sha256':digest(source),'tool':'built_in_imagegen','prompt':source.with_name('prompt.txt').relative_to(ROOT).as_posix(),'frames':frames,'whole_figure_redraw':True})
    print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'frames':frames}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
