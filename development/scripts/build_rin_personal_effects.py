"""수용된 린 몸체를 보존하고 순수 전송 빛·잔상·사망 구체를 청백색으로 연결."""
import argparse,json,struct,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_idle import entry,sha
from scripts.project import load_project,digest,working_cue
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.extract_zero import save_image
from src.psx_personal_effects import apply_warp,recolor_stage,trail_palette,WARP_FRAMES
from src.psx_death_orbs import recolor_death_orbs
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
from src.psx_static_effect import compose_static
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

WARP_LUT=bytes((0,11,10,7,6,10,5,4,15,10,6,1,8,11,10,11))
DEATH_LUT=bytes((0,10,11,12,14,5,6,7,8,9,10,11,12,13,14,15))

def prepare(parent):
    m=json.loads((parent/'manifest.json').read_text('utf-8'));original=(parent/'modified.arc').read_bytes()
    if m['kind']!='accepted_style_specials' or sha(original)!=m['modified_archive_sha256']:raise ValueError('Unexpected effect parent')
    arc,warp=apply_warp(original,lut=WARP_LUT);arc,death=recolor_death_orbs(arc,lut_override=DEATH_LUT)
    oldg=entry(original,2)[1];g=entry(arc,2)[1];oldp=entry(original,3)[1];p=entry(arc,3)[1];palette=entry(arc,9)[1][:32]
    if entry(original,9)[1]!=entry(arc,9)[1]:raise ValueError('Player palettes changed')
    checked=0
    for bi in (0,1):
        pb=0 if bi==0 else 5
        for a,b in zip(graphics_bank(oldg,bi)['frames'],graphics_bank(g,bi)['frames']):
            n=a['index'];ar=decode_stream(oldg,a['offset'],a['limit'],a['tile_count']*128).data;br=decode_stream(g,b['offset'],b['limit'],b['tile_count']*128).data;ac=composition_frame(oldp,pb,n);bc=composition_frame(p,pb,n)
            if ac!=bc:raise ValueError('Compressed composition changed')
            if ar!=br:
                before=compose_launch(ar,a['tile_count'],ac);after=compose_launch(br,b['tile_count'],bc)
                expected=bytes(WARP_LUT[v] for v in before[0]) if n in WARP_FRAMES[bi] else before[0]
                if after[:3]!=(expected,*before[1:3]):raise ValueError(f'Unexpected body/effect change {bi}:{n}')
            checked+=1
    for n in (23,24):
        a=compose_static(entry(original,0x10206)[1],composition_frame(oldp,6,n));b=compose_static(entry(arc,0x10206)[1],composition_frame(p,6,n))
        if a[:3]!=b[:3]:raise ValueError('Accepted burst silhouette changed')
    for rec in psx_arc(original):
        if rec['type'] not in ('0x2','0x3','0x10206') and original[rec['offset']:rec['offset']+rec['size']]!=arc[rec['offset']:rec['offset']+rec['size']]:raise ValueError('Unrelated ARC entry changed')
    return arc,{'warp':warp,'death':death,'compressed_references_checked':checked,'body_266_and_burst_static2_preserved':True,'geometry_timing_exe_unchanged':True,'warp_lut':list(WARP_LUT),'trail_reference_index':6,'trail_palette_hex':trail_palette(palette,reference_index=6).hex()},m,palette

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--prepare-only',action='store_true');a=ap.parse_args();parent=a.parent.resolve()
    if not parent.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Isolated parent required')
    arc,report,pm,palette=prepare(parent);again,*_=prepare(parent)
    if arc!=again:raise ValueError('Effect reproduction differs')
    config=json.loads((ROOT/'config/riko_personal_effects_us.json').read_text('utf-8'));project=load_project(ROOT,'ver_rin_nana');source=ROOT/project['source_bin'];profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'))
    if config['source_sha256']!=project['source_sha256']:raise ValueError('Input profile differs')
    replacements=[(profile['zero_archive'],arc)];stage_reports=[]
    with source.open('rb') as f:
        disc=DiscReader(f,source.stat().st_size);actual={r['path']:r for r in disc.inspect()['files']}
        for rec in config['stage_archives']:
            if any(actual[rec['path']][k]!=rec[k] for k in ('lba','size')):raise ValueError('Stage file moved')
            old=disc.read(rec['lba'],rec['size']);new=recolor_stage(old,rec['sha256'],palette,reference_index=6);replacements.append((rec,new));stage_reports.append({**rec,'modified_sha256':sha(new)})
    report['stage_archives']=stage_reports;report['repeat_arc_identical']=True
    if a.prepare_only:
        d=ROOT/'work/ver_rin_nana/personal_effects/v1';d.mkdir(parents=True,exist_ok=True);(d/'modified.arc').write_bytes(arc);(d/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps({'output':str(d),'sha256':sha(arc),'stages':len(stage_reports)}));return
    if digest(parent/'rin_nana.bin')!=pm['modified_bin']['sha256']:raise ValueError('Parent BIN changed')
    preservation=json.loads((parent/'preservation.json').read_text('utf-8'))
    if any(digest(ROOT/r['path'])!=r['expected_sha256'] for r in preservation['files']):raise ValueError('Protected input changed')
    out=ROOT/'out/ver_rin_nana'/('rin_personal_effects_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    modified=write_archive_copies(source,out/'rin_nana.bin',replacements,project['source_sha256']);(out/'modified.arc').write_bytes(arc)
    (out/'rin_nana.cue').write_text(working_cue((ROOT/project['source_cue']).read_text('utf-8-sig'),'rin_nana.bin'),'ascii')
    changed={r['lba'] for r in modified['changed_sectors']};count=0
    with source.open('rb') as s,(out/'rin_nana.bin').open('rb') as t:
        while True:
            x=s.read(2352);y=t.read(2352)
            if not x:
                if y:raise ValueError('Output longer than source')
                break
            if len(x)!=len(y) or (x!=y)!=(count in changed):raise ValueError('Unexpected disc change')
            if count in changed:validate_checks(y)
            count+=1
    with (out/'rin_nana.bin').open('rb') as t:
        disc=DiscReader(t,(out/'rin_nana.bin').stat().st_size)
        for rec,data in replacements:
            if disc.read(rec['lba'],rec['size'])!=data:raise ValueError('Archive readback differs')
    report.update(all_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,all_25_archives_readback_equal=True,runtime_verified=False)
    m={**pm,'kind':'rin_personal_effects','parent':parent.relative_to(ROOT).as_posix(),'parent_sha256':pm['modified_bin']['sha256'],'modified_bin':modified,'modified_archive_sha256':sha(arc),'personal_effects':report,'runtime_verified':False,'inherited_special_verification':pm['verification']}
    # Earlier evidence is explicitly inherited, not a fresh count for this layer.
    m['verification']={'parent_specials':parent.relative_to(ROOT).as_posix(),'embedded_static_bodies':pm['verification']['embedded_static_bodies'],**report}
    for name,data in [('manifest.json',m),('verification.json',report),('preservation.json',preservation)]: (out/name).write_text(json.dumps(data,indent=2)+'\n','utf-8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':modified['sha256'],'frames':m['cumulative_frames'],'bank1_frames':m['cumulative_bank1_frames'],'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf-8');print(json.dumps({'output':str(out),'sha256':modified['sha256'],'warp_refs':13,'death_refs':9,'stage_cluts':len(stage_reports)*3}))

if __name__=='__main__':main()
