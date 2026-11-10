"""통합 아머 ARC의 모든 유효 참조·부분 장착 조합을 재조립해 확인한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_armor import entries
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args();build=a.build.resolve()
    if not build.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Isolated build required')
    manifest=json.loads((build/'manifest.json').read_text(encoding='utf-8'));recipe=json.loads((build/'recipe.json').read_text(encoding='utf-8'));arc=(build/'modified.arc').read_bytes()
    if manifest['task']!='fourth_armor_shibuki' or sha256(arc)!=manifest['modified_archive_sha256']:raise ValueError('Armor build mismatch')
    parent=ROOT/recipe['parent_build'];old=entries((parent/'modified.arc').read_bytes());es=entries(arc);g,c,pal=es[2],es[3],es[9];bank=graphics_bank(g,0,allow_bank_aliases=True)
    paths={0:ROOT/'work/ver_buki_riko/shibuki_art/fourth_armor_v1/layers03',1:ROOT/'work/ver_buki_riko/shibuki_art/fourth_armor_motion_v1/layers06',2:ROOT/recipe['source_art']}
    tables=[]
    for row in range(3):
        words=struct.unpack_from('<16H',pal,row*32);v=np.zeros((256,4),np.uint8);v[:,3]=255;v[0,3]=0
        for i,w in enumerate(words):v[i,:3]=[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31]
        tables.append(v)
    out=build/'armor_full_review';out.mkdir(exist_ok=False);checks=[];pictures={};transparent=[]
    frames=sorted(set(range(237))-{105,*range(175,183)})
    for n in frames:
        f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        actual={bi:canvas_from_parts(raw,f['tile_count'],composition_frame(c,bi,n)) for bi in (0,5,6,7,8)}
        art=paths[0 if n in (0,115,116,117,118,119) else 1 if 1<=n<=32 else 2]
        expected={0:actual[0]}
        for kind,bi in (('head',5),('body',6),('arm',7),('leg',8)):
            target=np.zeros((160,160),np.uint8) if n==198 else np.array(Image.open(art/f'{kind}_{n:03}.png'))
            if n in (106,107,108):
                oldbank=graphics_bank(old[2],0,allow_bank_aliases=True);of=oldbank['frames'][n];oraw=decode_stream(old[2],of['offset'],of['limit'],of['tile_count']*128).data;cp=composition_frame(old[3],bi,n);qs=[q for q in cp['parts'] if q['tile'] in (17,18)]
                if qs:
                    fx=canvas_from_parts(oraw,of['tile_count'],{**cp,'parts':qs});target=np.where(fx,fx,target).astype(np.uint8)
            if not np.array_equal(actual[bi],target):raise ValueError(f'ARC/art differs: {n}/{kind}')
            expected[bi]=target
        if not any(np.any(actual[bi]) for bi in (5,6,7,8)):transparent.append(n)
        for arm_type in (1,2):
            for mask in range(16):
                got=tables[0][actual[0]].copy();want=tables[0][expected[0]].copy()
                for bit,bi in ((8,8),(1,5),(4,7),(2,6)):
                    if mask&bit:
                        colors=tables[2 if bi==7 and arm_type==2 else 1]
                        m=actual[bi]>0;got[m]=colors[actual[bi][m]]
                        m=expected[bi]>0;want[m]=colors[expected[bi][m]]
                if not np.array_equal(got,want):raise ValueError('Combined raster differs')
                checks.append([n,mask,arm_type])
                if arm_type==2 and mask==15:
                    pic=Image.fromarray(got);pictures[n]=pic;pic.save(out/f'full_{n:03}.png')
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    for start in range(0,len(frames),48):
        sheet=Image.new('RGB',(1440,1150),'#253546');draw=ImageDraw.Draw(sheet)
        for i,n in enumerate(frames[start:start+48]):
            im=pictures[n].crop((30,30,130,122)).resize((180,166),Image.Resampling.NEAREST);x=i%8*180;y=i//8*184;sheet.paste(im,(x,y+18),im);draw.text((x+8,y+2),str(n),fill='white')
        draw.text((12,1112),'통합 ARC 재조립 미리보기 · 실제 게임 실행 화면 아님',font=font,fill='white');sheet.save(out/f'all_frames_{start//48}.png')
    selections=[0,29,34,43,55,71,85,89,98,106,120,144,156,162,204,207]
    sheet=Image.new('RGB',(1280,1120),'#253546');draw=ImageDraw.Draw(sheet)
    for i,n in enumerate(selections):
        im=pictures[n].crop((42,44,112,112)).resize((280,272),Image.Resampling.NEAREST);x=i%4*320;y=i//4*280;sheet.paste(im,(x+20,y),im);draw.text((x+4,y+4),str(n),fill='white')
    sheet.save(out/'representative_poses.png')
    report={'source_arc_sha256':sha256(arc),'valid_frames_checked':len(frames),'combinations_checked':len(checks),'all_layers_equal':True,'original_transparent_armor_frames':transparent,'static_only':True,'runtime_verified':False,'checks':checks}
    (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
if __name__=='__main__':main()
