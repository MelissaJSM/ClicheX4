"""Prepare only reviewable extracted resources and a labelled native preview."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D,messages
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import sha256
from src.psx_korean_font import font_cache_proposal
from src.psx_korean_text import build_dialogue,replace_text_same_capacity,glyph_bitmap

PILOT=[['헌터 본부','5567지점에 이레귤러가','출현했다!'],['헌터 본부','스카이 라군을 점거했다!'],['헌터 본부','레플리포스의 소행으로','보인다!'],['유즈하 리코','레플리포스라고?','알겠어. 지금 출동한다.']]

def main():
    dest=D/'pilot_proposal_v2';dest.mkdir(exist_ok=False);files={};reports={}
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        old=(D/'inventory'/name).read_bytes();source=entry(old,0x15)
        text,report=build_dialogue(source,messages(source),{25:PILOT} if name=='PL01_U.ARC' else {})
        new=replace_text_same_capacity(old,text);(dest/name).write_bytes(new)
        files[name]={'before':sha256(old),'after':sha256(new),'size':len(new)};reports[name]=report
    exe=(D/'inventory/SLUS_005.61').read_bytes();new,report=font_cache_proposal(exe)
    (dest/'SLUS_005.61').write_bytes(new);files['SLUS_005.61']={'before':sha256(exe),'after':sha256(new),'size':len(new)}
    im=Image.new('RGB',(320,112),(8,18,34));d=ImageDraw.Draw(im)
    d.rectangle((32,12,288,80),fill=(4,33,74),outline=(120,211,232),width=2)
    from src.psx_korean_text import LEGACY
    from scripts.inventory_korean import decode
    # Preview font only, not an emulator capture.
    for row,line in enumerate(PILOT[3]):
        for col,char in enumerate(line):
            if char==' ':continue
            bits=int.from_bytes(glyph_bitmap(char),'little')
            for y in range(12):
                for x in range(12):
                    if bits>>(y*12+x)&1:im.putpixel((40+col*12+x,20+row*18+y),(245,245,245))
    d.text((35,90),'FONT PREVIEW - NOT IN-GAME',font=ImageFont.load_default(),fill='white')
    im.save(dest/'font_preview_native.png');im.resize((960,336),Image.Resampling.NEAREST).save(dest/'font_preview_3x.png')
    result={'kind':'korean_pilot_proposal','bin_applied':False,'files':files,'dialogue':reports,'exe':report}
    (dest/'proposal.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'path':str(dest),'sizes':{n:r['size'] for n,r in reports.items()},'font':reports['PL01_U.ARC']['glyph_count'],'exe_changed_bytes':report['changed_bytes']}))

if __name__=='__main__':main()
