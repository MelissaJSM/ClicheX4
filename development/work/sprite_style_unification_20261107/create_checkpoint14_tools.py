"""Create versioned guards without changing code bound by older frozen assets."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
W = Path(__file__).resolve().parent

def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)

def write_new(path, text):
    if path.exists():
        assert path.read_text('utf8') == text
    else:
        path.write_text(text, 'utf8')

code = (ROOT / 'scripts/build_sprite_style_unification.py').read_text('utf8')
code = replace_once(code, 'def check_selection(old, new, sync_zero=False, preserve_x=False):',
                    'def check_selection(old, new, sync_zero=False, preserve_x=False, sync_beam=False):')
code = replace_once(code, "    before, after = entry(old, 0x10102), entry(new, 0x10102)",
    "    builder.require(type(sync_beam) is bool and not (sync_beam and preserve_x), 'Invalid beam scope')\n"
    "    allowed_x = (18, 19, 20, 21, 23) if sync_beam else (18, 19, 20, 21)\n"
    "    before, after = entry(old, 0x10102), entry(new, 0x10102)")
code = replace_once(code, 'if preserve_x or ref not in (18, 19, 20, 21):', 'if preserve_x or ref not in allowed_x:')
code = replace_once(code, "        else:\n            builder.require({v['clut'] for v in p['parts']}",
    "        else:\n            if ref == 23:\n"
    "                builder.require(len(p['parts']) == len(q['parts']), 'Beam part count changed')\n"
    "                for old_part, new_part in zip(p['parts'], q['parts']):\n"
    "                    # Earlier reviewed X body packing changed record locations.\n"
    "                    # The beam-only preparation separately preserves v13 offsets.\n"
    "                    builder.require(all(old_part[k] == new_part[k] for k in ('flip_x', 'flip_y', 'clut')), 'Beam part semantics changed')\n"
    "            builder.require({v['clut'] for v in p['parts']}")
code = replace_once(code, "    for ref, body in ((18, 207), (19, 156), (20, 157), (21, 158)):",
    "    mapping = [(18, 207), (19, 156), (20, 157), (21, 158)]\n"
    "    if plan.get('sync_shibuki_selection_beam', False):\n"
    "        builder.require(plan['project'] == 'ver_buki_riko', 'Beam origin requires BR mapping')\n"
    "        mapping.append((23, 160))\n"
    "    for ref, body in mapping:")
code = replace_once(code, 'if ref in (18, 19, 20):', 'if ref in (18, 19, 20, 23):')
code = replace_once(code, '(x, y-1) if ref == 18 else (319-x, y+1)', '(x, y-1) if ref in (18, 23) else (319-x, y+1)')
code = replace_once(code, "    preserve_x=plan.get('preserve_x_selection',False)",
    "    preserve_x=plan.get('preserve_x_selection',False)\n"
    "    sync_beam=plan.get('sync_shibuki_selection_beam',False)\n"
    "    builder.require(type(sync_beam) is bool, 'Invalid beam scope')\n"
    "    builder.require(not sync_beam or (plan['project']=='ver_buki_riko' and not preserve_x and 'ST0E_U1.ARC' in plan['resources']), 'Missing or conflicting beam scope')")
code = replace_once(code, 'check_selection(old, new, sync_zero, preserve_x)', 'check_selection(old, new, sync_zero, preserve_x, sync_beam)')
code = replace_once(code, "= [] if preserve_x else [18, 19, 20, 21]", "= [] if preserve_x else ([18, 19, 20, 21, 23] if sync_beam else [18, 19, 20, 21])")
code = replace_once(code, "            result['x_selection_all_bytes_preserved'] = preserve_x",
    "            result['shibuki_beam23_player160_origin_exact'] = sync_beam\n"
    "            result['x_selection_all_bytes_preserved'] = preserve_x")
code = '# Versioned extension: preserve the v1 file and its frozen hashes.\n' + code
write_new(ROOT / 'scripts/build_sprite_style_selection_v2.py', code)

prep = (W / 'prepare_checkpoint13.py').read_text('utf8')
prep = replace_once(prep, "f'staging_{a.mode}_v12.json'", "f'staging_{a.mode}_v13.json'")
prep = prep.replace('20261107_v13', '20261107_v14').replace('checkpoint_13', 'checkpoint_14')
prep = replace_once(prep, "dest = W / f'staging_{a.mode}_v13.json'", "dest = W / f'staging_{a.mode}_v14.json'")
prep = replace_once(prep, "assert 'ST0E_U1.ARC' in seen, 'New Zero selection body copies required'",
    "plan['sync_shibuki_selection_beam'] = (a.mode == 'br')\n"
    "if a.mode == 'br':\n"
    "    assert 'ST0E_U1.ARC' in seen, 'New Shibuki beam copy required'\n"
    "guard = ROOT / 'scripts/build_sprite_style_selection_v2.py'\n"
    "plan['integration_guard'] = {'path': guard.relative_to(ROOT).as_posix(), 'sha256': sha(guard)}")
write_new(W / 'prepare_checkpoint14.py', prep)
print('Created versioned selection guard and checkpoint 14 preparer; previous files unchanged.')
