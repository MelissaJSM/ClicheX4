import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream,indexed_atlas

reports=[]
for mode in ('ver_buki_riko','ver_rin_nana'):
    pointer=json.loads((ROOT/'projects'/mode/'current_build.json').read_text(encoding='utf-8'))
    arcs,_=read_disc((ROOT/pointer['cue']).with_suffix('.bin'),['PL00_U.ARC','PL02_U.ARC'])
    for name,arc in arcs.items():
        g=entry(arc,2);bank=graphics_bank(g,0,allow_bank_aliases=True)
        blocks={}
        for f in bank['frames']:
            packed=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            key=(f['tile_count'],packed)
            if key not in blocks:
                atlas,mapping,h=indexed_atlas(packed,f['tile_count'])
                blocks[key]=(np.frombuffer(atlas,dtype=np.uint8).reshape(h,256),np.array([m is not None for m in mapping]).reshape(h,256))
        pixels=np.zeros((8176,256),dtype=np.uint8);owned=np.zeros_like(pixels,dtype=bool)
        used=0;positions={}
        for key,(data,mask) in sorted(blocks.items(),key=lambda kv:(-kv[0][0],kv[0][1])):
            h=data.shape[0];choice=None
            for y in range(0,used+1,16):
                if y+h>len(pixels):continue
                overlap=owned[y:y+h]&mask
                if np.any(overlap&(pixels[y:y+h]!=data)):continue
                score=(max(used,y+h),int(np.count_nonzero(mask&~owned[y:y+h])),y)
                if choice is None or score<choice[0]:choice=(score,y)
            if choice is None:raise ValueError('No texture placement')
            y=choice[1];pixels[y:y+h][mask]=data[mask];owned[y:y+h]|=mask
            positions[key]=y;used=max(used,y+h)
        for key,(data,mask) in blocks.items():
            y=positions[key];assert np.array_equal(pixels[y:y+len(data)][mask],data[mask])
        report={'mode':mode,'arc':name,'refs':len(bank['frames']),'unique':len(blocks),'packed_rows':used,'loaded_pixels_equal':True}
        reports.append(report);print(report)
(ROOT/'work/steam_port_20261109/x_packing_plan.json').write_text(json.dumps(reports,indent=2)+'\n')
