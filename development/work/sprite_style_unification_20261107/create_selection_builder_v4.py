"""Version the approved selection8 scope without mutating frozen v2/v3 code."""
from pathlib import Path
import ast
W=Path(__file__).resolve().parent;ROOT=W.parents[1];s=(ROOT/'scripts/build_sprite_style_selection_v2.py').read_text('utf8')
changes=[
('def check_selection(old, new, sync_zero=False, preserve_x=False, sync_beam=False):','def check_selection(old, new, sync_zero=False, preserve_x=False, sync_beam=False, sync_standing=False):'),
("    allowed_x = (18, 19, 20, 21, 23) if sync_beam else (18, 19, 20, 21)","    builder.require(type(sync_standing) is bool and not(sync_standing and preserve_x), 'Invalid standing scope')\n    allowed_x = ((18, 19, 20, 21, 23) if sync_beam else (18, 19, 20, 21)) + (tuple(range(1,9)) if sync_standing else ())"),
("    sync_beam=plan.get('sync_shibuki_selection_beam',False)","    sync_beam=plan.get('sync_shibuki_selection_beam',False)\n    sync_standing=plan.get('sync_x_selection_standing',False)\n    builder.require(type(sync_standing) is bool, 'Invalid standing scope')\n    builder.require(not sync_standing or (plan['project']=='ver_buki_riko' and not preserve_x and 'ST0E_U1.ARC' in plan['resources']), 'Unmeasured or conflicting standing origin')"),
('check_selection(old, new, sync_zero, preserve_x, sync_beam)','check_selection(old, new, sync_zero, preserve_x, sync_beam, sync_standing)'),
("result['selection_bank2_allowed_frames'] = [] if preserve_x else ([18, 19, 20, 21, 23] if sync_beam else [18, 19, 20, 21])","result['selection_bank2_allowed_frames'] = [] if preserve_x else sorted(([18, 19, 20, 21, 23] if sync_beam else [18, 19, 20, 21]) + (list(range(1,9)) if sync_standing else []))\n            result['standing_selection85_92_origin_exact'] = sync_standing")]
for a,b in changes:
 assert s.count(a)==1,a;s=s.replace(a,b)
lo=s.index('def check_selection_body(plan):');hi=s.index('def check_static_body(',lo)
replacement='''def check_selection_body(plan):
    """Keep v3 version-specific ceremony origins and add measured BR shooting8."""
    from scripts.build_sprite_style_selection_v3 import check_selection_body as check_ceremonies
    from scripts.export_x_consistency import Archive
    from scripts.build_sprite_style_album import selection_image
    from scripts.c01_audio_build import read_disc
    check_ceremonies(plan)
    enabled=plan.get('sync_x_selection_standing',False)
    builder.require(type(enabled) is bool,'Invalid standing scope')
    if not enabled:return
    builder.require(plan['project']=='ver_buki_riko','Unmeasured standing origin')
    source=ROOT/plan['source_bin']
    builder.require(builder.file_hash(source)==plan['source_sha256'],'Standing source hash mismatch')
    assets=read_disc(source,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0]
    for name in assets:
        if name in plan['resources']:
            row=plan['resources'][name];data=(ROOT/row['path']).read_bytes()
            builder.require(builder.sha(data)==row['after'],'Standing resource hash mismatch')
            assets[name]=data
    model=Archive(assets['PL00_U.ARC'])
    for ref,dy in enumerate((-1,0,0,0,0,-1,-2,0),1):
        picture=np.array(model.composite(ref+84,0)[0]);expected=np.zeros_like(picture)
        yy,xx=np.where(picture[:,:,3]>0);ty=yy+dy
        builder.require(bool(np.all((ty>=0)&(ty<picture.shape[0]))),'Standing origin outside canvas')
        expected[ty,xx]=picture[yy,xx]
        builder.require(np.array_equal(np.array(selection_image(assets,{'bank':2,'ref':ref})),expected),f'Selection {ref} differs from gameplay {ref+84} at measured standing origin')


'''
s=s[:lo]+replacement+s[hi:];s=s.replace('# Versioned extension: preserve the v1 file and its frozen hashes.','# Versioned extension: preserve frozen v1/v2/v3; add measured BR standing copies1..8.',1)
ast.parse(s);dest=ROOT/'scripts/build_sprite_style_selection_v4.py';assert not dest.exists();dest.write_text(s,'utf8');print(dest)
