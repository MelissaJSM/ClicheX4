"""다음 Nana 벽4키의 원래 접점과 대기 스타일 입력을 준비한다."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(Path(__file__).parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from src.psx_player import composition_frame
from PIL import Image,ImageDraw,ImageFont
import numpy as np
D=Path(__file__).parent;OUT=D/'wall_repaint';KEYS=[55,57,61,65]
SOURCE=D/'base_run_repaint/packed_joint_v2/PL00_U.ARC';EXPECTED='b5b3157a5c09c8603eec579f66251d8c69228b5948ceb9f35b5303ac52dd6f97'
def page(a,poses,path,scale=8):
    size=96;cw,ch=size*scale,size*scale+48;board=Image.new('RGBA',(cw*2,ch*2),(0,0,0,0));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22)
    for k,(label,n,mask)in enumerate(poses):
        im=a.composite(n,mask)[0].crop((112,112,208,208)).resize((cw,size*scale),Image.Resampling.NEAREST);x=k%2*cw;y=k//2*ch;board.alpha_composite(im,(x,y+48));draw.text((x+18,y+8),label,font=font,fill=(90,100,110,255))
    board.save(path)
def main():
    need(digest(SOURCE)==EXPECTED,'Source SHA');OUT.mkdir(exist_ok=True);a=Archive(SOURCE.read_bytes());page(a,[(f'POSE {n}',n,0)for n in KEYS],OUT/'basic_wall_keys.png');page(a,[('STYLE IDLE 0',0,0),('STYLE FIRE 85',85,0),('NEW RUN 7',7,0),('NEW RUN 15',15,0)],OUT/'basic_style_master.png')
    records=[]
    for n in range(55,67):
        ar=a.layer(n)[0];y,x=np.nonzero(ar);ey,ex=np.nonzero(ar==14);f=a.banks[0]['frames'][n];eye=[float(np.median(ex)-160),float(np.median(ey)-160)]if len(ex)else None
        records.append({'ref':n,'rgba_sha256':sha(a.composite(n)[0].tobytes()),'indexed_sha256':sha(ar.tobytes()),'bbox_world':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],'eye_world':eye,'tile_count':f['tile_count'],'stream_aliases':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],'parts_by_bank':{str(pb):len(composition_frame(a.c,pb,n)['parts'])for pb in(0,5,6,7,8)}})
    helper.grid([(f'현재 벽 {n}',[('기본 대기',a.composite(0)[0]),('기본',a.composite(n)[0]),('포스 대기',a.composite(0,15)[0]),('포스',a.composite(n,15)[0])])for n in KEYS],OUT/'native_before.png',6)
    write(OUT/'inputs.json',{'source_arc':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':EXPECTED,'keys':KEYS,'scope':'먼저기본벽4키,다음59/63및사격짝까지12참조전체.현재기본/포스모든기존원화보존.','frames':records,'inputs':{p.name:digest(p)for p in(OUT/'basic_wall_keys.png',OUT/'basic_style_master.png')}})
    print(json.dumps({'out':str(OUT),'refs':[r['ref']for r in records]}))
if __name__=='__main__':main()
