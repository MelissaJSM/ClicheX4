"""새 기본 자세를 유지하는 포스 의상 재작화 입력만 구성한다."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from register_cycle import PAGES
from preview_restore import Archive,sha,digest,write,need
from PIL import Image,ImageDraw,ImageFont
import numpy as np
D=Path(__file__).parent

def board(images,path,title):
    out=Image.new('RGB',(1536,1648),'#b5c1c9');dr=ImageDraw.Draw(out)
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',24)
    for i,(n,im) in enumerate(images):
        alpha=np.array(im.getchannel('A'));alpha[112:208,112:208]=0
        need(not alpha.any(),'Source clipped')
        x=i%2*768;y=i//2*824
        tile=im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST)
        out.paste(tile,(x,y+56),tile);dr.text((x+12,y+12),f'{title} {n}',font=font,fill='#15202b')
    out.save(path)

def main():
    out=D/'fourth_inputs';out.mkdir(exist_ok=True)
    a=Archive((D/'baseline_PL00_U.ARC').read_bytes());need(sha(a.data)=='18be60ea9e6745abf2309611cc9617e76acda4ebd984f7abf2995c457ec06908','Baseline changed')
    rows=[]
    for page,(_,refs) in enumerate(PAGES,1):
        images=[(n,a.rgba(np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png')))) for n in refs]
        path=out/f'new_base_page{page}.png';board(images,path,'새 기본 자세: 유지')
        old=out/f'old_fourth_page{page}.png';board([(n,a.composite(n,15,1)[0])for n in refs],old,'기존 포스 의상: 자세/디테일 복사 금지')
        rows.append({'page':page,'refs':refs,'new_base':str(path.relative_to(ROOT)),'new_base_sha256':digest(path),'old_fourth':str(old.relative_to(ROOT)),'old_fourth_sha256':digest(old)})
    board([(0,a.composite(0,15,1)[0]),(85,a.composite(85,15,1)[0]),(0,a.composite(0,0,1)[0]),(85,a.composite(85,0,1)[0])],out/'idle_and_fire_master.png','현재 수용 기준')
    write(out/'manifest.json',{'parent_arc_sha256':sha(a.data),'pages':rows,'idle_master_sha256':digest(out/'idle_and_fire_master.png'),'constraints':['새 기본16의 머리/눈/몸통/무릎/발 및 사랑이 위치 유지','포스 대기와 같은 검정 베일·흰 프릴·맨다리·붉은 신발','기본층 불투명 범위를 완전히 덮는 등록 필요: 레이어 투명도는 기존 기본픽셀을 지우지 못함','팔/몸통을 색으로 늘려 채우지 말고 원화의 소재·명암·윤곽 유지','사용자 수용 head5/body6/arm7/leg8(뒤베일 포함) 의미소유 유지'],'runtime_verified':False,'art_generated':False})
    print(json.dumps({'pages':4,'out':str(out)}))
if __name__=='__main__':main()
