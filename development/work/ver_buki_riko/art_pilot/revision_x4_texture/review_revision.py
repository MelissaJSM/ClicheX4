"""검토용 1배/3배 비교, 입력 보존 및 동일 재생성 검사. 게임에는 쓰지 않는다."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

root=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(root))
from scripts.project import load_project,inspect_references

parser=argparse.ArgumentParser()
parser.add_argument('--candidate',type=Path,required=True)
parser.add_argument('--repeat',type=Path,required=True)
args=parser.parse_args()
candidate=args.candidate.resolve();repeat=args.repeat.resolve()
assert candidate.is_relative_to(root/'out/ver_buki_riko')
assert repeat.is_relative_to(root/'out/ver_buki_riko')
previous=root/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z'
extracted=root/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
images=[Image.open(extracted/'idle_147.png').convert('RGBA'),
        Image.open(previous/'riko_idle147_rgba.png').convert('RGBA'),
        Image.open(candidate/'riko_idle147_rgba.png').convert('RGBA')]
labels=['원본 제로','이전 Riko','수정 Riko']
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',13)
card=Image.new('RGB',(624,316),(30,33,40));draw=ImageDraw.Draw(card)
draw.text((14,8),'원작과 같은 배율 비교 · 스타일 검토용 / 게임 적용 전',font=font,fill='white')
for i,(im,label) in enumerate(zip(images,labels)):
    x=12+i*208
    draw.text((x,40),label,font=font,fill=(231,235,243))
    draw.text((x,70),'1배',font=small,fill=(170,185,201))
    card.paste(im,(x+72,65),im)
    draw.text((x,131),'3배 · 최근접',font=small,fill=(170,185,201))
    enlarged=im.resize((168,144),Image.Resampling.NEAREST)
    card.paste(enlarged,(x+16,160),enlarged)
card.save(candidate/'revision_comparison_1x_3x.png')
im=Image.open(candidate/'riko_idle147_indexed.png')
rgba=im.convert('RGBA')
assert im.mode=='P' and im.size==(56,48) and im.info['transparency']==0
assert max(im.get_flattened_data())<=15
assert set(rgba.getchannel('A').get_flattened_data())=={0,255}
palette=im.getpalette()
for i in range(16):
    for c in palette[3*i:3*i+3]:
        assert c in {v*255//31 for v in range(32)}
assets=['riko_idle147_indexed.png','riko_idle147_rgba.png','riko_idle147.indices',
        'candidate_palette.bin','candidate_block.packed4','candidate_block.compressed',
        'comparison_1x.png','comparison_8x.png','background_composite_3x.png','palette_config.json']
same={name:hashlib.sha256((candidate/name).read_bytes()).hexdigest() for name in assets}
assert all((candidate/name).read_bytes()==(repeat/name).read_bytes() for name in assets)
refs={name:inspect_references(root,load_project(root,name)) for name in ('ver_buki_riko','ver_rin_nana')}
def sha_file(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
game_hash=sha_file(root/'MegaMan X4.bin')
assert game_hash=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
result={'created_utc':datetime.now(timezone.utc).isoformat(),'candidate':str(candidate),'repeat':str(repeat),
        'deterministic_assets':same,'original_bin_sha256':game_hash,'reference_checks':refs,
        'indexed_size':[56,48],'index_range_valid':True,'binary_alpha':True,'rgb555':True,
        'game_applied':False,'style_approved':False,'comparison_is_art_review':True}
(candidate/'revision_checks.local.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'candidate':str(candidate),'reproduced_assets':len(same),'game_hash':game_hash}))
