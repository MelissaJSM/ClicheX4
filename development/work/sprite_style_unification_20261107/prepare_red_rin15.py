from pathlib import Path
import json
W=Path(__file__).resolve().parent;R=W/'runtime'
src=(R/'advance_intro_br12.py').read_text('utf8')
src=src.replace('black-Riko v12','red-Rin v15').replace('ver_buki_riko','ver_rin_nana').replace('20261107T110718653432Z','20261107T132706808542Z').replace('read_menu_br12','read_menu_rn15').replace('19537440','17374752').replace('riko_black12_intro','red_rin15_intro')
p=R/'advance_intro_rn15.py';assert not p.exists();p.write_text(src,'utf8')
plan=json.loads((R/'riko_black12_play/evidence.json').read_text('utf8'))['plan']
p=R/'red_rin15_plan.json';assert not p.exists();p.write_text(json.dumps(plan)+'\n','utf8')
