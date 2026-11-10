"""Rin v9 격리 새게임 촬영. 기존 게임 창/카드/상태는 조작하지 않는다."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
helper = ROOT/'work/hud_frame_fix_20261105/shibuki_runtime_review/run_isolated.py'
spec = importlib.util.spec_from_file_location('isolated_review',helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.OUT = Path(__file__).resolve().parent
module.EXE = module.OUT/'emulator/ePSXe.exe'
module.CUE = ROOT/'out/ver_rin_nana/hud_rin_optical_20261105_v9/rin_nana.cue'
module.GAME_SHA = '8b70dbca936c2ad4d72eade207cf44f9095fb9ae05beb4e2e4943a7ba6e19768'

if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'launch':
        module.launch()
    elif action == 'relaunch':
        import os, subprocess, json
        from datetime import datetime, timezone
        saved = json.loads((module.OUT/'session.json').read_text('utf8'))
        record = json.loads((Path(saved['session'])/'session.local.json').read_text('utf8'))
        module.control.EMULATOR = module.EXE
        assert not module.control.working_instances()
        assert module.digest(module.EXE) == module.control.EXE_HASH
        assert module.digest(module.CUE.with_suffix('.bin')) == module.GAME_SHA
        env = os.environ.copy(); env['__COMPAT_LAYER'] = 'WIN7RTM'
        startup = subprocess.STARTUPINFO(); startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW; startup.wShowWindow = 0
        process = subprocess.Popen(record['command'], cwd=module.EXE.parent, env=env, startupinfo=startup)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        session = ROOT/'work/ver_buki_riko/emulator_sessions'/(stamp+'_isolated_rin_hud')
        session.mkdir()
        record['pid'] = process.pid
        (session/'session.local.json').write_text(json.dumps(record,indent=2)+'\n','utf8')
        (module.OUT/'session.json').write_text(json.dumps({'session':str(session),'pid':process.pid},indent=2)+'\n','utf8')
        print(json.dumps({'session':str(session),'pid':process.pid}))
    elif action == 'key':
        module.run('key',int(sys.argv[2],0),extended='--extended' in sys.argv)
    elif action in ('capture','close','audit'):
        module.run(action)
    else:
        raise ValueError('Unsupported isolated action')
