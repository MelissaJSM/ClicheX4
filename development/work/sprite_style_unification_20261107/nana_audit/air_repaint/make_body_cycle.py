"""전11몸체+대기 연결 미술 시각화. 실제 점프 물리/타이밍 재현이 아니다."""
from pathlib import Path
import sys,json
from PIL import Image,ImageDraw,ImageFont
import numpy as np
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D)]
from preview_restore import Archive,sha,write
from review_all_bodies import source
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'basic_sequence_review_v1';refs=list(range(33,55,2))+[0];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    def tile(n,new,scale=3):
        idx=np.array(Image.open(source(n)/f'base_{n:03}.png'))if new and n else a.layer(n)[0]
        im=a.rgba(idx).crop((124,124,196,196));canvas=Image.new('RGBA',im.size,(187,199,205,255));canvas.alpha_composite(im);draw=ImageDraw.Draw(canvas);draw.line((31,36,41,36),fill=(110,135,145,255));draw.line((36,33,36,39),fill=(110,135,145,255))
        return canvas.resize((72*scale,72*scale),Image.Resampling.NEAREST).convert('RGB')
    frames=[]
    for n in refs:
        board=Image.new('RGB',(432,262),(187,199,205));dr=ImageDraw.Draw(board);dr.text((8,4),f'현재 {n}',font=font,fill='black');dr.text((224,4),f'새 그림 {n}',font=font,fill='black');board.paste(tile(n,False),(0,30));board.paste(tile(n,True),(216,30));dr.text((8,243),'미술 비교:80ms/자세, 실제 점프 물리 아님',font=font,fill='black');frames.append(board)
    frames[0].save(out/'body_cycle_preview.gif',save_all=True,append_images=frames[1:],duration=80,loop=0,disposal=2,optimize=False)
    for page in range(3):
        ns=refs[page*4:page*4+4];board=Image.new('RGB',(864,492),(187,199,205));draw=ImageDraw.Draw(board)
        for i,n in enumerate(ns):
            draw.text((i*216+10,5),f'현재 {n}',font=font,fill='black');board.paste(tile(n,False),(i*216,28));draw.text((i*216+10,247),f'새 그림 {n}',font=font,fill='black');board.paste(tile(n,True),(i*216,271))
        board.save(out/f'body_cycle_strip_{page+1}.png')
    write(out/'cycle.json',{'frames':refs,'duration_ms':80,'source_arc_sha256':sha(a.data),'actual_game_physics':False,'actual_native_duration':False,
        'scope':'11개 새 몸체와 대기를 한 원점에서 빠짐없이 비교하는 미술 루프. 각 자세80ms는 비교용이며 게임의 state전환/수직이동/타이밍을 대신하지 않는다. 실제 표는 manifest.json에 별도 보존.'})
if __name__=='__main__':main()
