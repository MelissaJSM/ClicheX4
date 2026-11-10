"""Independent read-only inspection of the November 6 sprite proposals."""
from pathlib import Path
import hashlib, json, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets, composition_frame, decode_stream, indexed_atlas

OUT = Path(__file__).parent
PARENT = {
    'nana': ('ver_rin_nana', 'rin_nana', 'dcdf175eb93014da90d1bfb429774b48533e1c156e289a3ac49f969ea7a0f9c7'),
    'shibuki': ('ver_buki_riko', 'shibuki_riko', '8c1a2fa5b3f985be9945717d3d88776f2f4534030c42818843ec8093a3ce1a81'),
}
SKIP = {105, *range(175, 183)}
LAYER_ORDER = ((8, 8), (1, 5), (4, 7), (2, 6))

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', 'utf8')

def load(character, prepared, name):
    mode, stem, expected = PARENT[character]
    path = ROOT / f'out/{mode}/hurt_capsule_fix_20261106_v1/{stem}.bin'
    need(digest(path) == expected, 'Parent hash mismatch')
    with path.open('rb') as f:
        disc = DiscReader(f, path.stat().st_size)
        rec = next(r for r in disc.inspect()['files'] if r['name'] == name + ';1')
        old = disc.read(rec['lba'], rec['size'])
    proposal_path = ROOT / f'work/sprite_reaudit_20261106/{character}/{prepared}/proposal.json'
    proposal = json.loads(proposal_path.read_text('utf8'))
    spec = proposal['files'][name]
    output_path = ROOT / spec['path']
    new = output_path.read_bytes()
    need(path.resolve() != output_path.resolve(), 'Source-output collision')
    need(proposal['baseline_sha256'] == expected, 'Proposal parent mismatch')
    need(len(old) == len(new) == rec['size'], 'ARC length mismatch')
    need(sha(old) == spec['before'] and sha(new) == spec['after'], 'ARC hash mismatch')
    return old, new, {'parent': str(path.relative_to(ROOT)), 'parent_sha256': expected,
                     'proposal': str(proposal_path.relative_to(ROOT)), 'proposal_sha256': digest(proposal_path),
                     'arc': spec['path'], 'arc_before_sha256': sha(old), 'arc_after_sha256': sha(new)}

def part_records(c, bank, ref):
    return [tuple(p[k] for k in ('flags', 'tile', 'x', 'y')) for p in composition_frame(c, bank, ref)['parts']]

def unchanged_entries(old, new, allowed):
    fields = ('type', 'offset', 'size')
    need([tuple(r[k] for k in fields) for r in psx_arc(old)] ==
         [tuple(r[k] for k in fields) for r in psx_arc(new)], 'ARC entry directory changed')
    allowed_bytes = np.zeros(len(old), bool)
    for r in psx_arc(old):
        if int(r['type'], 16) in allowed:
            allowed_bytes[r['offset']:r['offset'] + r['size']] = True
        else:
            need(old[r['offset']:r['offset']+r['size']] == new[r['offset']:r['offset']+r['size']], 'Non-target ARC entry')
    delta = np.frombuffer(old, np.uint8) != np.frombuffer(new, np.uint8)
    need(not np.any(delta & ~allowed_bytes), 'ARC padding/header changed')
    return int(delta.sum())

def raw_and_gpu(before, after, refs):
    need(bank_offsets(before.g, allow_aliases=True) == bank_offsets(after.g, allow_aliases=True), 'Graphics bank layout')
    offsets = bank_offsets(before.g, allow_aliases=True)
    need(before.g[offsets[1]:] == after.g[offsets[1]:], 'Non-target graphics banks')
    unchanged = changed = gpu = 0
    for bi, (ob, nb) in enumerate(zip(before.banks, after.banks)):
        need(len(ob['frames']) == len(nb['frames']), 'Frame count')
        for of, nf in zip(ob['frames'], nb['frames']):
            ref = of['index']
            need(of['tile_count'] == nf['tile_count'], 'Tile count')
            a = decode_stream(before.g, of['offset'], of['limit'], of['tile_count']*128).data
            b = decode_stream(after.g, nf['offset'], nf['limit'], nf['tile_count']*128).data
            if bi != 0 or ref not in refs:
                need(a == b, f'Non-target decoded frame {bi}/{ref}')
                unchanged += 1
                continue
            need(nf['tile_count'] <= 32, '32-tile capacity')
            changed += int(a != b)
            aa = np.frombuffer(indexed_atlas(a, of['tile_count'])[0], np.uint8).reshape(-1, 256)
            bb = np.frombuffer(indexed_atlas(b, nf['tile_count'])[0], np.uint8).reshape(-1, 256)
            for bank in (0, 5, 6, 7, 8):
                old_records = part_records(before.c, bank, ref)
                for p in composition_frame(after.c, bank, ref)['parts']:
                    t = p['tile']; x = t % 16 * 16; y = t // 16 * 16
                    new_tile, old_tile = bb[y:y+16, x:x+16], aa[y:y+16, x:x+16]
                    bad = (t % 16 == 0 and new_tile[:, 0].any()) or (p['flip_y'] and t // 16 % 16 == 0 and new_tile[0].any())
                    if bad:
                        need(np.array_equal(new_tile, old_tile) and tuple(p[k] for k in ('flags','tile','x','y')) in old_records,
                             f'New GPU seam risk {ref}/{bank}/{t}')
                    gpu += 1
    return {'unchanged_decoded_references': unchanged, 'changed_decoded_references': changed,
            'checked_target_parts_for_gpu_seams': gpu, 'tile_capacity_and_counts_preserved': True}

def native_words(arc, layers, mask, arm):
    out = arc.words[layers[0]].copy()
    out[layers[0] == 0] = 0
    for bit, bank in LAYER_ORDER:
        if mask & bit:
            a = layers[bank]; occupied = a != 0
            offset = 32 if bank == 7 and arm == 2 else 16
            out[occupied] = arc.words[a[occupied] + offset]
    return out

def comparison(rows, path):
    images = [im for label, cols in rows for name, im in cols]
    boxes = [im.getbbox() for im in images if im.getbbox()]
    box = (min(b[0] for b in boxes)-3, min(b[1] for b in boxes)-3,
           max(b[2] for b in boxes)+3, max(b[3] for b in boxes)+3)
    scale = 4; w = (box[2]-box[0])*scale; h = (box[3]-box[1])*scale
    cw, ch = w+8, h+40
    board = Image.new('RGB', (cw*4, ch*len(rows)), '#bec9ce')
    draw = ImageDraw.Draw(board); font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 12)
    for j, (label, cols) in enumerate(rows):
        for i, (name, im) in enumerate(cols):
            x, y = i*cw, j*ch
            draw.text((x+3,y+2), label, fill='#182533', font=font)
            draw.text((x+3,y+18), name, fill='#182533', font=font)
            crop = im.crop(box).resize((w,h), Image.Resampling.NEAREST)
            board.paste(crop, (x,y+38), crop)
    board.save(path)

def nana():
    refs = set(range(120,126)) | {141,142}
    old, new, meta = load('nana', 'prepared_v1', 'PL00_U.ARC')
    byte_count = unchanged_entries(old, new, {2,3})
    before, after = Archive(old), Archive(new)
    report = raw_and_gpu(before, after, refs)
    cs = bank_offsets(before.c)
    need(cs == bank_offsets(after.c), 'Composition bank layout')
    need(before.c[:cs[5]] == after.c[:cs[5]] and before.c[cs[6]:] == after.c[cs[6]:], 'Other part bank changed')
    for bi in range(len(cs)):
        count = composition_frame(before.c, bi, 0)['bank_frame_count']
        need(count == composition_frame(after.c, bi, 0)['bank_frame_count'], 'Composition frame count')
        for ref in range(count):
            a, b = part_records(before.c,bi,ref), part_records(after.c,bi,ref)
            if bi == 5 and ref in refs:
                need(len(b) == len(a)+1 and b[:-1] == a and b[-1][0] == 0, 'Only one head part append permitted')
            else:
                need(a == b, 'Other geometry or draw order changed')
    count = same = base_full = layer_checks = 0; changed = []
    for ref in range(237):
        if ref in SKIP:
            continue
        old_layers, new_layers = {}, {}
        for bank in (0,5,6,7,8):
            a = before.layer(ref,bank)[0]; b = after.layer(ref,bank)[0]
            expected = a.copy()
            if ref in refs:
                source_bank = 6 if ref < 141 else 8
                if ref < 141:
                    y0 = -9 - (ref-120)//2
                    pts = [(x,y,3 if x==11 and y==y0+1 else 2) for y in (y0,y0+1) for x in (10,11,12)]
                else:
                    pts = [(11,-14,1),(11,-13,1)]
                for x,y,color in pts:
                    if bank == 5:
                        need(a[y+160,x+160] == 0, 'Head destination already occupied')
                        expected[y+160,x+160] = color
                    elif bank == source_bank:
                        need(a[y+160,x+160] == color, 'Source material mismatch')
                        expected[y+160,x+160] = 0
            need(np.array_equal(b,expected), f'Unexpected layer pixels {ref}/{bank}')
            old_layers[bank] = a; new_layers[bank] = b; layer_checks += 1
        for arm in (1,2):
            for mask in range(16):
                a = native_words(before,old_layers,mask,arm)
                b = native_words(after,new_layers,mask,arm)
                different = a != b; pixels = int(different.sum())
                if mask in (0,15):
                    need(pixels == 0, 'Basic/full armor image altered'); base_full += 1
                if pixels:
                    need(ref in refs, 'Non-target composite changed')
                    # A transfer only changes display when exactly one of its owners is present.
                    source_bit = 2 if ref < 141 else 8
                    need(bool(mask & 1) != bool(mask & source_bit), 'Unexpected mask ownership change')
                    changed.append({'ref':ref,'mask':mask,'arm':arm,'pixel_count':pixels})
                else:
                    same += 1
                count += 1
    sheets=[]
    for batch, subset in enumerate((range(120,124),(124,125,141,142))):
        rows=[]
        for ref in subset:
            mask=2 if ref<141 else 8
            rows.append((f'ref {ref} / owner {mask}', [('before owner',before.composite(ref,mask)[0]),('after owner',after.composite(ref,mask)[0]),('before head only',before.composite(ref,1)[0]),('after head only',after.composite(ref,1)[0])]))
        path=OUT/f'nana_independent_{batch}.png';comparison(rows,path);sheets.append(str(path.relative_to(ROOT)))
    report.update(meta)
    report.update(passed=True, changed_arc_bytes=byte_count, palette_timing_audio_non_target_entries_exact=True,
                  layer_checks=layer_checks, all_mask_arm_composites=count, unchanged_composites=same,
                  base_full_preserved_composites=base_full, changed_composites=changed,
                  only_existing_pixels_transferred=True, comparison_sheets=sheets,
                  scope='나나 기본·포스 공용 자원에서 베일 조각의 소유 레이어만 교정. 신규 그림·좌표·타이밍 변경 없음.',
                  runtime_verified=False, visual_review_recorded_separately=True)
    write(OUT/'nana_prepared_independent.json',report)
    print(json.dumps({k:report[k] for k in ('passed','all_mask_arm_composites','unchanged_composites','base_full_preserved_composites')},ensure_ascii=False),flush=True)

def shibuki(prepared):
    allowed = set(range(11,17)) | set(range(33,85))
    old,new,meta = load('shibuki',prepared,'PL02_U.ARC')
    byte_count=unchanged_entries(old,new,{2})
    before,after=Archive(old),Archive(new)
    report=raw_and_gpu(before,after,allowed)
    layer_changes=[]; changed_composites=[]; composites=0; actual_refs=set()
    for ref in range(237):
        if ref in SKIP:continue
        old_layers={b:before.layer(ref,b)[0] for b in (0,5,6,7,8)}
        new_layers={b:after.layer(ref,b)[0] for b in (0,5,6,7,8)}
        base_change=old_layers[0]!=new_layers[0]
        opaque=old_layers[0]>0
        padded=np.pad(opaque,1)
        inside=opaque & padded[:-2,1:-1] & padded[2:,1:-1] & padded[1:-1,:-2] & padded[1:-1,2:]
        need(not np.any(base_change & ~inside),'Outer contour or alpha changed')
        if base_change.any():
            yy,xx=np.nonzero(base_change)
            need(ref in allowed and min(xx)>=144 and max(xx)<182 and min(yy)>=167 and max(yy)<=182,
                 'Material change outside lower leg region')
            need(set(new_layers[0][base_change].tolist())<=set((5,8,9,11,12,13)), 'Unexpected material indices')
        for bank in (0,5,6,7,8):
            a,b=old_layers[bank],new_layers[bank];diff=a!=b
            need(np.array_equal(a>0,b>0),'Layer transparency changed')
            if diff.any():
                need(ref in allowed,'Non-target layer changed')
                need(not np.any(diff & ~base_change),f'Overlay changed outside base material correction {ref}/{bank}: '+str(np.argwhere(diff & ~base_change).tolist()))
                need(np.array_equal(b[diff],new_layers[0][diff]),'Overlay material not aligned with base')
                actual_refs.add(ref)
                layer_changes.append({'ref':ref,'bank':bank,'pixels':int(diff.sum())})
        if ref in (73,74):
            # The native dash-streak deltas must remain intact.
            effect=before.layer(ref,0)[0]!=before.layer(ref-2,0)[0]
            need(not np.any(base_change & effect),'Dash particle/streak pixels changed')
        for arm in (1,2):
            for mask in range(16):
                a=native_words(before,old_layers,mask,arm)
                b=native_words(after,new_layers,mask,arm)
                diff=a!=b
                need(not np.any(diff & ~base_change),'Composite changed outside material pixels')
                need(np.array_equal(a!=0,b!=0),'Composite transparency changed')
                if diff.any():changed_composites.append({'ref':ref,'mask':mask,'arm':arm,'pixels':int(diff.sum())})
                composites+=1
    sheets=[]
    for i,start in enumerate(range(0,len(actual_refs),6)):
        rows=[]
        for ref in sorted(actual_refs)[start:start+6]:
            rows.append((f'ref {ref}', [('pre before',before.composite(ref,15)[0]),('pre revised',after.composite(ref,15)[0]),
                                      ('post before',before.composite(ref,0)[0]),('post revised',after.composite(ref,0)[0])]))
        path=OUT/f'shibuki_independent_{i:02}.png';comparison(rows,path);sheets.append(str(path.relative_to(ROOT)))
    report.update(meta)
    report.update(passed=True,changed_arc_bytes=byte_count,actual_changed_refs=sorted(actual_refs),
                  composition_palette_timing_audio_other_entries_exact=True,alpha_outer_contour_exact=True,
                  all_mask_arm_composites=composites,changed_composites=changed_composites,layer_changes=layer_changes,
                  comparison_sheets=sheets,runtime_verified=False,visual_review_recorded_separately=True,
                  scope='시부키 얼티밋의 하체 재질만 교정. 원래 외곽·투명도·머리·몸체·팔·좌표·입자 보존.')
    write(OUT/'shibuki_prepared_independent.json',report)
    print(json.dumps({'passed':True,'refs':len(actual_refs),'composites':composites,'sheets':len(sheets)}),flush=True)

def nana_frost():
    old,new,meta=load('nana','prepared_frost_v1','PL02_U.ARC')
    byte_count=unchanged_entries(old,new,{2})
    before,after=Archive(old),Archive(new)
    report=raw_and_gpu(before,after,{95,96})
    directory=ROOT/'work/sprite_reaudit_20261106/nana/frost'
    material_path=directory/'material_v2.json'
    material=json.loads(material_path.read_text('utf8'))
    authored=np.array(Image.open(directory/'authored_095_indices.png'))
    need(sha(authored.tobytes())==material['reused_authored_indexed_sha256'],'Authored indexed source hash')
    need(digest(ROOT/'work/ver_rin_nana/nana_ultimate_armor/frost_pose_v2/generated.png')==material['source_sha256'],'Original authored source hash')
    need(len(material['changes'])==material['changed_count']==36,'Material scope')
    for q in material['changes']:
        x,y=q['world'];sx,sy=q['authored_world']
        need(0<=y<=15 and sy==y and q['after'] in (11,12),'Only authored calf skin in same scanline')
        need(int(authored[sy+160,sx+160])==q['after'],'Authored source shade')
        lo,hi=q['target_leg_span_world']
        need(lo<x<hi,'Silhouette row endpoint changed')
    old95=before.banks[0]['frames'][95];new95=after.banks[0]['frames'][95]
    need(before.banks[0]['frames'][96]['offset']==old95['offset'] and
         after.banks[0]['frames'][96]['offset']==new95['offset'],'95/96 shared stream changed')
    layer_changes=[]; changed_composites=0; total=0
    for ref in range(237):
        if ref in SKIP:continue
        old_layers={b:before.layer(ref,b)[0] for b in (0,5,6,7,8)}
        new_layers={b:after.layer(ref,b)[0] for b in (0,5,6,7,8)}
        for bank in (0,5,6,7,8):
            a,b=old_layers[bank],new_layers[bank];want=a.copy()
            if ref in (95,96) and bank in (0,5):
                for q in material['changes']:
                    x,y=q['world'];x+=ref-95
                    if want[y+160,x+160]:
                        need(want[y+160,x+160] in (1,2,3,4),'Expected dark interior')
                        want[y+160,x+160]=q['after']
            need(np.array_equal(b,want),f'Unexpected Frost layer {ref}/{bank}')
            need(np.array_equal(a>0,b>0),'Frost alpha altered')
            if np.any(a!=b):layer_changes.append({'ref':ref,'bank':bank,'pixels':int((a!=b).sum())})
        for arm in (1,2):
            for mask in range(16):
                a=native_words(before,old_layers,mask,arm)
                b=native_words(after,new_layers,mask,arm);want=a.copy()
                if ref in (95,96):
                    for q in material['changes']:
                        x,y=q['world'];want[y+160,x+160+ref-95]=before.words[q['after']]
                need(np.array_equal(b,want),'Frost composite differs from 36 authored material replacements')
                changed_composites+=int(np.any(a!=b));total+=1
    rows=[]
    for ref in (95,96):
        rows.append((f'ref {ref}', [('pre before',before.composite(ref,15)[0]),('pre revised',after.composite(ref,15)[0]),
                                  ('post before',before.composite(ref,0)[0]),('post revised',after.composite(ref,0)[0])]))
    path=OUT/'nana_frost_independent.png';comparison(rows,path)
    report.update(meta)
    report.update(passed=True,changed_arc_bytes=byte_count,all_mask_arm_composites=total,changed_composites=changed_composites,
                  layer_changes=layer_changes,material_source_manifest_sha256=digest(material_path),
                  composition_palette_timing_audio_other_entries_exact=True,alpha_coordinates_shoes_row_endpoints_exact=True,
                  comparison_sheets=[str(path.relative_to(ROOT))],runtime_verified=False,visual_review_recorded_separately=True,
                  scope='나나 얼티밋 프로스트 실드 95/96의 뒤 종아리 내부 36픽셀을 같은 자세의 기존 원화 피부 명암으로 복원.')
    write(OUT/'nana_frost_independent.json',report)
    print(json.dumps({'passed':True,'composites':total,'changed_composites':changed_composites}),flush=True)

if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='shibuki':shibuki(sys.argv[2])
    elif len(sys.argv)>1 and sys.argv[1]=='frost':nana_frost()
    else:nana()
