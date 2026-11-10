"""수용 효과판 위에 탑승 머리19참조만 추가한다. 좌표와 빈 참조80을 보존한다."""
import json,struct,sys,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_ride_heads import OUT,PARENT
from scripts.build_rin_idle import entry,sha
from scripts.project import digest
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_hurt_launch import compose_launch
from src.psx_frame_edit import read_indexed_png,edit_frame_set
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks
IDS=set(range(66,86))-{80}

def prepare():
    m=json.loads((PARENT/'manifest.json').read_text('utf-8'));r=json.loads((OUT/'recipe.json').read_text('utf-8'));a=(PARENT/'modified.arc').read_bytes()
    if sha(a)!=m['modified_archive_sha256'] or r['parent_sha256']!=m['modified_bin']['sha256']:raise ValueError('Parent differs')
    if r['issues'] or set(map(int,r['frames']))!=IDS or r['preserved_blank_refs']!=[80]:raise ValueError('Incomplete head recipe')
    gm,g=entry(a,2);p=entry(a,3)[1];pal=struct.unpack_from('<16H',entry(a,9)[1]);frames={};streams={}
    for n in IDS:
        rec=r['frames'][str(n)];path=OUT/rec['file']
        if digest(path)!=rec['sha256']:raise ValueError('Head art changed')
        frames[n]=read_indexed_png(path,pal)
        if frames[n][1]!=(16,16):raise ValueError('Head size changed')
    for f in graphics_bank(g,1)['frames']:streams.setdefault(f['offset'],[]).append(f)
    replacements={};packed_expected={}
    for off,refs in streams.items():
        selected=[f for f in refs if f['index'] in IDS]
        if not selected:continue
        f=refs[0];raw=decode_stream(g,off,f['limit'],f['tile_count']*128).data
        edits=[(composition_frame(p,5,q['index']),*frames[q['index']]) for q in selected];protected=[composition_frame(p,5,q['index']) for q in refs if q not in selected]
        packed=edit_frame_set(raw,f['tile_count'],edits,preserved_compositions=protected)
        atlas,_,_=indexed_atlas(packed,f['tile_count'])
        for q in selected:
            c=composition_frame(p,5,q['index']);t=c['parts'][0]['tile']
            if t%16==0 and any(atlas[(t//16*16+y)*256] for y in range(16)):raise ValueError('Mirror edge occupied')
        code=encode_stream(packed)
        for q in refs:replacements[q['index']]=code;packed_expected[q['index']]=packed
    newg,repack=repack_graphics_bank(g,1,replacements);checked=0;preserved=0
    for bi in (0,1):
        for old,new in zip(graphics_bank(g,bi)['frames'],graphics_bank(newg,bi)['frames']):
            n=old['index'];raw=decode_stream(g,old['offset'],old['limit'],old['tile_count']*128).data;decoded=decode_stream(newg,new['offset'],new['limit'],new['tile_count']*128).data
            if old['tile_count']!=new['tile_count']:raise ValueError('Tile count changed')
            if bi==1 and n in IDS:
                c=composition_frame(p,5,n);pic=compose_launch(decoded,new['tile_count'],c)
                if pic[:2]!=frames[n]:raise ValueError('Head readback differs')
            elif bi==1 and n==80:
                c=composition_frame(p,5,n)
                if compose_launch(raw,old['tile_count'],c)[:3]!=compose_launch(decoded,new['tile_count'],c)[:3] or any(compose_launch(decoded,new['tile_count'],c)[0]):raise ValueError('Blank reference80 changed')
                preserved+=1
            elif raw!=decoded:raise ValueError(f'Existing sprite data changed {bi}:{n}')
            else:preserved+=1
            checked+=1
    result=bytearray(a);result[gm['offset']:gm['offset']+gm['size']]=newg
    for e in psx_arc(a):
        if e['type']!='0x2' and result[e['offset']:e['offset']+e['size']]!=a[e['offset']:e['offset']+e['size']]:raise ValueError('Other ARC entry changed')
    report={'references_checked':checked,'heads_changed':sorted(IDS),'unique_heads':5,'other_compressed_displays_preserved':preserved,'blank80_preserved':True,'all_parts_positions_flags_tiles_exact':True,'palettes_static_effects_other_entries_exact':True,'repack':repack,'runtime_verified':False}
    return bytes(result),m,r,report

def main():
    arc,m,r,v=prepare();again,*_=prepare()
    if arc!=again:raise ValueError('Repeat assembly differs')
    source=PARENT/'rin_nana.bin';parent_sha=m['modified_bin']['sha256']
    if digest(source)!=parent_sha:raise ValueError('Parent BIN changed')
    preservation=json.loads((PARENT/'preservation.json').read_text('utf-8'))
    if any(digest(ROOT/q['path'])!=q['expected_sha256'] for q in preservation['files']):raise ValueError('Protected input changed')
    out=ROOT/'out/ver_rin_nana'/('rin_ride_heads_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'));rec={**profile['zero_archive'],'sha256':m['modified_archive_sha256']}
    result=write_archive_copy(source,out/'rin_nana.bin',rec,arc,parent_sha);(out/'rin_nana.cue').write_bytes((PARENT/'rin_nana.cue').read_bytes());(out/'modified.arc').write_bytes(arc)
    changed={q['lba'] for q in result['changed_sectors']};count=0;readback=bytearray()
    with source.open('rb') as s,(out/'rin_nana.bin').open('rb') as t:
        while True:
            x=s.read(2352);y=t.read(2352)
            if not x:
                if y:raise ValueError('Output longer than parent')
                break
            if len(x)!=len(y) or (x!=y)!=(count in changed):raise ValueError('Unexpected disc change')
            if count in changed:validate_checks(y)
            if rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048:readback.extend(y[24:2072])
            count+=1
    if readback[:len(arc)]!=arc:raise ValueError('Readback differs')
    if any(digest(ROOT/q['path'])!=q['expected_sha256'] for q in preservation['files']):raise ValueError('Protected input changed during build')
    v.update(repeat_arc_identical=True,all_disc_sectors_compared=count,changed_sectors=len(changed),sector_comparison_basis=parent_sha,edc_ecc_checked=True,reextracted_arc_equal=True,all_other_parent_sectors_exact=True,embedded_static_bodies=m['verification']['embedded_static_bodies'])
    shutil.copytree(OUT,out/'art');cumulative=sorted(set(m['cumulative_bank1_frames'])|IDS)
    manifest={**m,'kind':'rin_ride_heads','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':parent_sha,'modified_bin':result,'modified_archive_sha256':sha(arc),'art_recipe':(out/'art/recipe.json').relative_to(ROOT).as_posix(),'verification':v,'inherited_verification':m['verification'],'cumulative_bank1_frames':cumulative,'runtime_verified':False}
    manifest['bank1_frame_inputs']={**m['bank1_frame_inputs'],**{n:{'path':str(out/'art'/q['file']),'sha256':q['sha256'],'bounds':q['bounds']} for n,q in r['frames'].items()}}
    for name,data in [('manifest.json',manifest),('verification.json',v),('preservation.json',preservation)]: (out/name).write_text(json.dumps(data,indent=2)+'\n','utf-8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'frames':m['cumulative_frames'],'bank1_frames':cumulative,'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf-8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'total_refs':len(cumulative)+len(m['cumulative_frames']),'changed_sectors':len(changed)}))

if __name__=='__main__':main()
