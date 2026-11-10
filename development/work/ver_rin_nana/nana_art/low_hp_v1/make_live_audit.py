from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
s=(ROOT/'work/ver_rin_nana/nana_art/ladder_v1/live_audit.py').read_text('utf8').replace('20261029T232946297413Z','20261029T233920567202Z').replace('사다리 발동 검사는 아님','저체력 발동 검사는 아님').replace("'ladder_animation_observed':False","'low_hp_animation_observed':False")
p=Path(__file__).parent/'live_audit.py';assert not p.exists();p.write_text(s,'utf8')
