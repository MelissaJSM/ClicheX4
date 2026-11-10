"""이미 실행 중인 ePSXe 창 캡처와 포커스를 확인한 단일 키 입력. Windows 전용."""
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path
import time

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]


class KeyInput(ctypes.Structure):
    _fields_ = [('vk', wintypes.WORD), ('scan', wintypes.WORD),
                ('flags', wintypes.DWORD), ('time', wintypes.DWORD), ('extra', ctypes.c_size_t)]


class MouseInput(ctypes.Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG), ('data', wintypes.DWORD),
                ('flags', wintypes.DWORD), ('time', wintypes.DWORD), ('extra', ctypes.c_size_t)]


class InputData(ctypes.Union):
    _fields_ = [('key', KeyInput), ('mouse', MouseInput)]


class Input(ctypes.Structure):
    _fields_ = [('type', wintypes.DWORD), ('data', InputData)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hwnd', type=int, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--scan', type=lambda v: int(v, 0))
    parser.add_argument('--extended', action='store_true')
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if not out.is_relative_to((ROOT/'work').resolve()) or not out.is_dir():
        raise ValueError('Existing workspace work directory required')
    if args.scan is not None and not 1 <= args.scan <= 0x7f:
        raise ValueError('Invalid scan code')
    user = ctypes.windll.user32
    title = ctypes.create_unicode_buffer(256)
    user.GetWindowTextW(args.hwnd, title, 256)
    if title.value != 'ePSXe - Enhanced PSX emulator':
        raise ValueError('Not the expected emulator window')
    # 업무 방해 방지: 창을 자동으로 앞으로 가져오지 않는다.
    # 사용자가 직접 ePSXe를 활성화한 경우에만 입력/화면 검증한다.
    if user.GetForegroundWindow() != args.hwnd:
        raise RuntimeError('Emulator is not focused; no input sent')
    if args.scan is not None:
        flags = 8 | int(args.extended)
        event = Input()
        event.type = 1
        event.data.key = KeyInput(0, args.scan, flags, 0, 0)
        if user.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
            raise RuntimeError('Key down failed')
        try:
            time.sleep(0.12)
        finally:
            event.data.key.flags |= 2
            if user.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
                raise RuntimeError('Key release failed')
        time.sleep(0.7)
    if user.GetForegroundWindow() != args.hwnd:
        raise RuntimeError('Focus changed; screenshot not recorded')
    rect = wintypes.RECT()
    point = wintypes.POINT(0, 0)
    user.GetClientRect(args.hwnd, ctypes.byref(rect))
    user.ClientToScreen(args.hwnd, ctypes.byref(point))
    screenshot = ImageGrab.grab(bbox=(point.x, point.y, point.x+rect.right, point.y+rect.bottom))
    path = out/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'_screen.png')
    with path.open('xb') as stream:
        screenshot.save(stream, format='PNG')
    print(path)


if __name__ == '__main__':
    main()
