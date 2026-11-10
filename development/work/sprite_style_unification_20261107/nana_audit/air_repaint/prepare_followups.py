"""나머지7개 비사격 공중/착지 포즈 입력; 각 참조를 생략하지 않는다."""
from pathlib import Path
import sys,json
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,digest
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent');reports=[]
    for name,refs in [('basic_air_middle',[35,37,41,43]),('basic_air_landing',[45,49,53])]:
        cell=768;line=48;board=Image.new('RGBA',(cell*2,(cell+line)*2));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
        for k,n in enumerate(refs):
            im=a.composite(n)[0].crop((112,112,208,208)).resize((cell,cell),Image.Resampling.NEAREST);x=k%2*cell;y=k//2*(cell+line);board.alpha_composite(im,(x,y+line));draw.text((x+18,y+8),f'POSE {n}',font=font,fill=(90,100,110,255))
        dest=D/(name+'.png');board.save(dest);reports.append({'file':dest.name,'sha256':digest(dest),'refs':refs})
    write(D/'followup_inputs.json',{'source_arc_sha256':sha(a.data),'pages':reports,'pending_generation':True})
if __name__=='__main__':main()
