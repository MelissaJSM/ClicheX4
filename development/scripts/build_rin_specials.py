"""수용된 린 몸체를 보존하며 준비된 특수기술만 별도 BIN에 추가한다."""
import argparse,json,struct,sys,shutil,os
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_specials import OUT,PARENT,GROUPS
from scripts.build_rin_idle import entry,sha
from scripts.project import digest,load_project,inspect_references,working_cue
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_hurt_launch import compose_launch
from src.psx_frame_edit import edit_frame_set,read_indexed_png,frame_coverage,_apply_writes
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks
from scripts.assemble_rin_special_frames import prepare as prepare_shared
from scripts.prepare_rin_static_burst import prepare as prepare_static

def prepare(groups):
    pm=json.loads((PARENT/'manifest.json').read_text('utf-8'));arc=(PARENT/'modified.arc').read_bytes()
    if sha(arc)!=pm['modified_archive_sha256']:raise ValueError('Parent ARC changed')
    gm,g=entry(arc,2);cm,oldparts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<16H',pal)
    parts=bytearray(oldparts);frames={0:{},1:{}};recipes={};allowed=set()
    for group in groups:
        folder=OUT/group;r=json.loads((folder/'registered.json').read_text('utf-8'));bi,ns=GROUPS[group];pb=0 if bi==0 else 5
        actual=set(map(int,r['frames']))
        if r['issues'] or actual!=set(ns):raise ValueError(f'Incomplete {group}')
        if r['parent_sha256']!=pm['modified_bin']['sha256']:raise ValueError('Recipe parent differs')
        edited=(folder/'composition_entry.bin').read_bytes()
        if sha(edited)!=r['composition_sha256'] or len(edited)!=len(parts):raise ValueError('Changed recipe parts')
        group_allowed=set()
        for n in ns:
            a=composition_frame(oldparts,pb,n);b=composition_frame(edited,pb,n)
            if len(a['parts'])!=len(b['parts']):raise ValueError('Part count differs')
            for x,y in zip(a['parts'],b['parts']):
                if any(x[k]!=y[k] for k in x if k not in ('x','y')):raise ValueError('Part metadata differs')
                group_allowed.update((x['record_offset']+2,x['record_offset']+3))
            rec=r['frames'][str(n)];path=folder/rec['file']
            if digest(path)!=rec['sha256']:raise ValueError('Indexed art changed')
            frames[bi][n]=read_indexed_png(path,words)
        for i,(a,b) in enumerate(zip(oldparts,edited)):
            if a!=b:
                if i not in group_allowed or parts[i] not in (a,b):raise ValueError('Unrelated/colliding parts change')
                parts[i]=b
        allowed.update(group_allowed);recipes[group]=r
    parts,frames,sharing,worlds=prepare_shared(g,oldparts,parts,frames,words,groups)
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(oldparts,parts))):raise ValueError('Special sharing changed unrelated parts')
    modified=g;packing=[];changed_streams={}
    for bi in (0,1):
        pb=0 if bi==0 else 5;bank=graphics_bank(g,bi);streams={}
        for f in bank['frames']:streams.setdefault(f['offset'],[]).append(f)
        replacements={}
        for off,refs in streams.items():
            chosen=[f for f in refs if f['index'] in frames[bi]]
            if not chosen:continue
            f=refs[0];raw=decode_stream(g,off,f['limit'],f['tile_count']*128).data
            edits=[(composition_frame(parts,pb,q['index']),*frames[bi][q['index']]) for q in chosen]
            protected=[composition_frame(oldparts,pb,q['index']) for q in refs if q not in chosen]
            # These selected bodies are fully replaced. Their relocated windows
            # may overlap; give them equal blank sources, while forbidding any
            # overlap with preserved effects. Final rendering is still exact.
            owned={s for c,px,sz in edits for cell in frame_coverage(raw,f['tile_count'],c)[0] for s in cell}
            retained={s for c in protected for cell in frame_coverage(raw,f['tile_count'],c)[0] for s in cell}
            if owned&retained:raise ValueError('Body tiles overlap preserved effect sources')
            seed=_apply_writes(raw,dict.fromkeys(owned,0))
            try:packed=edit_frame_set(seed,f['tile_count'],edits,preserved_compositions=protected,overlap_policy='equal_sources')
            except ValueError as e:raise ValueError(f'Bank{bi} refs{[q["index"] for q in refs]}: {e}') from e
            atlas,_,_=indexed_atlas(packed,f['tile_count'])
            for q in chosen:
                for p in composition_frame(parts,pb,q['index'])['parts']:
                    t=p['tile']
                    if t%16==0 and any(atlas[(t//16*16+y)*256] for y in range(16)):raise ValueError('Mirror U0 boundary')
            code=encode_stream(packed)
            for q in refs:replacements[q['index']]=code
            changed_streams[bi,off]=packed
        if replacements:
            modified,report=repack_graphics_bank(modified,bi,replacements);packing.append(report)
    checked=0;dest=OUT/('assembled_'+'_'.join(groups));dest.mkdir(exist_ok=True);final={0:{},1:{}}
    for bi in (0,1):
        pb=0 if bi==0 else 5;before=graphics_bank(g,bi);after=graphics_bank(modified,bi)
        if (before['base'],before['end'])!=(after['base'],after['end']):raise ValueError('Bank boundary changed')
        for a,b in zip(before['frames'],after['frames']):
            n=a['index'];old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(modified,b['offset'],b['limit'],b['tile_count']*128).data
            if a['tile_count']!=b['tile_count']:raise ValueError('Tile count changed')
            oc=composition_frame(oldparts,pb,n);nc=composition_frame(parts,pb,n)
            if n not in frames[bi] and old==new:
                if oc!=nc:raise ValueError(f'Unselected composition changed {bi}:{n}')
                checked+=1
                continue
            oldpic=compose_launch(old,a['tile_count'],oc);newpic=compose_launch(new,b['tile_count'],nc)
            if n in frames[bi]:
                if newpic[:2]!=(frames[bi][n][0],tuple(frames[bi][n][1])):raise ValueError(f'Render mismatch {bi}:{n}')
                p=dest/f'bank{bi}_{n:03d}.png';save_image(newpic[0],newpic[1],words,p);final[bi][str(n)]={'path':str(p),'sha256':digest(p),'bounds':newpic[2]}
            elif oldpic[:3]!=newpic[:3] or oc!=nc:raise ValueError(f'Unselected display changed {bi}:{n}')
            checked+=1
    result=bytearray(arc);result[gm['offset']:gm['offset']+gm['size']]=modified;result[cm['offset']:cm['offset']+cm['size']]=parts
    if len(result)!=len(arc):raise ValueError('ARC length changed')
    for e in psx_arc(arc):
        if e['type'] not in ('0x2','0x3') and result[e['offset']:e['offset']+e['size']]!=arc[e['offset']:e['offset']+e['size']]:raise ValueError('Unrelated ARC entry changed')
    static_report=None
    if 'burst' in groups:result,static_report=prepare_static(bytes(result),worlds)
    report={'groups':list(groups),'new_body_refs':{str(b):sorted(frames[b]) for b in (0,1)},'decoded_references_checked':checked,'existing_217_body_references_unchanged':True,'unselected_display_and_composition_unchanged':True,'paired_effects_preserved':True,'palettes_animations_other_entries_preserved':True,'part_metadata_unchanged':True,'selected_x_y_offsets_only':True,'in_bank_repacking':packing,'runtime_verified':False,**sharing}
    report['embedded_static_bodies']=static_report
    if static_report:
        report['palettes_animations_other_entries_preserved']=False
        report['palettes_animations_unchanged']=True
        report['changed_arc_entry_types']=['0x2','0x3','0x10206']
    accepted=ROOT/'out/ver_rin_nana/rin_specials_20261028T232523478200Z'
    am=json.loads((accepted/'manifest.json').read_text('utf-8'));aa=(accepted/'modified.arc').read_bytes()
    if sha(aa)!=am['modified_archive_sha256']:raise ValueError('Accepted 225 archive changed')
    ag=entry(aa,2)[1];ap=entry(aa,3)[1];accepted_checked=0
    for bi,ids in ((0,am['cumulative_frames']),(1,am['cumulative_bank1_frames'])):
        pb=0 if bi==0 else 5
        for n in ids:
            a=graphics_bank(ag,bi)['frames'][n];b=graphics_bank(modified,bi)['frames'][n]
            ar=decode_stream(ag,a['offset'],a['limit'],a['tile_count']*128).data;br=decode_stream(modified,b['offset'],b['limit'],b['tile_count']*128).data
            ac=composition_frame(ap,pb,n);bc=composition_frame(parts,pb,n)
            if ac!=bc or compose_launch(ar,a['tile_count'],ac)[:3]!=compose_launch(br,b['tile_count'],bc)[:3]:raise ValueError(f'Accepted225 pose changed {bi}:{n}')
            accepted_checked+=1
    report['accepted_build_sha256']=am['modified_bin']['sha256'];report['accepted_body_displays_preserved']=accepted_checked
    (dest/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');(dest/'modified.arc').write_bytes(result)
    return bytes(result),report,pm,final,dest

def main():
    p=argparse.ArgumentParser();p.add_argument('--groups',nargs='+',choices=GROUPS,default=['rise']);p.add_argument('--assemble-only',action='store_true');a=p.parse_args()
    if len(set(a.groups))!=len(a.groups):raise ValueError('Duplicate group')
    arc,report,pm,final,dest=prepare(a.groups)
    if a.assemble_only:print(json.dumps({'output':str(dest),'sha256':sha(arc),'refs':report['decoded_references_checked']}));return
    again,*_=prepare(a.groups)
    if arc!=again:raise ValueError('Repeated assembly differs')
    project=load_project(ROOT,'ver_rin_nana');inspect_references(ROOT,project)
    if digest(PARENT/'rin_nana.bin')!=pm['modified_bin']['sha256']:raise ValueError('Parent BIN changed')
    previous=json.loads((PARENT/'preservation.json').read_text('utf-8'));protected=[]
    for rec in previous['files']:
        actual=digest(ROOT/rec['path']);protected.append({**rec,'actual_sha256':actual,'unchanged':actual==rec['expected_sha256']})
    if not all(q['unchanged'] for q in protected):raise ValueError('Protected input changed')
    out=ROOT/'out/ver_rin_nana'/('rin_specials_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'));source=ROOT/project['source_bin'];target=out/'rin_nana.bin';result=write_archive_copy(source,target,profile['zero_archive'],arc,project['source_sha256'])
    (out/'rin_nana.cue').write_text(working_cue((ROOT/project['source_cue']).read_text('utf-8-sig'),'rin_nana.bin'),'ascii',newline='');(out/'modified.arc').write_bytes(arc)
    changed={q['lba'] for q in result['changed_sectors']};rec=profile['zero_archive'];readback=bytearray();count=0
    with source.open('rb') as s,target.open('rb') as t:
        while True:
            x=s.read(2352);y=t.read(2352)
            if not x:
                if y:raise ValueError('Long output')
                break
            if len(x)!=len(y) or (x!=y)!=(count in changed):raise ValueError('Unexpected sector difference')
            if count in changed:validate_checks(y)
            if rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048:readback.extend(y[24:2072])
            count+=1
    if readback[:len(arc)]!=arc:raise ValueError('BIN readback differs')
    report.update({'repeat_arc_identical':True,'all_disc_sectors_compared':count,'changed_sectors':len(changed),'edc_ecc_checked':True,'reextracted_arc_equal':True})
    # A later correction must not invalidate this build's evidence paths.
    if report.get('embedded_static_bodies'):
        static_dir=out/'static_burst';shutil.copytree(OUT/'static_burst',static_dir)
        original_recipe=OUT/'static_burst/static_effects.json';saved_recipe=static_dir/'static_effects.json';sr=json.loads(saved_recipe.read_text('utf-8'))
        evidence=(original_recipe.parent/sr['palette_evidence_file']).resolve();sr['palette_evidence_file']=os.path.relpath(evidence,static_dir)
        saved_recipe.write_text(json.dumps(sr,indent=2)+'\n','utf-8');report['embedded_static_bodies']['recipe']=str(saved_recipe);report['embedded_static_bodies']['recipe_sha256']=digest(saved_recipe)
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
    sprite_dir=out/'sprites';sprite_dir.mkdir()
    for bi in (0,1):
        for n,rec in final[bi].items():
            source=Path(rec['path']);target_sprite=sprite_dir/source.name;shutil.copy2(source,target_sprite);rec['path']=str(target_sprite)
    cumulative=sorted(set(pm['cumulative_frames'])|set(map(int,final[0])));bank1=sorted(set(pm['cumulative_bank1_frames'])|set(map(int,final[1])))
    manifest={'project':'ver_rin_nana','task':'zero_rin','kind':'accepted_style_specials','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':pm['modified_bin']['sha256'],'source_sha256':project['source_sha256'],'modified_bin':result,'modified_archive_sha256':sha(arc),'art_recipe':(out/'verification.json').relative_to(ROOT).as_posix(),'verification':report,'cumulative_frames':cumulative,'cumulative_bank1_frames':bank1,'bank1_frame_inputs':{**pm['bank1_frame_inputs'],**final[1]},'runtime_verified':False}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n','utf-8');(out/'preservation.json').write_text(json.dumps({'files':protected},ensure_ascii=False,indent=2)+'\n','utf-8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'frames':cumulative,'bank1_frames':bank1,'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf-8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'new_refs':sum(len(final[b]) for b in (0,1)),'total_refs':len(cumulative)+len(bank1),'changed_sectors':len(changed)}))

if __name__=='__main__':main()
