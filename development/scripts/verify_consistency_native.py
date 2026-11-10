"""Run changed compressed references through the original MIPS decoder offline."""
import argparse, json, struct, sys, hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc, require
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import digest
from scripts.overhaul_nana_buffer_watch import cpu_checks
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame,indexed_atlas

def sha(b):return hashlib.sha256(b).hexdigest()

def verify(plan_path):
    plan=json.loads(plan_path.read_text('utf8'));source=ROOT/plan['source_bin']
    require(digest(source)==plan['source_sha256'],'Unsupported source')
    names=[n for n in plan['resources'] if n.startswith('PL')]
    old,_=read_disc(source,tuple(names)+('SLUS_005.61',));exe=old['SLUS_005.61'];report={}
    for name in names:
        q=plan['resources'][name];data=(ROOT/q['path']).read_bytes()
        require(sha(old[name])==q['before'] and sha(data)==q['after'],'Resource hash mismatch')
        g,c=entry(data,2),entry(data,3);og,oc=entry(old[name],2),entry(old[name],3)
        records=[];edge_checks=0;preserved_edges=[]
        for gb in range(len(bank_offsets(g,allow_aliases=True))):
            bank=graphics_bank(g,gb,allow_bank_aliases=True);ob=graphics_bank(og,gb,allow_bank_aliases=True)
            changed={};raws={}
            for f in bank['frames']:
                n=f['index'];of=ob['frames'][n]
                raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
                before=decode_stream(og,of['offset'],of['limit'],of['tile_count']*128).data
                # Main references with unchanged compressed data can still
                # change native composition pointers, such as final arrival142.
                pbs=([0,5,6,7,8] if name!='PL01_U.ARC' and gb==0 else [gb*5] if name=='PL01_U.ARC' and gb in (0,1) else [])
                semantic=lambda comp:[(p['flags'],p['tile'],p['x'],p['y']) for p in comp['parts']]
                composition_changed=any(semantic(composition_frame(c,b,n))!=semantic(composition_frame(oc,b,n)) for b in pbs)
                if raw==before and not composition_changed:continue
                require(f['tile_count']<=32,'Native decode buffer exceeded')
                changed[n]=(f,raw);raws[n]=(raw,before,f['tile_count'],of['tile_count'],pbs)
            if not changed:continue
            native=cpu_checks(exe,{2:g},bank,changed,targets=list(changed))
            for n,(raw,before,count,oldcount,pbs) in raws.items():
                a=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256)
                oa=np.frombuffer(indexed_atlas(before,oldcount)[0],np.uint8).reshape(-1,256)
                for pb in pbs:
                    original=composition_frame(oc,pb,n)['parts']
                    for part in composition_frame(c,pb,n)['parts']:
                        t=part['tile'];y,x=t//16*16,t%16*16
                        require(y+16<=a.shape[0],'Partial reference unexpectedly modified')
                        patch=a[y:y+16,x:x+16];flags=(part['flags'],part['tile'],part['x'],part['y'])
                        for axis,new_edge in [('U',patch[:,0] if t%16==0 else []),('V',patch[0] if part['flip_y'] and t//16%16==0 else [])]:
                            if not np.any(new_edge):continue
                            same=any((p['flags'],p['tile'],p['x'],p['y'])==flags for p in original)
                            previous=oa[y:y+16,x:x+16]
                            prior_edge=previous[:,0] if axis=='U' else previous[0]
                            require(same and np.array_equal(new_edge,prior_edge),f'New GPU {axis} edge {name}/{gb}/{n}/{pb}/{t}')
                            preserved_edges.append({'bank':gb,'ref':n,'parts_bank':pb,'tile':t,'axis':axis,'original_edge_exact':True})
                        edge_checks+=1
            records.append({'bank':gb,'changed_refs':list(changed),'native_decoder_checks':native})
        report[name]={'candidate_sha256':sha(data),'banks':records,'GPU_part_edge_checks':edge_checks,'original_edges_preserved':preserved_edges}
    result={'passed':True,'plan':str(plan_path),'resources':report,'game_executable_sha256':sha(exe),
      'real_game_code_executed_in_isolated_MIPS':True,'gameplay_runtime_verified':False,
      'emulator_process_touched':False,'save_data_written':False}
    dest=plan_path.with_name(plan_path.stem+'_native_checks.json');dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'passed':True,'report':str(dest),'resources':list(report)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);a=p.parse_args();verify(a.plan)
