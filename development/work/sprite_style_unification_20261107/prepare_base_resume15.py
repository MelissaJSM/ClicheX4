from pathlib import Path
R=Path(__file__).resolve().parent/'runtime'
p=R/'load_base_resume_br15.py';assert not p.exists()
t=(R/'load_base_br15.py').read_text('utf8')
t=t.replace("result['game_info']['route']==7", "result['game_info']['route']==9 and result['engine']['substate']==3 and result['menu_cursor']==0")
p.write_text(t,'utf8')
