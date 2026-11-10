"""수용 대기/수정 눈감음을 보존하고 린 이동18참조를 별도 BIN으로 적용."""
import argparse,hashlib,json,struct,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,working_cue,load_project,inspect_references
from scripts.build_rin_idle import entry,sha
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas
from src.psx_frame_edit import read_indexed_png,edit_frame_set
from src.psx_compress import replace_stream
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks

ART=ROOT/'work/ver_rin_nana/run_production/v2'
PARENT=ROOT/'out/ver_rin_nana/rin_idle_20261028T090209662967Z'
PARENT_SHA='33643006ab25a401d0c582eb8698fcb058162ebf494f3486aefec93080b592a3'
IDS=set(range(3,21))

def prepare(art=ART):
    art=art.resolve()
    if not art.is_relative_to(ROOT/'work/ver_rin_nana/run_production'):raise ValueError('Unexpected motion art path')
    project=load_project(ROOT,'ver_rin_nana');inspect_references(ROOT,project)
    m=json.loads((PARENT/'manifest.json').read_text('utf-8'));arc=(PARENT/'modified.arc').read_bytes()
    if m['modified_bin']['sha256']!=PARENT_SHA or sha(arc)!=m['modified_archive_sha256']:raise ValueError('Parent identity mismatch')
    r=json.loads((art/'run_recipe.json').read_text('utf-8'))
    if r['issues'] or set(map(int,r['frames']))!=IDS:raise ValueError('Motion inputs incomplete')
    gm,g=entry(arc,2);cm,oldparts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<16H',pal)
    if sha(pal[:32])!=r['palette_sha256']:raise ValueError('Palette differs from accepted idle')
    parts=(art/'composition_entry.bin').read_bytes()
    if sha(parts)!=r['composition_sha256'] or len(parts)!=len(oldparts):raise ValueError('Composition input mismatch')
    changed_comps=[];allowed_part_bytes=set()
    for bi,offset in enumerate(bank_offsets(oldparts)):
        count=struct.unpack_from('<I',oldparts,offset)[0]>>16
        for n in range(count):
            before=composition_frame(oldparts,bi,n);after=composition_frame(parts,bi,n)
            if before==after:continue
            if bi!=0 or n not in IDS or len(before['parts'])!=len(after['parts']):raise ValueError('Unrelated composition changed')
            for a,b in zip(before['parts'],after['parts']):
                if any(a[k]!=b[k] for k in a if k!='x'):raise ValueError('Only horizontal part registration allowed')
                allowed_part_bytes.add(a['record_offset']+2)
            changed_comps.append(n)
    if any(a!=b and i not in allowed_part_bytes for i,(a,b) in enumerate(zip(oldparts,parts))):raise ValueError('Unexpected composition bytes')
    frames={}
    for n in IDS:
        rec=r['frames'][str(n)];path=art/rec['file']
        if digest(path)!=rec['sha256']:raise ValueError('Frame changed')
        frames[n]=read_indexed_png(path,words)
    preserved_lower=[]
    if r.get('upper_revision'):
        previous=ROOT/'out/ver_rin_nana/rin_run_20261028T090848002789Z'
        pm=json.loads((previous/'manifest.json').read_text('utf-8'));pa=(previous/'modified.arc').read_bytes()
        if pm['modified_bin']['sha256']!='fd4ad489aaade5629986282542b11e197ec6b89005f61a3dbdd0d42215ac853e' or sha(pa)!=pm['modified_archive_sha256']:raise ValueError('Lower-body reference changed')
        _,pg=entry(pa,2);_,pp=entry(pa,3)
        if pp!=parts:raise ValueError('Upper revision must preserve every part coordinate')
        pb=graphics_bank(pg,0)
        for n in IDS:
            f=pb['frames'][n];raw=decode_stream(pg,f['offset'],f['limit'],f['tile_count']*128).data
            pixels,size,bounds,_=compose_indices(raw,f['tile_count'],composition_frame(pp,0,n));new,newsize=frames[n]
            if size!=tuple(newsize):raise ValueError('Upper revision changed frame size')
            cut=max(0,4-bounds[1])*size[0]
            if pixels[cut:]!=new[cut:]:raise ValueError('Accepted lower body changed')
            if n in (5,6) and pixels!=new:raise ValueError('Stop pose changed')
            preserved_lower.append(n)
    bank=graphics_bank(g,0);groups={}
    for f in bank['frames']:
        if f['index'] in IDS:groups.setdefault(f['offset'],[]).append(f)
    modified=g;budgets=[]
    for offset,refs in groups.items():
        if any(f['offset']==offset and f['index'] not in IDS for f in bank['frames']):raise ValueError('Shared unselected bitmap')
        f=refs[0];old=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
        packed=edit_frame_set(old,f['tile_count'],[(composition_frame(parts,0,q['index']),*frames[q['index']]) for q in refs])
        atlas,_,_=indexed_atlas(packed,f['tile_count'])
        for q in refs:
            for part in composition_frame(parts,0,q['index'])['parts']:
                t=part['tile']
                if t%16==0 and any(atlas[(t//16*16+y)*256] for y in range(16)):raise ValueError('Opaque mirror boundary')
        modified,budget=replace_stream(modified,f,packed);budgets.append({'frames':[q['index'] for q in refs],**budget})
    decoded_checked=0
    for bi in (0,1):
        if graphics_bank(g,bi)!=graphics_bank(modified,bi):raise ValueError('Graphics addresses changed')
        for f in graphics_bank(g,bi)['frames']:
            old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            new=decode_stream(modified,f['offset'],f['limit'],f['tile_count']*128).data
            if bi==0 and f['index'] in IDS:
                n=f['index'];actual=compose_indices(new,f['tile_count'],composition_frame(parts,0,n))
                if actual[:2]!=(frames[n][0],tuple(frames[n][1])):raise ValueError('Displayed frame differs')
            elif old!=new:raise ValueError('Unrelated bitmap changed')
            decoded_checked+=1
    patched=bytearray(arc);patched[gm['offset']:gm['offset']+gm['size']]=modified;patched[cm['offset']:cm['offset']+cm['size']]=parts
    for e in __import__('scripts.discover_inputs',fromlist=['psx_arc']).psx_arc(arc):
        if e['type'] not in ('0x2','0x3') and patched[e['offset']:e['offset']+e['size']]!=arc[e['offset']:e['offset']+e['size']]:raise ValueError('Other ARC entry changed')
    report={'modified_archive_sha256':sha(patched),'decoded_references_checked':decoded_checked,'modified_motion_frames':sorted(IDS),'preserved_idle_frames':[0,1,2,146,147,148],'blink_fix_preserved':True,'composition_frame_changes':changed_comps,'composition_changed_bytes':sum(a!=b for a,b in zip(parts,oldparts)),'part_counts_flags_tiles_order_preserved':True,'graphics_offsets_preserved':True,'palette_and_animations_preserved':True,'source_recipe_sha256':digest(art/'run_recipe.json'),'compression':budgets,'run_sequence':r['run_sequence'],'run_ticks':r['run_ticks'],'art_review_pending':True,'runtime_verified':False,'preserved_lower_body_frames':preserved_lower,'upper_revision':bool(r.get('upper_revision'))}
    return project,bytes(patched),report

def main():
    p=argparse.ArgumentParser();p.add_argument('--art-dir',type=Path,default=ART);args=p.parse_args();art=args.art_dir.resolve()
    project,arc,report=prepare(art);_,repeat,_=prepare(art)
    if repeat!=arc:raise ValueError('Repeated ARC differs')
    report['repeat_arc_identical']=True
    out=ROOT/'out/ver_rin_nana'/('rin_run_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'));source=ROOT/project['source_bin'];target=out/'rin_nana.bin'
    result=write_archive_copy(source,target,profile['zero_archive'],arc,project['source_sha256'])
    (out/'rin_nana.cue').write_text(working_cue((ROOT/project['source_cue']).read_text('utf-8-sig'),'rin_nana.bin'),'ascii',newline='')
    (out/'modified.arc').write_bytes(arc)
    changed={r['lba'] for r in result['changed_sectors']};count=0;readback=bytearray();rec=profile['zero_archive']
    with source.open('rb') as a,target.open('rb') as b:
        while True:
            x=a.read(2352);y=b.read(2352)
            if not x:break
            if (x!=y)!=(count in changed):raise ValueError('Unexpected disc sector difference')
            if count in changed:validate_checks(y)
            if rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048:readback.extend(y[24:2072])
            count+=1
    if readback[:len(arc)]!=arc:raise ValueError('BIN reextraction differs')
    report.update({'all_disc_sectors_compared':count,'changed_sectors':len(changed),'edc_ecc_checked':True,'reextracted_arc_equal':True})
    manifest={'project':'ver_rin_nana','task':'zero_rin','kind':'idle_and_run','source_sha256':project['source_sha256'],'parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,'modified_archive_sha256':sha(arc),'verification':report,'runtime_verified':False,'known_limit':'대기와 이동만 적용. 공격·공중 동작·UI·한글화·공통 콘텐츠 통합은 후속 범위.'}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'frames':sorted(IDS|{0,1,2,146,147,148}),'idle_art':'work/ver_rin_nana/idle_production/v2','motion_art':art.relative_to(ROOT).as_posix(),'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed),'frames':len(pointer['frames'])}))

if __name__=='__main__':main()
