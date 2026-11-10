"""현재 BIN의 대기와 수정 대상 자세를 생성 참조로 보존한다. 입력은 읽기 전용."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_disc import file_hash

WORK = ROOT / 'work/sprite_style_unification_20261107'
SOURCES = {
 'ver_buki_riko': ('shibuki_riko', '21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a'),
 'ver_rin_nana': ('rin_nana', 'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720'),
}


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', 'utf8')


def main():
    WORK.mkdir(exist_ok=True)
    snapshot = WORK / 'protection_before.json'
    assert not snapshot.exists()
    prior = json.loads((ROOT / 'work/sprite_reaudit_20261106/final_validation.json').read_text('utf8'))
    names = set(prior['protected_files'])
    names.add('out/sprite_reaudit_20261106/ALL_SPRITES_CURRENT.html')
    sources = {}
    for mode, (stem, expected) in SOURCES.items():
        pointer = json.loads((ROOT / 'projects' / mode / 'current_build.json').read_text('utf8'))
        source = ROOT / pointer['build'] / (stem+'.bin')
        assert file_hash(source) == pointer['sha256'] == expected
        sources[mode] = {'bin': source.relative_to(ROOT).as_posix(), 'sha256': expected}
        names.update([source.relative_to(ROOT).as_posix(), source.with_suffix('.cue').relative_to(ROOT).as_posix(),
                      f'projects/{mode}/current_build.json', f'projects/{mode}/project.json'])
    # Read current user saves afresh; do not assume yesterday's F1 is unchanged.
    protected = {name: {'sha256': file_hash(ROOT/name), 'size': (ROOT/name).stat().st_size} for name in sorted(names)}
    write(snapshot, {'files': protected, 'sources': sources})
    art = WORK / 'shibuki/pilot01'
    art.mkdir(parents=True, exist_ok=False)
    source = ROOT / sources['ver_buki_riko']['bin']
    assets, _ = read_disc(source, ('PL02_U.ARC',))
    arc = Archive(assets['PL02_U.ARC'])
    # Unmodified, fixed native crop and nearest-neighbor display enlargement.
    box = (128,128,192,192)
    idle = arc.composite(0,15,2)[0]
    idle.save(art/'idle_native.png')
    idle.crop(box).resize((768,768),Image.Resampling.NEAREST).save(art/'idle_style_reference.png')
    refs = [11,13,1,17,33,71]
    sheet = Image.new('RGBA',(1536,1024))
    records = []
    for i, ref in enumerate(refs):
        pose = arc.composite(ref,15,2)[0]
        bounds = pose.getchannel('A').getbbox()
        assert bounds and bounds[0]>=box[0] and bounds[1]>=box[1] and bounds[2]<=box[2] and bounds[3]<=box[3]
        pose.save(art/f'current_{ref:03}.png')
        sheet.alpha_composite(pose.crop(box).resize((512,512),Image.Resampling.NEAREST),(i%3*512,i//3*512))
        records.append({'ref':ref,'cell':[i%3,i//3],'bounds':bounds,'native_sha256':file_hash(art/f'current_{ref:03}.png')})
    sheet.save(art/'motion_targets.png')
    write(art/'inputs.json', {'source':sources['ver_buki_riko'],'source_arc_sha256':__import__('hashlib').sha256(assets['PL02_U.ARC']).hexdigest(),
                            'form':'ultimate_before','idle_ref':0,'native_crop':list(box),'scale':8,'columns':3,'rows':2,'targets':records,
                            'input_images_are_unmodified_current_native_sprites':True,'generated_art_ready':False})
    print(json.dumps({'protected':len(protected),'pilot':str(art),'refs':refs}))


if __name__ == '__main__':
    main()
