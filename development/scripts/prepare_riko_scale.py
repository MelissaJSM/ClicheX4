"""검수한 native 포즈를 공통 머리·목 기준 및 파츠 검사 후 동작 입력으로 발행한다."""
import argparse,json,struct,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json
from scripts.discover_inputs import sha256
from scripts.repack_zero import read_inputs
from scripts.build_riko_idle import patch_frames,validate_motion_scope,check_motion_scale,KNOWN_SABER_EFFECT_FRAMES as SABER_EFFECT_FRAMES,LADDER_BASE_COUNTS
from src.psx_frame_edit import read_indexed_png,frame_coverage
from src.psx_player import graphics_bank,composition_frame,decode_stream

def prepare(extracted,recipe_path):
    recipe_path=recipe_path.resolve()
    if not recipe_path.is_relative_to((ROOT/'work/ver_buki_riko').resolve()):raise ValueError('Unexpected artwork recipe')
    recipe=json.loads(recipe_path.read_text(encoding='utf-8'));validate_motion_scope(recipe)
    profile,_,arc,gmeta,gfx,parts,_=read_inputs(extracted)
    selected=json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    master=ROOT/selected['indexed_png']
    if sha256(master.read_bytes())!=selected['indexed_png_sha256']:raise ValueError('Selected master changed')
    pal=master.with_name('candidate_palette.bin').read_bytes();words=struct.unpack('<16H',pal);reference,size=read_indexed_png(master,words)
    if recipe['source_sha256']!=profile['source_sha256'] or recipe['palette_sha256']!=sha256(pal):raise ValueError('Recipe source/palette mismatch')
    frames={};paths={};bank=graphics_bank(gfx,0)
    for key,r in recipe['frames'].items():
        path=(recipe_path.parent/r['file']).resolve()
        if not path.is_relative_to(recipe_path.parent) or sha256(path.read_bytes())!=r['sha256']:raise ValueError('Native artwork changed or escaped directory')
        n=int(key);paths[n]=path;frames[n]=read_indexed_png(path,words)
        f=bank['frames'][n];comp=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        coverage,frame_size,bounds=frame_coverage(raw,f['tile_count'],comp)
        if frames[n][1]!=frame_size:raise ValueError('Native canvas mismatch')
        pixels=frames[n][0]
        if n in SABER_EFFECT_FRAMES:
            # patch_frames checks original effects or explicitly hash-bound
            # sword additions; an effect does not use the player's head/CLUT.
            continue
        if any(pixel and (not cells or (len(set(cells))!=1 and n!=81 and n not in LADDER_BASE_COUNTS)) for pixel,cells in zip(pixels,coverage)):raise ValueError('Outside/overlapping parts')
        if n in LADDER_BASE_COUNTS:
            # patch_frames validates explicit disjoint base/overlay ownership.
            comp={**comp,'parts':comp['parts'][:LADDER_BASE_COUNTS[n]]}
        for p in comp['parts']:
            if p['flags'] & ~(0x40 if n in LADDER_BASE_COUNTS else 0):raise ValueError('Unmodeled flags')
            if p['tile']%16==0:
                x=p['x']-bounds[0]+(15 if p['flip_x'] else 0);y=p['y']-bounds[1]
                if any(pixels[(y+dy)*frame_size[0]+x] for dy in range(16)):raise ValueError('Reflected U=0 edge')
    scale=check_motion_scale(recipe,frames,gfx,parts,(reference,size))
    _,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal,recipe.get('sword_effect_edits'))
    out=new_run(ROOT,'ver_buki_riko','scale_frames');records={}
    for n,path in sorted(paths.items()):
        name=f'frame_{n:03d}.png';shutil.copyfile(path,out/name);records[str(n)]={'file':name,'sha256':sha256((out/name).read_bytes())}
    write_json(out/'motion_set.json',{**recipe,'frames':records,'recipe':str(recipe_path),'recipe_sha256':sha256(recipe_path.read_bytes()),
        'scale_check':scale,'checks':checks,'runtime_verified':False,'art_review_pending':True})
    print(json.dumps({'output':str(out),'scale_check':scale,'compression_max':max(c['encoded_bytes'] for c in checks['compression'])}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--extract',type=Path,required=True);p.add_argument('--recipe',type=Path,required=True)
    args=p.parse_args();prepare(args.extract,args.recipe)
