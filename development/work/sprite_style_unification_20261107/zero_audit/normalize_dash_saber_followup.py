"""질풍아 후속 원화를 고정 셀·팔레트로 정규화한다. 자동 위치 보정 없음."""
from pathlib import Path
import argparse, hashlib, json, struct, sys
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.prepare_rin_run import quantize, connected_groups
from scripts.overhaul_sprites_audit import render, rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--page', type=int, choices=(1, 2), required=True); ap.add_argument('--local-legs', action='store_true'); args = ap.parse_args()
    d = Path(__file__).parent / 'rin_extension' / f'dash_saber_followup{args.page:02}'
    if args.local_legs: d = d/'local_legs01'
    info = json.loads((d/'inputs.json').read_text('utf8')); source = ROOT/info['actual_input_arc']
    assert digest(source) == info['archive_sha256']; arc = source.read_bytes()
    src = d/'generated.png'; im = Image.open(src).convert('RGBA')
    assert im.width == im.height and im.getchannel('A').getextrema() == (0, 255)
    out = d/'native_fixed'; assert not out.exists(); out.mkdir()
    pal = info['palette_words']; black = struct.unpack_from('<16H', entry(arc, 9), 13*32)
    assert list(struct.unpack_from('<16H', entry(arc, 9))) == pal
    colors = np.array([[(w >> s & 31)*255//31 for s in (0,5,10)] for w in pal[1:]], np.int32)
    cw = im.width/2; scale = 96/cw; rows = []; items = {k:[] for k in ('normal','black')}
    for f in info['frames']:
        key = f['key']; x, y = f['cell']; crop = im.crop((round(x*cw),round(y*cw),round((x+1)*cw),round((y+1)*cw)))
        a = quantize(crop, colors, scale); assert a.shape == (96,96)
        z = np.zeros((384,384),np.uint8); x0,y0,x1,y1 = info['crop']; z[y0:y1,x0:x1] = a
        old = render(arc,f['bank'],f['bank']*5,f['ref'])[0]
        dst = out/(key+'_indices.png'); Image.fromarray(z).save(dst)
        for name, words in [('normal',pal),('black',black)]:
            rgba(z,words).save(out/(name+'_'+key+'.png'))
            items[name].extend([(key+' original',rgba(old,words)),(key+' fixed native',rgba(z,words))])
        rows.append({**f,'old_bbox':rgba(old,pal).getbbox(),'new_bbox':rgba(z,pal).getbbox(),
                     'old_floor':int(np.nonzero(old)[0].max()),'new_floor':int(np.nonzero(z)[0].max()),
                     'opaque_pixels':int(np.count_nonzero(z)),'components':[len(g) for g in connected_groups(z>0)],
                     'output_sha256':digest(dst),'translation':[0,0]})
    for name, words in [('normal',pal),('black',black)]:
        page(items[name],rgba(render(arc,0,0,147)[0],words),out/(name+'_comparison.png'),cols=2,scale=5)
    result={'source_art':str(src.relative_to(ROOT)),'source_art_sha256':digest(src),'source_size':im.size,
            'archive_sha256':digest(source),'fixed_grid':True,'scale':scale,'records':rows,
            'old_art_override':False,'candidate_only':True,'game_modified':False}
    (out/'registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(rows))

if __name__ == '__main__': main()
