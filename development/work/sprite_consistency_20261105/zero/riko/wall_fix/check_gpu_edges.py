"""모든 공유 참조의 native GPU U/V 경계에 새 불투명 픽셀이 생겼는지 검사한다."""
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.export_zero_consistency import write,sha
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas

D=Path(__file__).resolve().parent
old=(D.parent/'PL01_U.ARC').read_bytes();new=(D/'prepared_v1/PL01_U.ARC').read_bytes()
assert sha(old)=='d5720842fa16d9eed2b53c77c159656be444023943f8400d11cec4551876d17d'
assert sha(new)=='36e231a882be87d71d603667a26909025003b88908f939f115d328b0dd4d53dc'
og,ng=entry(old,2),entry(new,2);oc,nc=entry(old,3),entry(new,3)
assert oc==nc
records=[];violations=[];parts=0;refs=0;partial=[]
for b in (0,1):
    ob,nb=graphics_bank(og,b),graphics_bank(ng,b)
    for of,nf in zip(ob['frames'],nb['frames']):
        n=of['index'];refs+=1
        oraw=decode_stream(og,of['offset'],of['limit'],of['tile_count']*128).data
        nraw=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
        if b==1 and 42<=n<=49:
            assert oraw==nraw;partial.append(n);continue
        oa=np.frombuffer(indexed_atlas(oraw,of['tile_count'])[0],np.uint8).reshape(-1,256)
        na=np.frombuffer(indexed_atlas(nraw,nf['tile_count'])[0],np.uint8).reshape(-1,256)
        for p in composition_frame(nc,0 if b==0 else 5,n)['parts']:
            parts+=1;t=p['tile'];tx=t%16*16;ty=t//16*16
            op=oa[ty:ty+16,tx:tx+16];npix=na[ty:ty+16,tx:tx+16]
            for edge,oldedge,newedge in ([('u_first_column',op[:,0],npix[:,0])] if t%16==0 else [])+([('flipped_v_first_row',op[0],npix[0])] if p['flip_y'] and t//16%16==0 else []):
                added=np.flatnonzero((newedge>0)&(oldedge==0)).tolist()
                changed=np.flatnonzero(newedge!=oldedge).tolist()
                row={'bank':b,'frame':n,'part':p['index'],'tile':t,'x':p['x'],'y':p['y'],
                     'flip_x':p['flip_x'],'flip_y':p['flip_y'],'edge':edge,
                     'old_opaque':int(np.count_nonzero(oldedge)),'new_opaque':int(np.count_nonzero(newedge)),
                     'new_intrusions':added,'changed_edge_positions':changed}
                records.append(row)
                if added:violations.append(row)
report={'passed':not violations,'source_arc_sha256':sha(old),'candidate_arc_sha256':sha(new),
        'refs':refs,'parts':parts,'edge_checks':len(records),'violations':violations,
        'partial_raw_preserved':partial,'records':records,
        'basis':'build_nana_ultimate_run.validate: tile%16==0 first column; flip_y and tile//16%16==0 first row. 기존과 비교해 새 침범을 거부.',
        'runtime_verified':False}
write(D/'gpu_edges.json',report)
print({'passed':report['passed'],'edge_checks':len(records),'violations':len(violations),
       'changed_edges':sum(bool(x['changed_edge_positions'])for x in records)})
if violations:raise SystemExit(1)
