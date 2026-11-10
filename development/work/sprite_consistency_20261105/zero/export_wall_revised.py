"""동결된 리코 벽 수정 ARC를 별도 갤러리로 내보낸다. 기준 갤러리와 게임은 읽기 전용."""
from pathlib import Path
import json
import struct
import sys
import shutil
import hashlib
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from scripts.export_zero_consistency import write
from scripts.prepare_riko_consistency_wall import TARGETS
from src.psx_disc import file_hash

WORK=ROOT/'work/sprite_consistency_20261105/zero'
BASE=ROOT/'out/sprite_consistency_20261105/riko'
OUT=ROOT/'out/sprite_consistency_20261105/revised/riko'
FIX=WORK/'riko/wall_fix'
ARC_SHA='36e231a882be87d71d603667a26909025003b88908f939f115d328b0dd4d53dc'
SOURCE_ARC_SHA='d5720842fa16d9eed2b53c77c159656be444023943f8400d11cec4551876d17d'


def main():
    if OUT.exists():
        raise ValueError('Fresh revised output required')
    arc_path=FIX/'prepared_v1/PL01_U.ARC'
    original_path=WORK/'riko/PL01_U.ARC'
    assert file_hash(arc_path)==ARC_SHA
    assert file_hash(original_path)==SOURCE_ARC_SHA
    before=original_path.read_bytes();after=arc_path.read_bytes()
    assert entry(before,9)==entry(after,9)
    frames=[]
    for bank,refs in TARGETS.items():
        for ref in refs:
            old,_=render(before,bank,0 if bank==0 else 5,ref)
            new,_=render(after,bank,0 if bank==0 else 5,ref)
            assert old.shape==new.shape==(384,384)
            assert new.max()<16
            frames.append((f'b{bank}_{ref:03}',bank,ref,old,new))
    originals={}
    for variant in ('normal','black'):
        for ident,*_ in frames:
            p=BASE/variant/'native'/f'{ident}.png'
            originals[p]=file_hash(p)
    OUT.mkdir(parents=True)
    mapping={};details=[];sheets=[]
    for variant,row in (('normal',0),('black',13)):
        folder=OUT/variant;folder.mkdir()
        words=struct.unpack_from('<16H',entry(after,9),row*32)
        # Whole-pose common viewport, not per-frame rescaling/recentering.
        # Cropped only for contact sheets; native images retain all 384 pixels.
        viewport=(128,124,192,192)
        cell=(256,160);sheet=Image.new('RGB',(cell[0]*4,cell[1]*4),'#263442')
        draw=ImageDraw.Draw(sheet)
        for idx,(ident,bank,ref,old,new) in enumerate(frames):
            baseline=BASE/variant/'native'/f'{ident}.png'
            old_rgba=rgba(old,words);new_rgba=rgba(new,words)
            assert np.array_equal(np.array(Image.open(baseline).convert('RGBA')),np.array(old_rgba))
            path=folder/f'{ident}.png';new_rgba.save(path)
            reopened=Image.open(path)
            assert reopened.mode=='RGBA' and reopened.size==(384,384)
            assert np.array_equal(np.array(reopened),np.array(new_rgba))
            key=f'{variant}:{ident}';relative=path.relative_to(ROOT).as_posix()
            mapping[key]=relative
            details.append({'id':key,'frame_id':ident,'graphics_bank':bank,'parts_bank':0 if bank==0 else 5,
                'frame':ref,'palette_row':row,'baseline_png':baseline.relative_to(ROOT).as_posix(),
                'baseline_png_sha256':originals[baseline],'revised_png':relative,
                'revised_png_sha256':file_hash(path),'size':[384,384],'origin':[160,160],
                'frame_scaling':False,'prepared_arc_sha256':ARC_SHA,
                'index_pixels_sha256':hashlib.sha256(new.tobytes()).hexdigest()})
            xx=idx%4*cell[0];yy=idx//4*cell[1]
            draw.text((xx+3,yy+3),f'{variant} {ident} before / revised',fill='white')
            for col,im in enumerate((old_rgba,new_rgba)):
                box=im.getbbox()
                assert box is not None and box[0]>=viewport[0] and box[1]>=viewport[1] and box[2]<=viewport[2] and box[3]<=viewport[3],(ident,box)
                thumb=im.crop(viewport).resize((128,136),Image.Resampling.NEAREST)
                sheet.paste(thumb,(xx+col*128,yy+24),thumb)
        sheet_path=OUT/f'comparison_{variant}.png';sheet.save(sheet_path)
        sheets.append({'variant':variant,'path':sheet_path.relative_to(ROOT).as_posix(),
                       'scale':2,'world_viewport':[-32,-36,32,32],'whole_opaque_pose_preserved':True})
    for path,expected in originals.items():
        assert file_hash(path)==expected
    assert file_hash(arc_path)==ARC_SHA
    assert file_hash(original_path)==SOURCE_ARC_SHA
    for source,name in ((BASE/'report.json','audit_report.json'),(FIX/'verification.json','verification.json'),
                        (FIX/'prepared_v1/normal_black_review.png','idle_before_after.png')):
        shutil.copyfile(source,OUT/name)
    result={'schema':'sprite_consistency_revised_mapping_v1','character':'riko',
        'baseline_manifest':'out/sprite_consistency_20261105/riko/manifest.json',
        'source_bin_sha256':'bedba81a4c1263388835e10f57a8e30f6b7e9d9ac6f3f3d3dbf77821f4fb7c08',
        'prepared_arc':arc_path.relative_to(ROOT).as_posix(),'prepared_arc_sha256':ARC_SHA,
        'canvas':{'width':384,'height':384,'origin':[160,160],'per_frame_scaling':False},
        'frames':mapping,'frame_details':details,'count':len(mapping),
        'sheets':sheets,'reports':{'audit':'out/sprite_consistency_20261105/revised/riko/audit_report.json',
          'verification':'out/sprite_consistency_20261105/revised/riko/verification.json',
          'rin_unchanged_review':'out/sprite_consistency_20261105/rin/report.json'},
        'baseline_pngs_preserved':True,'game_bin_written_by_exporter':False,'runtime_verified':False}
    write(OUT/'mapping.json',result)
    (OUT/'README.md').write_text('''# 리코 벽 동작 수정 표시 자료

기존 갤러리를 덮어쓰지 않고 동결된 수정 후보 ARC에서 normal/black 각각16장, 총32장을 내보냈다. 모두384×384 RGBA, 원점(160,160)이며 개별 확대나 중심 재정렬이 없다.

`mapping.json`의 `frames`는 기존 갤러리 ID(`normal:b0_038`)에서 프로젝트 루트 기준 수정 PNG 경로로 연결된다. `frame_details`에는 두 이미지 해시·뱅크·프레임·팔레트·원점이 있다. 기존 기준 PNG32장의 해시는 전후 동일하다.

- [일반색16프레임 전후](comparison_normal.png)
- [블랙색16프레임 전후](comparison_black.png)
- [대기와 나란히 비교](idle_before_after.png)
- [전체 리코 감사](audit_report.json)
- [수정 ARC 검증](verification.json)
- [린 검토 범위·새 수정 없음](../../rin/report.json)

비교 시트는2배 최근접 확대이며 전체 불투명 포즈가 뷰포트 안에 있는지 검사했다. 원본 크기 PNG는 각 색상 폴더에 있다. 이 자료는 정적 복원·수정 후보 표시이며 실제 BIN 적용 또는 실기 수용을 뜻하지 않는다.
''',encoding='utf-8')
    print(json.dumps({'mapping':str(OUT/'mapping.json'),'frames':len(mapping),'baseline_preserved':True}))


if __name__=='__main__':
    main()
