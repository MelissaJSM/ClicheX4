"""현재 수용 대기를 고정하고 린 동작 재제작용 좌표 시트를 만든다."""
import json, math, shutil, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_idle import entry
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.build_rin_motion import SCOPES,SCOPE_BANKS
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch

OUT=ROOT/'work/ver_rin_nana/style_revision/v1'
PARENT=ROOT/'out/ver_rin_nana/rin_idle_style_20261028T210935993995Z'
MASTER=ROOT/'work/ver_rin_nana/idle_style/v2'
CELL=80;ORIGIN=40;SCALE=4

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((PARENT/'manifest.json').read_text('utf-8'))
    if digest(PARENT/'rin_nana.bin')!='0d47990fdb59a1cffcb1c600ab7464fa420ec41da40d5a6861ca2239e9f16585':raise ValueError('Master BIN differs')
    arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<64H',pal)
    for name in ('preview_147.png','preview_000.png','generated_idle.png','idle_style_recipe.json'):
        target=OUT/('master_'+name)
        if target.exists() and digest(target)!=digest(MASTER/name):raise ValueError('Frozen master differs')
        shutil.copyfile(MASTER/name,target)
    save=Image.open(OUT/'master_preview_147.png').convert('RGBA')
    save.resize((448,384),Image.Resampling.NEAREST).save(OUT/'master_8x.png')
    frozen={'parent':PARENT.relative_to(ROOT).as_posix(),'bin_sha256':manifest['modified_bin']['sha256'],'master_file':'master_preview_147.png','master_sha256':digest(OUT/'master_preview_147.png'),'origin':[24,24],'palette_words':list(words[:16]),'fixed_idle_bank0':[0,1,2,5,6,146,147,148],'fixed_idle_bank1':[0,86],'imagegen_mode':'built_in','runtime_verified':False}
    groups={'run':(0,[*range(7,21),3,4]),'air':(0,[21,22,24,25,26,27,28,29,31,33,34]),'dash':(0,list(range(44,53))),'wall':(0,list(range(35,44))),
            'hurt':(0,[135,139,149,152]),'ground':(0,sorted(SCOPES['ground'])),'air_slash':(0,sorted(SCOPES['air_slash'])),'wall_saber':(1,sorted(SCOPES['wall_saber'])),
            'ladder':(0,sorted(SCOPES['ladder'])),'arrival':(0,list(range(249,254))),'victory':(1,list(range(1,7))),
            'spin':(1,[161]),'ice':(1,[87,134,135,138,140])}
    # Identical indexed bodies and bounds need only one redraw. Derived flashes
    # and rotation variants are rebuilt from the same redrawn body later.
    recipes={}
    for group,(bi,ids) in groups.items():
        cell_size=112 if group=='ice' else CELL
        origin=cell_size//2
        folder=OUT/group;folder.mkdir(exist_ok=True);bank=graphics_bank(g,bi);frames={};unique=[];aliases={};seen={}
        for n in ids:
            f=bank['frames'][n];c=composition_frame(parts,0 if bi==0 else 5,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            pixels,size,bounds,_=compose_launch(raw,f['tile_count'],c)
            key=(pixels,size,bounds)
            if key in seen:aliases[str(n)]=seen[key];continue
            seen[key]=n;unique.append(n)
            p=folder/f'before_{n:03d}.png';pic=save_image(pixels,size,words,p)
            cell=Image.new('RGBA',(cell_size,cell_size));cell.alpha_composite(pic.convert('RGBA'),(origin+bounds[0],origin+bounds[1]))
            if sum(v!=0 for v in pixels)!=np.count_nonzero(np.array(cell.getchannel('A'))):raise ValueError(f'Guide clips {group}/{n}')
            frames[str(n)]={'bounds':bounds,'size':size,'before':p.name,'sha256':digest(p)}
        sheets=[]
        for first in range(0,len(unique),16):
            ns=unique[first:first+16];rows=math.ceil(len(ns)/4);sheet=Image.new('RGBA',(cell_size*4,cell_size*rows))
            for i,n in enumerate(ns):
                rec=frames[str(n)];pic=Image.open(folder/rec['before']).convert('RGBA')
                sheet.alpha_composite(pic,(i%4*cell_size+origin+rec['bounds'][0],i//4*cell_size+origin+rec['bounds'][1]))
            name=f'guide_{first//16}.png';sheet.resize((sheet.width*SCALE,sheet.height*SCALE),Image.Resampling.NEAREST).save(folder/name)
            sheets.append({'file':name,'frames':ns,'columns':4,'rows':rows,'cell':cell_size,'origin':origin})
        record={'group':group,'graphics_bank':bi,'parts_bank':0 if bi==0 else 5,'parent':frozen['parent'],'parent_sha256':frozen['bin_sha256'],'frames':frames,'aliases':aliases,'sheets':sheets}
        (folder/'guide.json').write_text(json.dumps(record,indent=2)+'\n','utf-8');recipes[group]=record
    frozen['groups']={k:{'unique':len(v['frames']),'aliases':v['aliases'],'sheets':len(v['sheets'])} for k,v in recipes.items()}
    (OUT/'master.json').write_text(json.dumps(frozen,indent=2)+'\n','utf-8')
    print(json.dumps(frozen['groups']))

if __name__=='__main__':main()
