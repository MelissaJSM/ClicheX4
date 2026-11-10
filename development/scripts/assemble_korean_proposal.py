"""Merge independently verified resource proposals without writing a game BIN."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D,PARENT,PARENT_HASH,SOURCE_HASH
from scripts.discover_inputs import psx_arc,sha256
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.verify_korean_dialogue import verify
from scripts.project import digest

PARTS=['dialogue_full_v5','ui_proposal_v7','menu_proposal_v3','ending_proposal_v4','stage_proposal_v2','boss_proposal_v3']

def main(output):
    output.mkdir(exist_ok=False);verify(D/PARTS[0]);original={};merged={};owners={};input_proofs={}
    for folder in PARTS:
        path=D/folder;report=json.loads((path/'proposal.json').read_text('utf-8'));input_proofs[folder]=sha256((path/'proposal.json').read_bytes())
        for name,meta in report['files'].items():
            src=D/'inventory'/name
            if not src.exists():src=D/'ui_inventory'/name
            if not src.exists():src=D/'boss_intro_inventory'/name
            before=src.read_bytes();after=(path/name).read_bytes()
            if sha256(before)!=meta['before'] or sha256(after)!=meta['after'] or len(before)!=len(after):raise ValueError(f'Stale component {folder}/{name}')
            original[name]=before
            if name not in merged:merged[name]=after;owners[name]=[folder];continue
            if name in ('SLUS_005.61','MOJIPAT.ARC'):raise ValueError('Duplicate non-ARC mutation')
            base,proposed=psx_arc(before),psx_arc(after);current=merged[name]
            for a,z in zip(base,proposed):
                old=before[a['offset']:a['offset']+a['size']];new=after[z['offset']:z['offset']+z['size']]
                if old==new:continue
                if a['offset']!=z['offset'] or a['size']!=z['size']:raise ValueError('Second proposal changes entry bounds')
                if entry(current,int(a['type'],16))!=old:raise ValueError('Component entries overlap')
                current=replace_entry(current,int(a['type'],16),new)
            merged[name]=current;owners[name].append(folder)
    inv=json.loads((D/'inventory/inventory.json').read_text());files={}
    for name,raw in merged.items():
        (output/name).write_bytes(raw);files[name]={'before':sha256(original[name]),'after':sha256(raw),'size':len(raw),'components':owners[name]}
        if name.endswith('.ARC') and name!='MOJIPAT.ARC':psx_arc(raw)
    # Re-decode every translated page after UI integration, using the same
    # independently checked expected strings and font bitmaps.
    # Its verifier protects all non-text entries, so use the unmerged dialogue
    # verification as baseline and compare only the actual merged text bytes.
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        if entry(merged[name],0x15)!=entry((D/PARTS[0]/name).read_bytes(),0x15):raise ValueError('Integrated dialogue differs')
    report={'kind':'korean_localization_integrated_proposal','bin_applied':False,'runtime_verified':False,'approval_required':'54-byte dialogue renderer change and embedded helper','parent':str(PARENT.relative_to(ROOT)),'parent_sha256':PARENT_HASH,'source_sha256':SOURCE_HASH,'components':input_proofs,'files':files,'records':{n:inv['records'][n] for n in files},'coverage':{'dialogue_pages':543,'generic_menu_strings':110,'raster_ui_labels_including_armor_copies':67,'weapon_get_labels_across_two_resources':42,'stage_thumbnail_labels':20,'ending_narrative_sections':4,'creator_name_pixels_preserved':71090,'boss_intro_names':8,'boss_intro_descriptions':8},'remaining':['Actual emulator font uploads, page transitions, all menu palette states and regression tests','Audit other stage-intro names and movie-baked captions; movies remain out of scope','Korean linguistic review in scene context']}
    if digest(PARENT/'shibuki_riko.bin')!=PARENT_HASH or digest(ROOT/'MegaMan X4.bin')!=SOURCE_HASH:raise ValueError('Protected game input changed')
    (output/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'path':str(output),'files':len(files),'coverage':report['coverage'],'game_bin_written':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
