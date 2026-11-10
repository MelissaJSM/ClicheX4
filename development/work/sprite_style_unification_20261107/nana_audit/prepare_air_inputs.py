"""공중 전체22참조와4키의 원래 원점/동작표를 추출해 다음 새 원화 입력을 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path[:0]=[str(ROOT),str(D/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
from src.psx_player import composition_frame
SOURCE=D/'wall_repaint/packed_wall_candidate_v4/PL00_U.ARC';EXPECTED='03ebbfa01fa63772a61888b7a0022323090807b07b87f36bfa524cc755cf750d';OUT=D/'air_repaint';KEYS=[33,39,47,51]
def page(a,poses,dest):
    cell=768;line=48;board=Image.new('RGBA',(cell*2,(cell+line)*2));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    for k,(label,n,mask)in enumerate(poses):
        im=a.composite(n,mask)[0].crop((112,112,208,208)).resize((cell,cell),Image.Resampling.NEAREST);x=k%2*cell;y=k//2*(cell+line);board.alpha_composite(im,(x,y+line));draw.text((x+18,y+8),label,font=font,fill=(90,100,110,255))
    board.save(dest)
def main():
    need(digest(SOURCE)==EXPECTED,'Parent');a=Archive(SOURCE.read_bytes());OUT.mkdir(exist_ok=True);page(a,[(f'POSE {n}',n,0)for n in KEYS],OUT/'basic_air_keys.png');page(a,[('STYLE IDLE 0',0,0),('STYLE FIRE 85',85,0),('NEW RUN 7',7,0),('NEW WALL 63',63,0)],OUT/'basic_style_master.png');page(a,[(f'FOURTH POSE {n}',n,15)for n in KEYS],OUT/'fourth_air_keys.png');records=[]
    for n in range(33,55):
        ar=a.layer(n)[0];y,x=np.nonzero(ar);ey,ex=np.nonzero(ar==14);f=a.banks[0]['frames'][n];records.append({'ref':n,'bbox':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],'eye':[float(np.median(ex)-160),float(np.median(ey)-160)]if len(ex)else None,'rgba_sha256':sha(a.composite(n)[0].tobytes()),'indexed_sha256':sha(ar.tobytes()),'tile_count':f['tile_count'],'aliases':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],'parts':{str(pb):len(composition_frame(a.c,pb,n)['parts'])for pb in(0,5,6,7,8)}})
    refs=list(range(33,55,2))
    for i in range(0,len(refs),4):helper.grid([(f'air {n}/{n+1}',[('기본 대기',a.composite(0)[0]),('현재 기본',a.composite(n)[0]),('현재 기본 사격',a.composite(n+1)[0]),('포스 대기',a.composite(0,15)[0]),('현재 포스',a.composite(n,15)[0]),('현재 포스 사격',a.composite(n+1,15)[0])])for n in refs[i:i+4]],OUT/f'current_{i//4+1}.png',5)
    m=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));animations=[]
    for p in m['characters']['nana']['forms']['base']['animations']:
        if p['id']in(10,11,12,122,123,124):animations.append({k:p[k]for k in('id','label','address','steps')})
    write(OUT/'inputs.json',{'parent_arc':SOURCE.relative_to(ROOT).as_posix(),'parent_arc_sha256':EXPECTED,'first_keys':KEYS,'full_scope':list(range(33,55)),'excluded_93_94':'공중대시 진입/종료: 다음 대시 묶음','frames':records,'animations_from_hash_bound_prior_exe':animations,'new_art_generated':False,'native_packed':False});print(json.dumps({'out':str(OUT),'keys':KEYS,'scope':len(records)}))
if __name__=='__main__':main()
