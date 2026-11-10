"""벽 동결부모에서 대시20+노바머리3 최종 자원을 독립 재추출해 검사한다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
import pack_native as producer
from scripts.export_x_consistency import DRAW_ORDER
from scripts.discover_inputs import psx_arc
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import composition_frame,bank_offsets,indexed_atlas
FINAL='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
NOVA=(217,218,220)
def composed(a,layers,mask,arm):
    out=np.asarray(a.rgba(layers[0])).copy()
    for bit,pb in DRAW_ORDER:
        if mask&bit:
            part=np.asarray(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16))
            visible=part[:,:,3]>0;out[visible]=part[visible]
    return out
def main():
    out=D/'packed_dash_nova_diagnostic_v3';td=D/'joint_native_targets_v1';nd=D/'nova_head_registered_v1'
    a=Archive((D.parent/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC').read_bytes());b=Archive((out/'PL02_U.ARC').read_bytes())
    need(sha(a.data)==producer.BEFORE and sha(b.data)==FINAL,'Bound source and output')
    meta=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in producer.REFS for pb in producer.PBS};producer.validate_targets(targets,meta)
    nm=json.loads((nd/'registration.json').read_text('utf8'))
    for n in NOVA:
        q=next(q for q in nm['frames']if q['ref']==n);t=np.array(Image.open(nd/f'target_{n:03}.png'));need(sha(t.tobytes())==q['target_index_sha256'],'Nova target source');targets[n,0]=t
    selected_refs=set(producer.REFS)|set(NOVA);fire=json.loads((D/'fire_constraints_v2/manifest.json').read_text('utf8'));windows={q['ref']:q['window_world']for q in fire['frames']}
    images=selected=nonselected=muzzles=layers=nonlayers=0;frame_records=[]
    for n in range(237):
        if n in PLACEHOLDERS:continue
        old={pb:a.layer(n,pb)[0]for pb in producer.PBS};new={pb:b.layer(n,pb)[0]for pb in producer.PBS};expected={pb:targets.get((n,pb),old[pb])for pb in producer.PBS}
        for pb in producer.PBS:need(np.array_equal(new[pb],expected[pb]),f'Layer {n}/{pb}');layers+=1;nonlayers+=(n,pb)not in targets
        for arm in(1,2):
            for mask in range(16):
                actual=np.asarray(b.composite(n,mask,arm)[0]);want=composed(a,expected,mask,arm);need(np.array_equal(actual,want),f'RGBA {n}/{mask}/{arm}');images+=1;selected+=n in selected_refs;nonselected+=n not in selected_refs
                if n in windows:
                    x0,y0,x1,y1=windows[n];sl=np.s_[y0+160:y1+160,x0+160:x1+160];need(np.array_equal(actual[sl],np.asarray(a.composite(n,mask,arm)[0])[sl]),f'Original muzzle {n}/{mask}/{arm}');muzzles+=1
        if n in selected_refs:frame_records.append({'ref':n,'before_rgba_sha256':sha(np.asarray(b.composite(n,15)[0]).tobytes()),'after_rgba_sha256':sha(np.asarray(b.composite(n,0)[0]).tobytes()),'tile_count':b.banks[0]['frames'][n]['tile_count']})
    raw_checks=nonraw=0
    for gb,bank in enumerate(a.banks):
        need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Graphics bank boundaries')
        for n in range(len(bank['frames'])):
            raw_checks+=1
            if gb==0 and n in selected_refs:continue
            need(raw(a,gb,n)==raw(b,gb,n),f'Nonselected raw {gb}/{n}');nonraw+=1
    composition_checks=0
    need(bank_offsets(a.c)==bank_offsets(b.c),'Composition bank boundaries')
    for pb in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
            if (n,pb)in targets:continue
            need(records(a.c,pb,n)==records(b.c,pb,n),f'Nonselected composition {pb}/{n}');composition_checks+=1
    gpu=0;effect_tiles=0
    for n in selected_refs:
        count=b.banks[0]['frames'][n]['tile_count'];need(count==32,'Buffer limit');atlas=np.frombuffer(indexed_atlas(raw(b,0,n),count)[0],np.uint8).reshape(32,256)
        for pb in producer.PBS:
            for p in composition_frame(b.c,pb,n)['parts']:
                ti=p['tile'];tile=atlas[ti//16*16:ti//16*16+16,ti%16*16:ti%16*16+16]
                if ti%16==0:need(not tile[:,0].any(),'GPU first-column')
                if p['flip_y']and ti//16==0:need(not tile[0].any(),'GPU flipY row')
                gpu+=1
        if n in NOVA:
            old_atlas=np.frombuffer(indexed_atlas(raw(a,0,n),a.banks[0]['frames'][n]['tile_count'])[0],np.uint8).reshape(32,256)
            keep={p['tile']for pb in producer.PBS[1:]for p in composition_frame(a.c,pb,n)['parts']}
            for ti in keep:need(np.array_equal(atlas[ti//16*16:ti//16*16+16,ti%16*16:ti%16*16+16],old_atlas[ti//16*16:ti//16*16+16,ti%16*16:ti%16*16+16]),'Original Nova effect full tile');effect_tiles+=1
    layout=lambda data:[{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(data)]
    need(layout(a.data)==layout(b.data),'ARC layout');expected_bytes=bytearray(a.data)
    for e in psx_arc(a.data):
        if int(e['type'],16)in(2,3):expected_bytes[e['offset']:e['offset']+e['size']]=b.data[e['offset']:e['offset']+e['size']]
    need(expected_bytes==b.data,'Other entries/audio/palette')
    effects=[]
    for n in(73,74):
        fx=np.array(Image.open(D/f'structure_v3/effect_{n:03}.png'));visible=fx>0;need(np.array_equal(b.layer(n,0)[0][visible],fx[visible]),'Original dash effect');effects.append({'ref':n,'exact_texels':int(visible.sum()),'index_sha256':sha(fx.tobytes())})
    pair_checks=[]
    for n in tuple(range(67,85,2))+(93,):
        f,g=b.banks[0]['frames'][n:n+2];need(f['offset']==g['offset']and f['tile_count']==g['tile_count']==32,'Paired alias');pair_checks.append([n,n+1])
    rejected=[]
    def reject(name,call):
        try:call()
        except(ValueError,KeyError,TypeError):rejected.append(name)
        else:raise ValueError('Invalid input accepted: '+name)
    bad=bytearray(a.data);bad[-1]^=1;reject('wrong_parent',lambda:producer.validate_source(bytes(bad)));reject('existing_output',lambda:producer.validate_output(out));reject('outside_output',lambda:producer.validate_output(ROOT/'unauthorized_candidate'))
    for name,mut in [('manifest_parent',lambda m:m.update(source_arc_sha256='0'*64)),('duplicate_manifest_ref',lambda m:m['frames'].__setitem__(0,m['frames'][1])),('manifest_pixel_hash',lambda m:m['frames'][0].update(base_sha256='0'*64))]:
        m=copy.deepcopy(meta);mut(m);reject(name,lambda m=m:producer.validate_targets({k:v for k,v in targets.items()if k[0]in producer.REFS},m))
    base_targets={k:v for k,v in targets.items()if k[0]in producer.REFS}
    t=dict(base_targets);t.pop((67,0));reject('missing_target',lambda:producer.validate_targets(t,meta))
    for name,value in [('pixel_mutation',base_targets[67,0].copy()),('wrong_shape',np.zeros((383,384),np.uint8)),('wrong_depth',base_targets[67,0].astype(np.uint16)),('invalid_palette_index',base_targets[67,0].copy())]:
        if name=='pixel_mutation':value[160,160]^=1
        if name=='invalid_palette_index':value[0,0]=16
        t=dict(base_targets);t[67,0]=value;reject(name,lambda t=t:producer.validate_targets(t,meta))
    t=dict(base_targets);t[67,0]=t[67,0].copy();t[67,0][0,0]=1;m=copy.deepcopy(meta);m['frames'][0]['base_sha256']=sha(t[67,0].tobytes());reject('outside_packing_window',lambda:producer.validate_targets(t,m))
    write(out/'extended_verification.json',{'passed':True,'parent_sha256':sha(a.data),'candidate_sha256':sha(b.data),'dash_refs':list(producer.REFS),'nova_head_only_refs':list(NOVA),'raw_checks':raw_checks,'nonselected_raw_exact':nonraw,'layers_checked':layers,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':composition_checks,'rgba_combinations_checked':images,'selected_combinations_checked':selected,'unchanged_combinations_checked':nonselected,'original_muzzle_rgba_checked':muzzles,'dash_effects':effects,'original_nova_effect_tiles_exact':effect_tiles,'gpu_parts':gpu,'paired_streams':pair_checks,'frames':frame_records,'directory_layout_unchanged':True,'palette_audio_other_entries_exact':True,'negative_cases':rejected,'runtime_verified':False,'native_mips_verified':False,'scope':'228 유효 참조 ×16 표시마스크 ×팔형2 직접 합성. 정상 Ultimate 표시는 획득전15/획득후0,217..230은 항상15. 기타 마스크는 구조 회귀이며 실기 아님.'})
    print(json.dumps({'passed':True,'rgba':images,'muzzles':muzzles,'raw':raw_checks,'nonraw':nonraw,'rejections':len(rejected)}),flush=True)
if __name__=='__main__':main()
