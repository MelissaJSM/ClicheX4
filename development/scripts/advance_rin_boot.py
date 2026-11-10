"""이미 확인한 원작 타이틀과 선택 화면만 인식하여 Start를 제한 입력한다."""
import argparse,json,subprocess,sys,time
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--session',required=True);args=p.parse_args()
    session=(ROOT/args.session).resolve()
    if not session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions'):raise ValueError('Unexpected session')
    reference=np.asarray(Image.open(ROOT/'work/ver_rin_nana/emulator_sessions/20261028T091419828452Z/20261028T091740989905Z.png').convert('RGB'),dtype=np.int16)
    log=[];sent=0;last=0;deadline=time.monotonic()+50
    def command(action):
        cmd=[sys.executable,str(ROOT/'scripts/korean_runtime_control.py'),'--project','ver_rin_nana',action,'--session',str(session)]
        if action=='key':cmd+=['--scan','0x35','--hold','0.16']
        result=subprocess.run(cmd,capture_output=True,text=True,check=True)
        return json.loads(result.stdout)
    while time.monotonic()<deadline:
        result=command('capture');a=np.asarray(Image.open(result['capture']).convert('RGB'),dtype=np.int16)
        distance=float(np.abs(a[45:280,70:730]-reference[45:280,70:730]).mean())
        green=float(np.mean((a[:80,:,1]>a[:80,:,0]+30)&(a[:80,:,1]>a[:80,:,2]+20)))
        log.append({'capture':result['capture'],'title_distance':distance,'select_green_fraction':green})
        if green>.4:break
        if distance<5 and sent<3 and time.monotonic()-last>1.5:
            command('key');sent+=1;last=time.monotonic()
        time.sleep(.7)
    (session/'title_navigation.json').write_text(json.dumps({'start_presses':sent,'observations':log},indent=2)+'\n','utf-8')
    print(json.dumps({'start_presses':sent,'last_capture':log[-1]['capture'],'selection_seen':log[-1]['select_green_fraction']>.4}))
if __name__=='__main__':main()
