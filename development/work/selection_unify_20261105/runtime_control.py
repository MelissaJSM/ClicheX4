"""선택 UI 확인을 위한 격리 에뮬레이터 제어. 원본 카드/F1 사용 없음."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('isolated_ui',ROOT/'work/hud_frame_fix_20261105/shibuki_runtime_review/run_isolated.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PROJECT='ver_rin_nana'
m.OUT=Path(__file__).resolve().parent/'runtime_second_v4'
m.OUT.mkdir(exist_ok=True)
m.CUE=ROOT/'out/ver_rin_nana/selection_unified_20261105_v4/rin_nana.cue'
m.GAME_SHA='8c5c7ba9bb2fd6d04080db453c2890c6446350fe19b896013661dc97b21b5bc1'
if '--first' in sys.argv:
    PROJECT='ver_buki_riko'
    m.OUT=Path(__file__).resolve().parent/'runtime_first_v4';m.OUT.mkdir(exist_ok=True)
    m.CUE=ROOT/'out/ver_buki_riko/selection_unified_20261105_v4/shibuki_riko.cue'
    m.GAME_SHA='15b6eec0ff23decff4f42133e20f0d0b33efed40c4ecf3f245905ef2a5357aea'
m.EXE=m.OUT/'emulator/ePSXe.exe'
if __name__=='__main__':
    action=sys.argv[1]
    if action=='launch':m.launch()
    elif action=='key':m.run('key',int(sys.argv[2],0),extended='--extended' in sys.argv)
    elif action in ('capture','close','audit'):m.run(action)
    else:raise ValueError('Unsupported isolated action')
