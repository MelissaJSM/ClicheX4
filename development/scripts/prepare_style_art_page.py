"""현재 몸체를 고정 원점으로 나란히 배치한 참조 시트. 새 그림/필터 보정 없음."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_sprite_style_unification import WORK,SOURCES,write


def main():
    p=argparse.ArgumentParser();p.add_argument('--character',choices=('shibuki','nana'),required=True)
    p.add_argument('--form',choices=('base','fourth','ultimate_before','ultimate_after'),required=True)
    p.add_argument('--name',required=True);p.add_argument('--refs',type=int,nargs='+',required=True);p.add_argument('--columns',type=int,choices=(2,4),default=4);a=p.parse_args()
    assert a.name.replace('_','').isalnum() and 1<=len(a.refs)<=16 and all(0<=n<237 for n in a.refs)
    dest=WORK/a.character/a.name;assert not dest.exists();dest.mkdir(parents=True)
    mode='ver_buki_riko'if a.character=='shibuki'else'ver_rin_nana';stem,expected=SOURCES[mode]
    source=ROOT/f'out/{mode}/sprite_reaudit_20261106_v1/{stem}.bin'
    from src.psx_disc import file_hash
    assert file_hash(source)==expected
    arcname='PL02_U.ARC' if a.form.startswith('ultimate') else 'PL00_U.ARC'
    arc=Archive(read_disc(source,(arcname,))[0][arcname]);mask=15 if a.form in('fourth','ultimate_before')else 0
    box=(112,128,208,192);cols=a.columns;rows=(len(a.refs)+cols-1)//cols;cw,ch=576,384
    sheet=Image.new('RGBA',(cw*cols,ch*rows));records=[]
    idle=arc.composite(0,mask,2)[0];idle.save(dest/'idle_native.png')
    idle.crop((128,128,192,192)).resize((768,768),Image.Resampling.NEAREST).save(dest/'idle_reference.png')
    for i,n in enumerate(a.refs):
        actual_mask=15 if a.form=='ultimate_after' and 217<=n<=230 else mask
        pose=arc.composite(n,actual_mask,2)[0];bb=pose.getchannel('A').getbbox()
        assert bb and bb[0]>=box[0]and bb[1]>=box[1]and bb[2]<=box[2]and bb[3]<=box[3],(n,bb)
        pose.save(dest/f'current_{n:03}.png')
        sheet.alpha_composite(pose.crop(box).resize((cw,ch),Image.Resampling.NEAREST),(i%cols*cw,i//cols*ch))
        records.append({'ref':n,'cell':[i%cols,i//cols],'bounds':bb})
    sheet.save(dest/'targets.png')
    write(dest/'inputs.json',{'source_bin':source.relative_to(ROOT).as_posix(),'source_sha256':expected,'archive':arcname,
                              'character':a.character,'form':a.form,'mask':mask,'palette_row':16 if mask else 0,
                              'crop':list(box),'columns':cols,'rows':rows,'cell_pixels':[cw,ch],'native_cell':[96,64],
                              'refs':a.refs,'frames':records,'generated_ready':False})
    print(json.dumps({'page':str(dest),'size':sheet.size,'refs':a.refs}))


if __name__=='__main__':main()
