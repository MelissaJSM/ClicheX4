"""이동 사격 연결 수정본에 대기 모자 크림색 점 제거를 합친다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scripts.prepare_nana_fourth_run_art import PARENT,PARENT_SHA,LAYERS
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.project import digest
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas,bank_offsets
from src.psx_compress import replace_stream
from src.psx_sprite_batch import canvas_from_parts

IDLE_DOTS=[0,85,86,87,92,119]
FRAMES=sorted([*range(1,33),*IDLE_DOTS])


def finish(prepared,out):
    prepared,out=prepared.resolve(),out.resolve();root=ROOT/'work/ver_rin_nana/nana_fourth_armor'
    require(prepared.is_relative_to(root) and out.is_relative_to(root) and not out.exists(),'Fresh variant work paths required')
    recipe=json.loads((prepared/'recipe.json').read_text('utf8'))
    arc=(prepared/'modified.arc').read_bytes();require(recipe['frames']==list(range(1,33)) and recipe['parent_sha256']==PARENT_SHA and sha256(arc)==recipe['modified_arc_sha256'],'Unexpected movement input')
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);ng=g;expected={};fixes=[]
    for n in IDLE_DOTS:
        f=bank['frames'][n];require([q['index'] for q in bank['frames'] if q['offset']==f['offset']]==[n],'Unexpected shared idle bitmap')
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        comp=composition_frame(c,5,n);require(len(comp['parts'])==1,'Unexpected hat composition');q=comp['parts'][0]
        require(not(q['flags'] or q['page'] or q['clut']),'Unexpected hat flags')
        x,y=86,61 if n==119 else 62;tx,ty=x-80-q['x'],y-80-q['y'];require(0<=tx<16 and 0<=ty<16,'Hat point outside tile')
        atlas,loc,_=indexed_atlas(raw,f['tile_count']);pixel=(q['tile']//16*16+ty)*256+q['tile']%16*16+tx
        require(atlas[pixel]==13,'Cream hat point changed');pos,shift=loc[pixel];changed=bytearray(raw);changed[pos]=(changed[pos]&~(15<<shift))|(2<<shift)
        require(sum(a!=b for a,b in zip(raw,changed))==1,'Unexpected hat texture changes')
        ng,compressed=replace_stream(ng,f,bytes(changed));expected[n]=bytes(changed);fixes.append({'frame':n,'world_canvas':[x,y],'tile':q['tile'],'old_index':13,'new_index':2,'compression':compressed})
    result=bytearray(arc);e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);result[e['offset']:e['offset']+e['size']]=ng
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        ob=graphics_bank(g,bi,allow_bank_aliases=True);nb=graphics_bank(ng,bi,allow_bank_aliases=True)
        for f,nf in zip(ob['frames'],nb['frames']):
            old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            new=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
            require(new==(expected[f['index']] if bi==0 and f['index'] in expected else old),'Unexpected hat fix scope')
    out.mkdir();(out/'modified.arc').write_bytes(result);words=struct.unpack_from('<16H',entry(result,9),32)
    for n in FRAMES:
        f=bank['frames'][n];raw=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data
        base=canvas_from_parts(raw,f['tile_count'],composition_frame(c,0,n));layers={b:canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,n)) for b in LAYERS.values()}
        for mask in range(16):
            merged=base.copy()
            for bit,b in ((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:merged=np.where(layers[b],layers[b],merged)
            save_image(merged.tobytes(),(160,160),words,out/f'frame_{n:03}_mask{mask:02}.png')
        if n in IDLE_DOTS:
            before=np.array(render(arc,n,True)[0]);after=np.array(render(result,n,True)[0]);points=np.argwhere(np.any(before!=after,axis=2))
            require(len(points)==1 and merged[tuple(points[0])]==2,'Idle pose changed beyond cream point')
    recipe.update(frames=FRAMES,modified_arc_sha256=sha256(result),hat_pixel_fixes=fixes,
                  movement_prepared=prepared.relative_to(ROOT).as_posix(),moving_shoulder_fix=True,
                  inherited_idle_pose_preserved_except_six_cream_points=True)
    write(out/'recipe.json',recipe);print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'sha256':sha256(result),'idle_hat_points':len(fixes),'selected_frames':len(FRAMES)}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();finish(a.prepared,a.output)
