import json,sys,time,threading
from pathlib import Path
import numpy as np,soundfile as sf,soundcard as sc
D=Path(__file__).parent
duration=float(sys.argv[1]) if len(sys.argv)>1 else 35
name=sys.argv[2] if len(sys.argv)>2 else 'runtime_title'
speaker=sc.default_speaker();loopback=sc.get_microphone(id=speaker.id,include_loopback=True)
assert loopback.isloopback
chunks=[];start=time.time()
with loopback.recorder(samplerate=48000,channels=2,blocksize=4800) as rec:
    print('LOOPBACK_READY',flush=True)
    for _ in range(round(duration*10)):chunks.append(rec.record(numframes=4800))
audio=np.concatenate(chunks)
sf.write(D/(name+'.wav'),audio,48000,subtype='PCM_16')
(D/(name+'.json')).write_text(json.dumps({'loopback_only':True,'microphone_recorded':False,'duration':duration,'start_unix':start,'peak':float(abs(audio).max()),'rms':float(np.sqrt(np.mean(audio**2)))},indent=2),'utf-8')
print('RECORDED',name,len(audio),flush=True)
