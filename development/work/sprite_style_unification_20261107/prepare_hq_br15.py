from pathlib import Path
R=Path(__file__).resolve().parent/'runtime'
p=R/'advance_hq_br15.py';assert not p.exists()
t=(R/'advance_hq_rn16.py').read_text('utf8').replace('read_menu_rn16','read_menu_br15').replace('ver_rin_nana','ver_buki_riko')
p.write_text(t,'utf8')
