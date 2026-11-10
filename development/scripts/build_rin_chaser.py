"""수용 탑승 머리판에 체이서28참조를 누적하고 디스크 전체를 재검사한다."""
import json,struct,sys,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_chaser import OUT,PARENT
from scripts.build_rin_idle import entry,sha
from scripts.project import digest
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
from src.psx_frame_edit import read_indexed_png
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks
IDS=set(range(14,42))

def prepare():
    m=json.loads((PARENT/'manifest.json').read_text());r=json.loads((OUT/'recipe.json').read_text());a=(PARENT/'modified.arc').read_bytes()
    if sha(a)!=m['modified_archive_sha256'] or r['parent_sha256']!=m['modified_bin']['sha256'] or r['parent_arc_sha256']!=sha(a):raise ValueError('Parent differs')
    if r['issues'] or set(map(int,r['frames']))!=IDS:raise ValueError('Incomplete chaser recipe')
    gm,g=entry(a,2);pm,oldparts=entry(a,3);parts=(OUT/'composition_entry.bin').read_bytes();words=struct.unpack_from('<16H',entry(a,9)[1]);frames={}
    if len(parts)!=len(oldparts) or sha(parts)!=r['parts_sha256']:raise ValueError('Parts changed')
    permitted={p['record_offset']+axis for n in IDS for p in composition_frame(oldparts,5,n)['parts'] for axis in (2,3)}
    if any(x!=y and i not in permitted for i,(x,y) in enumerate(zip(oldparts,parts))):raise ValueError('Non-position part change')
    for n in IDS:
        rec=r['frames'][str(n)];path=OUT/rec['file']
        if digest(path)!=rec['sha256']:raise ValueError('Art changed')
        frames[n]=read_indexed_png(path,words)
    replacements={}
    for s in r['streams']:
        packed=(OUT/s['file']).read_bytes()
        if sha(packed)!=s['sha256']:raise ValueError('Stream changed')
        f=graphics_bank(g,1)['frames'][s['base']];source=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        if sha(source)!=s['source_sha256'] or len(packed)!=len(source):raise ValueError('Stream source differs')
        code=encode_stream(packed)
        for n in s['references']:replacements[n]=code
    if set(replacements)!=IDS:raise ValueError('Stream selection differs')
    newg,repack=repack_graphics_bank(g,1,replacements);checked=0;preserved=0
    for bi in (0,1):
        pb=0 if bi==0 else 5
        for old,new in zip(graphics_bank(g,bi)['frames'],graphics_bank(newg,bi)['frames']):
            n=old['index'];raw=decode_stream(g,old['offset'],old['limit'],old['tile_count']*128).data;decoded=decode_stream(newg,new['offset'],new['limit'],new['tile_count']*128).data
            if old['tile_count']!=new['tile_count']:raise ValueError('Tile count changed')
            oc=composition_frame(oldparts,pb,n);nc=composition_frame(parts,pb,n)
            if bi==1 and n in IDS:
                actual=compose_launch(decoded,new['tile_count'],nc)
                if actual[:2]!=frames[n] or list(actual[2])!=r['frames'][str(n)]['bounds']:raise ValueError('Chaser readback differs')
                if len(oc['parts'])!=len(nc['parts']) or any({k:v for k,v in x.items() if k not in ('x','y')}!={k:v for k,v in y.items() if k not in ('x','y')} for x,y in zip(oc['parts'],nc['parts'])):raise ValueError('Part metadata changed')
            elif raw!=decoded or oc!=nc:raise ValueError(f'Existing sprite changed {bi}:{n}')
            else:preserved+=1
            checked+=1
    result=bytearray(a);result[gm['offset']:gm['offset']+gm['size']]=newg;result[pm['offset']:pm['offset']+pm['size']]=parts
    for e in psx_arc(a):
        if e['type'] not in ('0x2','0x3') and result[e['offset']:e['offset']+e['size']]!=a[e['offset']:e['offset']+e['size']]:raise ValueError('Other ARC entry changed')
    report={'references_checked':checked,'chaser_changed':sorted(IDS),'other_compressed_refs_preserved':preserved,'existing_285_displays_preserved':True,'selected_parts_xy_only':True,'part_counts_flags_tiles_order_preserved':True,'palettes_static_effects_other_entries_exact':True,'original_bob_y_preserved':True,'body_and_ribbon_layers_independent':True,'repack':repack,'runtime_verified':False,'unresolved_refs_preserved':list(range(42,50))}
    return bytes(result),m,r,report

def main():
    arc,m,r,v=prepare();again,*_=prepare()
    if arc!=again:raise ValueError('Repeat differs')
    source=PARENT/'rin_nana.bin';parent_sha=m['modified_bin']['sha256']
    if digest(source)!=parent_sha:raise ValueError('Parent BIN changed')
    preservation=json.loads((PARENT/'preservation.json').read_text())
    if any(digest(ROOT/q['path'])!=q['expected_sha256'] for q in preservation['files']):raise ValueError('Protected input changed')
    out=ROOT/'out/ver_rin_nana'/('rin_chaser_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text());rec={**profile['zero_archive'],'sha256':m['modified_archive_sha256']}
    result=write_archive_copy(source,out/'rin_nana.bin',rec,arc,parent_sha);(out/'rin_nana.cue').write_bytes((PARENT/'rin_nana.cue').read_bytes());(out/'modified.arc').write_bytes(arc)
    changed={q['lba'] for q in result['changed_sectors']};count=0;readback=bytearray()
    with source.open('rb') as s,(out/'rin_nana.bin').open('rb') as t:
        while True:
            x=s.read(2352);y=t.read(2352)
            if not x:
                if y:raise ValueError('Output too long')
                break
            if len(x)!=len(y) or (x!=y)!=(count in changed):raise ValueError('Unexpected disc change')
            if count in changed:validate_checks(y)
            if rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048:readback.extend(y[24:2072])
            count+=1
    if readback[:len(arc)]!=arc:raise ValueError('Readback differs')
    if any(digest(ROOT/q['path'])!=q['expected_sha256'] for q in preservation['files']):raise ValueError('Protected input changed during build')
    v.update(repeat_arc_identical=True,all_disc_sectors_compared=count,changed_sectors=len(changed),sector_comparison_basis=parent_sha,edc_ecc_checked=True,reextracted_arc_equal=True,all_other_parent_sectors_exact=True,embedded_static_bodies=m['verification']['embedded_static_bodies'])
    shutil.copytree(OUT,out/'art');cumulative=sorted(set(m['cumulative_bank1_frames'])|IDS)
    manifest={**m,'kind':'rin_chaser','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':parent_sha,'modified_bin':result,'modified_archive_sha256':sha(arc),'art_recipe':(out/'art/recipe.json').relative_to(ROOT).as_posix(),'verification':v,'inherited_verification':m['verification'],'cumulative_bank1_frames':cumulative,'runtime_verified':False}
    manifest['bank1_frame_inputs']={**m['bank1_frame_inputs'],**{n:{'path':str(out/'art'/q['file']),'sha256':q['sha256'],'bounds':q['bounds']} for n,q in r['frames'].items()}}
    for name,data in [('manifest.json',manifest),('verification.json',v),('preservation.json',preservation)]: (out/name).write_text(json.dumps(data,indent=2)+'\n','utf-8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'frames':m['cumulative_frames'],'bank1_frames':cumulative,'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf-8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'total_refs':len(cumulative)+len(m['cumulative_frames']),'changed_sectors':len(changed)}))

if __name__=='__main__':main()
