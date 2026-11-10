"""정합된 새 기본 포즈를 얼티밋 의상 편집의 입력으로 사용한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
import numpy as np
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write

def source_for(ref):
    if ref==104:return H/'rising104_arm_native02/base_104_indices.png'
    return H/f'rising_fire_native{"01"if ref in(100,101,102)else"02"}/base_{ref:03}_indices.png'

def main():
    out=H/'rising_ultimate_costume01';need(not out.exists(),'Fresh output required');out.mkdir()
    base=Archive((H/'prepared_double_cyclone_base01/PL00_U.ARC').read_bytes())
    ultimate=Archive((H/'prepared_double_cyclone_ultimate01/PL02_U.ARC').read_bytes())
    records=[]
    for number,refs in enumerate(([100,101,102],[103,104,231]),1):
        folder=out/f'page{number:02}';folder.mkdir()
        boards={k:Image.new('RGBA',(1536,1024))for k in('edit_pose','idle_reference','new98_detail')}
        sources=[]
        for col,ref in enumerate(refs):
            path=source_for(ref);idx=np.array(Image.open(path));im=base.rgba(idx,0)
            sources.append({'ref':ref,'native_path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes())})
            for row,mask in enumerate((15,0)):
                for key,render in [('edit_pose',im),('idle_reference',ultimate.composite(0,mask)[0]),('new98_detail',ultimate.composite(98,mask)[0])]:
                    crop=render.crop((128,124,192,188)).resize((512,512),Image.Resampling.NEAREST)
                    boards[key].alpha_composite(crop,(col*512,row*512))
        for key,board in boards.items():board.save(folder/f'{key}.png')
        records.append({'page':number,'refs':refs,'sources':sources,'rows':['ultimate_before','ultimate_after'],
                        'scale':8,'world_crop':[-32,-36,32,28],
                        'note':'같은 신규 기본 자세를 양 의상으로 편집한다. 기존 거친 Ultimate 본체를 덮지 않는다.'})
    write(out/'input.json',{'pages':records,'generation_pending':True,'base_resource_sha256':sha(base.data),
                           'ultimate_resource_sha256':sha(ultimate.data),'game_data_written':False})
if __name__=='__main__':main()
