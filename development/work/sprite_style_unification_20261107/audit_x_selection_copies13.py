"""Read-only compare current X UI copies with the corresponding player poses."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_sprite_style_album import selection_image
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
MAPPING={0:0,1:85,2:86,3:87,4:88,5:89,6:90,7:91,8:92,18:207,19:156,20:157,21:158,22:159,23:160,24:161}
sha=lambda b:hashlib.sha256(b).hexdigest()
reports=[]
for mode,char,stem in [('ver_buki_riko','shibuki','shibuki_riko'),('ver_rin_nana','nana','rin_nana')]:
    game=ROOT/'out'/mode/'sprite_style_unification_20261107_v13'/f'{stem}.bin'
    manifest=json.loads((game.parent/'manifest.json').read_text('utf8'))
    assert sha(game.read_bytes())==manifest['modified_bin']['sha256']
    assets=read_disc(game,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0]
    model=Archive(assets['PL00_U.ARC']);out=W/'x_selection_audit13'/char
    assert not out.exists();out.mkdir(parents=True)
    rows=[];pairs=[]
    for ref,body in MAPPING.items():
        ui=selection_image(assets,{'bank':2,'ref':ref})
        im=model.composite(body,0)[0]
        if ref in (19,20):
            a=np.array(im);b=np.zeros_like(a);yy,xx=np.where(a[:,:,3]>0)
            b[yy,319-xx]=a[yy,xx];im=Image.fromarray(b)
        ub,bb=ui.getbbox(),im.getbbox()
        equal=ui.crop(ub).size==im.crop(bb).size and ui.crop(ub).tobytes()==im.crop(bb).tobytes()
        rows.append({'ui_ref':ref,'body_ref':body,'mirrored_x':ref in (19,20),
            'same_rgba_ignoring_translation':equal,'ui_bbox':ub,'body_bbox':bb,
            'exact_translation_if_same':[ub[0]-bb[0],ub[1]-bb[1]] if equal else None})
        if not equal:pairs.append((ref,body,ui,im))
    pages=[]
    for start in range(0,len(pairs),4):
        group=pairs[start:start+4];board=Image.new('RGB',(960,354*len(group)),'#303d4a');draw=ImageDraw.Draw(board)
        for j,(ref,body,ui,im) in enumerate(group):
            for col,source in enumerate([ui,im]):
                pic=source.crop((80,90,240,200)).resize((480,330),Image.Resampling.NEAREST)
                board.paste(pic,(col*480,j*354+24),pic)
            draw.text((4,j*354+5),f'{char} select {ref} | current player {body} (original coordinates)',fill='white')
        p=out/f'comparison_{start//4:02}.png';board.save(p);pages.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())})
    result={'mode':mode,'character':char,'disc_sha256':manifest['modified_bin']['sha256'],
        'asset_sha256':{n:sha(v) for n,v in assets.items()},'rows':rows,
        'content_difference_count':sum(not r['same_rgba_ignoring_translation'] for r in rows),
        'comparison_pages':pages,'game_assets_modified':False,'runtime_checked':False,
        'limits':'도형/색상 동일 여부와 좌표를 분리한 읽기 전용 조사. 기존 UI의 고유 위치차이를 오류로 단정하지 않음. 전체 제작 후 동기화 검증 대상.'}
    (out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    reports.append({'character':char,'mapped':len(rows),'different':result['content_difference_count'],'pages':len(pages)})
print(json.dumps(reports))
