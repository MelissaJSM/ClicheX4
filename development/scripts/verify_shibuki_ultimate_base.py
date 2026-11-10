"""수용 기본형과 새 PL02 전 참조 및 보존 아머를 독립 대조한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D,load
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_ultimate_base import EXCLUDED
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition

def verify(candidate,repro):
    _,arcs=load();old=(D/'pilot01/PL02_U.ARC').read_bytes();base=arcs['parent']['PL00_U.ARC'];new=(candidate/'PL02_U.ARC').read_bytes();rr=json.loads((candidate/'recipe.json').read_text())
    if new!=(repro/'PL02_U.ARC').read_bytes() or sha256(new)!=rr['modified_arc_sha256']:raise ValueError('Reproduction mismatch')
    layout=lambda arc:[(e['index'],e['type'],e['offset'],e['size']) for e in psx_arc(arc)]
    if len(new)!=len(old) or layout(new)!=layout(old):raise ValueError('ARC layout changed')
    for e in psx_arc(old):
        if int(e['type'],16) not in (2,3) and entry(old,int(e['type'],16))!=entry(new,int(e['type'],16)):raise ValueError('Non-target entry changed')
    og,oc=entry(old,2),entry(old,3);g,c=entry(new,2),entry(new,3);bg,bc,bp=(entry(base,k) for k in (2,3,9));pal=entry(new,9)
    if bank_offsets(g,allow_aliases=True)!=bank_offsets(og,allow_aliases=True) or bank_offsets(c)!=bank_offsets(oc):raise ValueError('Bank boundaries changed')
    ob=graphics_bank(og,0,allow_bank_aliases=True);bb=graphics_bank(bg,0,allow_bank_aliases=True);nb=graphics_bank(g,0,allow_bank_aliases=True)
    expected_frames=set(range(237))-EXCLUDED
    if set(rr['frames'])!=expected_frames:raise ValueError('Scope changed')
    checks={'reproducible':True,'base_frames_exact':0,'both_direction_base_comparisons':0,'armor_layers_preserved':0,'decoded_refs':0,'non_base_graphic_refs_preserved':0,'original_invalid_armor_refs_preserved':[],'runtime_verified':False};pics={}
    for n in range(237):
        a,b,f=ob['frames'][n],nb['frames'][n],bb['frames'][n]
        oldraw=decode_stream(og,a['offset'],a['limit'],a['tile_count']*128).data;raw=decode_stream(g,b['offset'],b['limit'],b['tile_count']*128).data
        if a['tile_count']!=b['tile_count']:raise ValueError('Tile count changed')
        if n in expected_frames:
            base_raw=decode_stream(bg,f['offset'],f['limit'],f['tile_count']*128).data
            want=canvas_from_parts(base_raw,f['tile_count'],composition_frame(bc,0,n));got=canvas_from_parts(raw,b['tile_count'],composition_frame(c,0,n))
            for flipped in (False,True):
                if not np.array_equal(want[:,::-1] if flipped else want,got[:,::-1] if flipped else got):raise ValueError('Native base pixels differ')
                checks['both_direction_base_comparisons']+=1
            checks['base_frames_exact']+=1;pics[n]=got
        elif oldraw!=raw:raise ValueError('Excluded bitmap changed')
        for bi in (5,6,7,8):
            before=local_composition(composition_frame(oc,bi,n));after=local_composition(composition_frame(c,bi,n))
            if before!=after:raise ValueError('Armor composition changed')
            try:x=canvas_from_parts(oldraw,a['tile_count'],before)
            except ValueError:
                if oldraw!=raw:raise ValueError('Originally invalid frame changed')
                checks['original_invalid_armor_refs_preserved'].append([n,bi]);continue
            if not np.array_equal(x,canvas_from_parts(raw,b['tile_count'],after)):raise ValueError('Armor pixels changed')
            checks['armor_layers_preserved']+=1
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        a=graphics_bank(og,bi,allow_bank_aliases=True);b=graphics_bank(g,bi,allow_bank_aliases=True)
        for x,y in zip(a['frames'],b['frames']):
            oldraw=decode_stream(og,x['offset'],x['limit'],x['tile_count']*128).data;raw=decode_stream(g,y['offset'],y['limit'],y['tile_count']*128).data
            if bi and (x!=y or oldraw!=raw):raise ValueError('Other graphics bank changed')
            checks['decoded_refs']+=1
            if bi:checks['non_base_graphic_refs_preserved']+=1
    frames=[0,1,9,17,25,33,37,45,57,67,71,77,85,89,97,100,110,120,133,138,143,154,204,207]
    sheet=Image.new('RGB',(960,888),'#253546');draw=ImageDraw.Draw(sheet);words=struct.unpack_from('<16H',pal)
    for i,n in enumerate(frames):
        pic=save_image(pics[n].tobytes(),(160,160),words,candidate/f'base_{n:03}.png').convert('RGBA').crop((32,42,128,116)).resize((160,124),Image.Resampling.NEAREST)
        x=i%6*160;y=i//6*222;sheet.paste(pic,(x,y+34),pic);draw.text((x+7,y+8),f'PL02 base {n}',fill='white')
    sheet.save(candidate/'review.png');checks.update({'passed':True,'archive_sha256':sha256(new),'frame_scope':sorted(expected_frames),'static_preview_only':True})
    (candidate/'regression.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);a=p.parse_args();verify(a.candidate,a.repro)
