"""기존 새 공중/벽/대시의 texel을 보존한 순열 절감량만 조사한다. ARC 미출력."""
from pathlib import Path
import sys,json,copy,struct,argparse
H=Path(__file__).resolve().parent.parent/'shibuki_audit';ROOT=H.parents[2];sys.path[:0]=[str(ROOT),str(H)]
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame,decode_stream,compose_indices
from scripts.optimize_rin_style_tiles import permute
from optimize_hurt_tile_storage import optimize
PBS=(0,5,6,7,8)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='hover_existing_tileorder01');ap.add_argument('--steps',type=int,default=4);z=ap.parse_args();d=H/z.output;need(not d.exists(),'새 폴더 필요');d.mkdir()
    a=Archive((H/'prepared_nova_strike_base01/PL00_U.ARC').read_bytes());allcp={(b,n):composition_frame(a.c,b,n)for b in PBS for n in range(237)};owners={}
    need(sha(a.data)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e','Parent SHA')
    for (b,n),cp in allcp.items():
        for p in cp['parts']:owners.setdefault(p['record_offset'],set()).add((b,n))
    groups={}
    for f in a.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f)
    rows=[]
    for off,fs in groups.items():
        ns=[f['index']for f in fs]
        if not set(ns)<=set(range(33,85)):continue
        f=fs[0]
        if f['tile_count']!=32:continue
        dec=decode_stream(a.g,off,f['limit'],4096);raw=dec.data;fixed={0,16};reasons=[]
        for b in PBS:
            for n in ns:
                for p in allcp[b,n]['parts']:
                    outside=sorted((bb,nn)for bb,nn in owners[p['record_offset']]if nn not in ns)
                    if outside or p['clut']!=0:
                        fixed.add(p['tile']);reasons.append({'tile':p['tile'],'record_offset':p['record_offset'],'outside_owners':outside,'clut':p['clut']})
        if 73 in ns or 74 in ns:fixed.add(6)
        nr,mp,proof=optimize(raw,fixed,z.steps);inverse=[mp[t]for t in range(32)];need(permute(nr,32,inverse)==raw,'역순열 원raw 불일치');checked=0
        for n in ns:
            for b in PBS:
                cp=allcp[b,n];new=copy.deepcopy(cp)
                for p in new['parts']:p['tile']=mp[p['tile']]
                need(compose_indices(raw,32,cp)[:3]==compose_indices(nr,32,new)[:3],'기존층 표시 불일치');checked+=1
        row={'refs':ns,'original_offset':off,'source_raw_sha256':sha(raw),'optimized_raw_sha256':sha(nr),'optimization':proof,'mapping':mp,'pinned_due_to_shared_records_or_effect':reasons,'inverse_raw_exact':True,'layers_exact':checked,'candidate_applied':False};rows.append(row)
        (d/f'{ns[0]:03}_trial_raw.bin').write_bytes(nr);write(d/'report.json',{'parent_sha256':sha(a.data),'groups':rows,'saving':sum(r['optimization']['saved']for r in rows),'arc_written':False,'scope':'읽기 용량조사만. 모든256nibble 역순열 동일, 실제 gfx0의5층 조립 비교. 다른 UI 사본·전체실기·후보 새 directory 검증은 미수행.'});print(json.dumps({'refs':ns,'saved':proof['saved'],'total':sum(r['optimization']['saved']for r in rows),'fixed':len(fixed)}),flush=True)
if __name__=='__main__':main()
