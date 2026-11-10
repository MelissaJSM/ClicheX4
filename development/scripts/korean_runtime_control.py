"""Approved Korean localization test input, with verified emulator focus."""
import ctypes
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.emulator_session import checked_window, main
from scripts.emulator_probe import Input, KeyInput

if __name__ == '__main__':
    project='ver_buki_riko'
    if '--project' in sys.argv:project=sys.argv[sys.argv.index('--project')+1]
    if project not in ('ver_buki_riko','ver_rin_nana'):raise ValueError('Unexpected project')
    if project=='ver_rin_nana':
        import scripts.emulator_session as session_control
        session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    # The caller still supplies emulator_session's checked session and action.
    # Alt down/up permits SetForegroundWindow after the browser has focus;
    # both events are paired before game input and never held with a game key.
    if '--session' in sys.argv:
        path = Path(sys.argv[sys.argv.index('--session') + 1]).resolve()
        if not path.is_relative_to(ROOT/'work'/project/'emulator_sessions'):
            raise ValueError('Unexpected session')
        record = json.loads((path/'session.local.json').read_text('utf-8'))
        user, hwnd = checked_window(record['pid'])
        if user.GetForegroundWindow() != hwnd:
            event = Input(); event.type = 1
            event.data.key = KeyInput(0, 0x38, 8, 0, 0)
            if user.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
                raise RuntimeError('Focus key down failed')
            event.data.key.flags |= 2
            if user.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
                raise RuntimeError('Focus key release failed')
            user.SetForegroundWindow(hwnd)
    main()
