"""Read-only future capacity probe; do not alter the frozen29 native candidate."""
from pathlib import Path
import sys,json,importlib.util
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;O=D/'rin_extension'
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_compress import encode_stream
spec=importlib.util.spec_from_file_location('texels',D/'riko_restore/pack_rear_head.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=(O/'prepared_run_v1/PL01_U.ARC').read_bytes();final=(O/'prepared_air_continuation_v1/PL01_U.ARC').read_bytes();g=entry(source,2);ng=entry(final,2);c=entry(final,3);bank=graphics_bank(g,0);nb=graphics_bank(ng,0);rows=[]
for group in [(22,23),(39,40)]:
    f=bank['frames'][group[0]];assert all(bank['frames'][n]['offset']==f['offset']for n in group)
    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;edits=[]
    before_bytes=0
    for n in group:
        cp=composition_frame(c,0,n);_,size,bb,_=compose_indices(raw,f['tile_count'],cp);want=render(final,0,0,n)[0][160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]];edits.append((cp,want.tobytes(),size));q=nb['frames'][n];dd=decode_stream(ng,q['offset'],q['limit'],q['tile_count']*128);before_bytes+=dd.end-q['offset']
    try:
        joint=m.edit_visible_set(raw,f['tile_count'],edits);newbytes=len(encode_stream(joint));rows.append({'refs':group,'fits_current_windows':True,'split_encoded_bytes':before_bytes,'joint_encoded_bytes':newbytes,'potential_saved_bytes':before_bytes-newbytes})
    except ValueError as exc:rows.append({'refs':group,'fits_current_windows':False,'reason':str(exc),'split_encoded_bytes':before_bytes})
(O/'shared_capacity_probe.json').write_text(json.dumps({'scope':'읽기 전용 시험이며 작업 ARC도 변경하지 않음','current_bank0_slack':4058,'groups':rows},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(rows))
