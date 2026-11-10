"""기존9스트림의 역순열 증거와 새40층을 결합한 메모리 내 저장계획. ARC 미출력."""
from pathlib import Path
import sys,json,struct
import argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from repack_part_records_lossless import repack
from pack_shibuki_hurt import raw,repack_fixed_global
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,decode_stream,indexed_atlas
from scripts.optimize_rin_style_tiles import permute
PBS=(0,5,6,7,8)
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='standing_fire_storage_plan02');z=ap.parse_args();d=H/z.output;need(not d.exists(),'새 폴더 필요');d.mkdir();parent=H/'prepared_standing_special_base01/PL00_U.ARC';a=Archive(parent.read_bytes())
    cq=H/'standing_fire_compact01/report.json';eq=H/'standing_fire_existing_tileorder01/report.json';new=json.loads(cq.read_text('utf8'));existing=json.loads(eq.read_text('utf8'))
    rawchanges={};counts={};changes={b:{}for b in PBS}
    for group in new['groups']:
        nr=bytes.fromhex(group['raw'])
        for n in group['refs']:
            rawchanges[n]=nr;counts[n]=group['count']
            for b in PBS:changes[b][n]=b''.join(struct.pack('<BBbb',*p)for p in group['parts'][str(b)][str(n)])or struct.pack('<BBbb',0,0,-8,-8)
    chosen=[];remaining=1074
    for group in sorted((v for v in existing['groups']if len(v['refs'])==2),key=lambda v:(-v['optimization']['saved'],v['refs'][0])):
        if remaining<=0:break
        chosen.append(group);remaining-=group['optimization']['saved'];ns=group['refs'];nr=(eq.parent/f'{ns[0]:03}_trial_raw.bin').read_bytes();mp={int(k):v for k,v in group['mapping'].items()}
        need(sha(nr)==group['optimized_raw_sha256']and permute(nr,32,[mp[t]for t in range(32)])==raw(a,0,ns[0]),'입력 순열 불일치')
        for n in ns:
            rawchanges[n]=nr;counts[n]=32
            for b in PBS:
                cp=composition_frame(a.c,b,n);changes[b][n]=b''.join(struct.pack('<BBbb',p['flags'],mp[p['tile']],p['x'],p['y'])for p in cp['parts'])
    part_report={};nc=a.c
    for b,cr in changes.items():
        try:
            try:nc,slack=repack_parts(nc,b,cr);mode='existing'
            except ValueError:nc,slack,mode=repack(nc,b,cr)
            part_report[str(b)]={'fits':True,'slack':slack,'method':mode}
        except Exception as ex:part_report[str(b)]={'fits':False,'error':str(ex)}
    tail=[]
    for gb,bank in enumerate(a.banks):
        end=max([bank['base']+len(bank['frames'])*4]+[decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).end for f in bank['frames']]);aligned=(end+3)&~3
        tail.append({'bank':gb,'start':bank['base'],'end':bank['end'],'max_decoder_end':end,'aligned_end':aligned,'unconsumed_tail':bank['end']-aligned,'nonzero_tail_bytes':sum(v!=0 for v in a.g[aligned:bank['end']]),'dynamic_access_proof_here':False})
    r={'parent':ev(parent),'new_layout':ev(cq),'existing_permutation_probe':ev(eq),'new_art_refs':list(range(85,93)),'permutation_only_refs':sorted(n for g in chosen for n in g['refs']),'permutation_groups':[{'refs':g['refs'],'saved':g['optimization']['saved'],'fixed_tiles':g['optimization']['fixed_tiles']}for g in chosen],'permutation_total_saved':sum(g['optimization']['saved']for g in chosen),'parts':part_report,'bank_tail_inventory':tail,'arc_written':False,'bank_directory_changed':False,'art_changed':False,'raw_policy_change':'지정18참조의raw/parts tile번호만 새순열로 변경, 역순열로256nibble 전체동일. 현재원화그림 변경은85..92만. 이 계획은 후보ARC 적용 전 읽기 검토용.'}
    try:
        ng,graphics=repack_fixed_global(a,rawchanges,counts);r['graphics']=graphics
        need(all(p['fits']for p in part_report.values()),'조립은행 초과')
        candidate=replace_entry(replace_entry(a.data,2,ng),3,nc);out=Archive(candidate);newrefs=set(range(85,93));raw_checked=0;layer_checked=0;parts_checked=0;gpu=0
        for gb,bank in enumerate(a.banks):
            for f in bank['frames']:
                n=f['index'];expect=rawchanges[n]if gb==0 and n in rawchanges else raw(a,gb,n);need(raw(out,gb,n)==expect,'raw 불일치');raw_checked+=1
        for b in PBS:
            for n in range(237):
                if n in {105,*range(175,183)}:continue
                expected=np.array(Image.open(H/f'standing_fire_targets_probe01/{n:03}_bank{b}_indices.png'))if n in newrefs else a.layer(n,b)[0]
                need(np.array_equal(out.layer(n,b)[0],expected),'층 표시 불일치');layer_checked+=1
                if n not in changes[b]:need(records(a.c,b,n)==records(out.c,b,n),'비대상 기록 변경');parts_checked+=1
                if n in changes[b]:
                    count=out.banks[0]['frames'][n]['tile_count'];at=np.frombuffer(indexed_atlas(raw(out,0,n),count)[0],np.uint8).reshape(-1,256)
                    for p in composition_frame(out.c,b,n)['parts']:
                        t=p['tile'];tile=at[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                        need(t<count,'타일 정원');need(t%16!=0 or not tile[:,0].any(),'GPU U경계');need(not p['flip_y']or not tile[0].any(),'GPU V경계');gpu+=1
        r.update(memory_candidate_passed=True,memory_candidate_sha256=sha(candidate),raw_checks=raw_checked,layer_checks=layer_checked,unchanged_part_checks=parts_checked,gpu_parts=gpu,limitations=['원MIPS/실제큐/전체부분16RGBA·UI사본 독립검사 미수행','ARC는 메모리에서만 조립, 파일/게임/원본/포인터 미변경'])
    except Exception as ex:r.update(memory_candidate_passed=False,error=str(ex))
    write(d/'report.json',r);print(json.dumps({k:r.get(k)for k in('permutation_only_refs','permutation_total_saved','parts','graphics','memory_candidate_passed','error','memory_candidate_sha256','raw_checks','layer_checks','gpu_parts')}))
if __name__=='__main__':main()
