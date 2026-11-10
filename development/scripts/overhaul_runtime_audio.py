"""작업 에뮬레이터 테스트 동안 기본 출력 장치의 짧은 루프백을 로컬 저장한다.

마이크 입력은 열지 않는다. 출력 장치 전체이므로 녹음은 게임 동작 증거와 함께
검토하고, 다른 앱 음성과 구분하지 못한 구간은 게임 검증으로 채택하지 않는다.
"""
import argparse
import json
from pathlib import Path
import sys
import time
import wave
import numpy as np
import soundcard as sc

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import scripts.emulator_session as control
from scripts.project import digest,new_run,write_json

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],required=True)
    p.add_argument('--session',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=20)
    p.add_argument('--label',required=True)
    p.add_argument('--device',help='출력 장치 이름 또는 ID. 생략하면 기본 출력 장치.')
    a=p.parse_args()
    session=a.session.resolve()
    if not session.is_relative_to(ROOT/'work'/a.project/'emulator_sessions') or not 1<=a.seconds<=60:
        raise ValueError('Unexpected session or duration')
    if a.project=='ver_rin_nana':control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    state=json.loads((session/'session.local.json').read_text('utf8'))
    control.checked_window(state['pid'])
    speaker=sc.get_speaker(a.device) if a.device else sc.default_speaker()
    device=sc.get_microphone(speaker.id,include_loopback=True)
    if not device.isloopback:raise ValueError('Microphone recording is forbidden')
    out=new_run(ROOT,a.project,'overhaul_audio_runtime')
    print(json.dumps({'recording':str(out),'seconds':a.seconds,'device':device.name}),flush=True)
    start=time.time();rate=48000
    with device.recorder(samplerate=rate,channels=2) as recorder:
        pcm=recorder.record(numframes=round(a.seconds*rate))
    if not np.isfinite(pcm).all():raise ValueError('Invalid audio samples')
    data=np.rint(np.clip(pcm,-1,1)*32767).astype('<i2')
    path=out/'loopback.wav'
    with wave.open(str(path),'wb') as w:
        w.setparams((2,2,rate,0,'NONE','not compressed'));w.writeframes(data.tobytes())
    report=dict(label=a.label,session=str(session),pid=state['pid'],bin_sha256=state['bin_sha256'],
                started_epoch=start,seconds=len(pcm)/rate,output_device=device.name,loopback_only=True,
                microphone_opened=False,peak=float(np.max(np.abs(pcm))),rms=float(np.sqrt(np.mean(pcm**2))),
                sha256=digest(path),auditory_quality_reviewed=False,other_application_audio_may_be_present=True)
    write_json(out/'evidence.json',report)
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
