from pathlib import Path
import ast
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
s=(ROOT/'scripts/build_sprite_style_selection_v4.py').read_text('utf8')
replacements=[
("builder.require(plan['project']=='ver_buki_riko','Unmeasured standing origin')","builder.require(plan['project'] in ('ver_buki_riko','ver_rin_nana'),'Unmeasured standing origin')"),
("for ref,dy in enumerate((-1,0,0,0,0,-1,-2,0),1):","for ref,dy in enumerate((-1,0,0,0,0,-1,-2,0) if plan['project']=='ver_buki_riko' else (0,)*8,1):"),
("not sync_standing or (plan['project']=='ver_buki_riko' and not preserve_x","not sync_standing or (plan['project'] in ('ver_buki_riko','ver_rin_nana') and not preserve_x")]
for a,b in replacements:assert s.count(a)==1,a;s=s.replace(a,b)
s=s.replace('add measured BR standing copies1..8.','add measured BR/RN standing copies1..8; frozen v4 remains unchanged.').replace('add measured BR shooting8.','add measured BR/RN shooting8.')
ast.parse(s);p=ROOT/'scripts/build_sprite_style_selection_v5.py';assert not p.exists();p.write_text(s,'utf8');print(p)
