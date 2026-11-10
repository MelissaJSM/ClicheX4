"""로컬 조절 UI 서버를 숨김 실행하고 사용자 브라우저를 연다."""
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import webbrowser

ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:8766'


def ready():
    try:
        with urllib.request.urlopen(URL+'/api/state',timeout=1) as response:
            data=json.load(response)
        return len(data.get('labels',[]))==13 and 'selections' in data
    except Exception:return False


def main():
    if not ready():
        env_python=ROOT/'work/tools/voice_env/Scripts/python.exe'
        if not env_python.is_file():raise RuntimeError('The project voice environment is missing')
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
        with (ROOT/'work/tools/voice_studio.log').open('ab') as log,(ROOT/'work/tools/voice_studio_error.log').open('ab') as err:
            subprocess.Popen([str(env_python),'-u',str(ROOT/'scripts/riko_voice_studio.py')],cwd=ROOT,
                stdout=log,stderr=err,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and not ready():time.sleep(.3)
        if not ready():raise RuntimeError('Local server did not start; inspect work/tools/voice_studio_error.log')
    webbrowser.open(URL)
    print(URL)


if __name__=='__main__':main()
