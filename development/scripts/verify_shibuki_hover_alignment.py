"""호버 수정 ARC를 재조립하여 대상 밖 표시 보존과64개 유효 장착 조합을 검사한다."""
import argparse,json,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,write_json
from scripts.analyze_shibuki_armor import entries
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_hover_alignment import FRAMES,PARENT,PARENT_ARC
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args();build=a.build.resolve()
    if not build.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Isolated output required')
    m=json.loads((build/'manifest.json').read_text(encoding='utf-8'));r=json.loads((build/'recipe.json').read_text(encoding='utf-8'))
    if r['scope']!='fourth_armor_hover_alignment_4' or digest(build/'modified.arc')!=m['modified_archive_sha256'] or digest(ROOT/PARENT/'modified.arc')!=PARENT_ARC:raise ValueError('Wrong hover build')
    art=ROOT/r['source_art'];out=build/'hover_review';out.mkdir(exist_ok=False)
    es=[entries((q/'modified.arc').read_bytes()) for q in [ROOT/PARENT,build]];banks=[graphics_bank(e[2],0,allow_bank_aliases=True) for e in es];kept=0;checks=[];pictures={}
    def composite(layers,mask,arm):
        rgba=Image.new('RGBA',(160,160))
        for bit,bi in [(0,0),(8,8),(1,5),(4,7),(2,6)]:
            if bit and not mask&bit:continue
            row=0 if bi==0 else 2 if bi==7 and arm==2 else 1
            words=struct.unpack_from('<16H',es[1][9],row*32)
            rgba.alpha_composite(save_image(layers[bi].tobytes(),(160,160),words,out/'scratch.png').convert('RGBA'))
        return rgba
    for n in sorted(set(range(237))-{105,*range(175,183)}):
        sides=[]
        for e,bank in zip(es,banks):
            f=bank['frames'][n];raw=decode_stream(e[2],f['offset'],f['limit'],f['tile_count']*128).data
            sides.append({bi:canvas_from_parts(raw,f['tile_count'],composition_frame(e[3],bi,n)) for bi in [0,5,6,7,8]})
        before,after=sides
        if n not in FRAMES:
            if any(not np.array_equal(before[bi],after[bi]) for bi in before):raise ValueError('Unselected visible raster changed')
            kept+=1;continue
        expected={bi:np.array(Image.open(art/f'bank{bi}_{n:03}.png')) for bi in after}
        if any(not np.array_equal(expected[bi],after[bi]) for bi in after):raise ValueError('Art readback mismatch')
        for arm in [1,2]:
            for mask in range(8,16):
                got=composite(after,mask,arm);want=composite(expected,mask,arm)
                if got.tobytes()!=want.tobytes():raise ValueError('Combined hover differs')
                checks.append([n,mask,arm])
        for j,layers in enumerate([before,after]):
            im=composite(layers,15,2);pictures[j,n]=im;im.save(out/f'{"before" if j==0 else "after"}_{n:03}.png')
    sheet=Image.new('RGB',(1024,620),'#253546');d=ImageDraw.Draw(sheet)
    for j in [0,1]:
        for i,n in enumerate(FRAMES):
            im=pictures[j,n].crop((48,48,112,112)).resize((256,256),Image.Resampling.NEAREST);sheet.paste(im,(i*256,j*310+35),im);d.text((i*256+6,j*310+6),f'{n}: '+('before' if j==0 else 'after'),fill='white')
    sheet.save(out/'before_after.png')
    write_json(out/'verification.json',{'bin_sha256':m['modified_bin']['sha256'],'arc_sha256':m['modified_archive_sha256'],'unchanged_valid_frame_rasters':kept,'new_frames':FRAMES,'new_layer_rasters_exact':20,'valid_armor_combinations_checked':len(checks),'checks':checks,'mask_without_leg_armor_not_gameplay_reachable':True,'static_only':True})
    print(json.dumps({'output':str(out),'unchanged_frames':kept,'combinations':len(checks)}))
if __name__=='__main__':main()
