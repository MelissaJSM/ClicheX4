"""모든 후보 조립의 최종 표시 provenance 합집합에 없는 texel 절감량 조사만."""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,write,need
from scripts.export_x_consistency import Archive
from src.psx_player import bank_offsets,composition_frame,compose_indices,decode_stream
from src.psx_compress import encode_stream
from src.psx_ui_atlas import local_composition
def main():
    a=Archive((H/'prepared_dash_base01/PL00_U.ARC').read_bytes());q=json.loads((H/'base_run_complete_pack05/progress.json').read_text('utf8'));selected={int(n):bytes.fromhex(r)for n,r in q['raws'].items()};groups={}
    for f in a.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f)
    counts={b:composition_frame(a.c,b,0)['bank_frame_count']for b in range(len(bank_offsets(a.c)))};profiles={};codes={}
    def encoded(raw):
        key=sha(raw)
        if key not in codes:codes[key]=encode_stream(raw)
        return codes[key]
    for name,banks in [('main_visible',[0,5,6,7,8]),('all_same_frame_visible',list(counts))]:
        rows=[];dedup={};fullbefore=fullafter=0
        for off,fs in groups.items():
            f=fs[0];raw=decode_stream(a.g,off,f['limit'],f['tile_count']*128).data;visible=set();renders=[];invalid=[]
            for ff in fs:
                n=ff['index']
                for b in banks:
                    if n>=counts[b]:continue
                    cp=composition_frame(a.c,b,n);cp=local_composition(cp)if b in(5,6,7,8)else cp
                    try:pix,size,box,prov=compose_indices(raw,f['tile_count'],cp,allowed_cluts={0,1,2,3})
                    except ValueError as ex:invalid.append({'bank':b,'ref':n,'reason':str(ex)});continue
                    visible.update((p['byte'],p['shift'])for p in prov if p is not None);renders.append((b,n,cp,pix,size,box))
            nr=bytearray(raw);removed=[]
            # If an unhandled composition exists, do not assume it has no use.
            if not invalid:
                for pos,value in enumerate(raw):
                    for shift in(0,4):
                        idx=(value>>shift)&15
                        if idx and(pos,shift)not in visible:removed.append([pos,shift,idx]);nr[pos]&=~(15<<shift)
            nr=bytes(nr)
            for b,n,cp,pix,size,box in renders:need(compose_indices(nr,f['tile_count'],cp,allowed_cluts={0,1,2,3})[:3]==(pix,size,box),'Visible pixels changed')
            target=f['index']in selected;origchosen=selected[f['index']]if target else raw;chosen=selected[f['index']]if target else nr
            before=len(encoded(origchosen));after=len(encoded(chosen));fullbefore+=before;fullafter+=after;dedup.setdefault((sha(chosen),len(chosen)),after)
            if removed or invalid:rows.append({'refs':[v['index']for v in fs],'target':target,'changed_raw_sha256':sha(nr),'source_raw_sha256':sha(raw),'removed_nonzero_texels':len(removed),'removed_positions':removed,'actual_budget_saving':0 if target else before-after,'all_trial_layer_renders_exact':True,'layer_renders':len(renders),'invalid_compositions_causing_preservation':invalid})
        bank=a.banks[0];capacity=bank['end']-bank['base']-len(bank['frames'])*4;profiles[name]={'rows':rows,'before_bytes':fullbefore,'after_bytes':fullafter,'saved':fullbefore-fullafter,'deduplicated_bytes':sum(dedup.values()),'remaining_slack_with_dedup':capacity-sum(dedup.values())}
    write(H/'base_run_hidden_texel_probe.json',{'source_sha256':sha(a.data),'profiles':profiles,'analysis_only':True,'resource_written':False,'all_native_consumers_verified':False,'safety_limitations':['동일 frame 번호의 조립은행만 가정. 원코드 전체 소비·부분업로드 후 잔존·직접GPU 읽기 미확정.','부분 아머는 각 개별층 자체의 표시를 보존했으므로 알려진 레이어 조합에도 동일.','수용대기/등장도 해당 raw 변경은 실제적용 전에 별도 허용범위 확정 필요.']})
    print(json.dumps({n:{k:v for k,v in p.items()if k!='rows'}for n,p in profiles.items()}))
if __name__=='__main__':main()
