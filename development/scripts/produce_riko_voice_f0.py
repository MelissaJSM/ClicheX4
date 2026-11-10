"""UI와 같은 엔진으로 13개 음성의 다음 후보를 제작한다."""
import argparse
import json
from pathlib import Path
import shutil
from riko_voice_engine import VoiceEngine
from riko_voice_environment import VOICE_ROOT


def main(args):
    output=VOICE_ROOT/args.name
    if output.exists():raise ValueError('Fresh batch name required')
    engine=VoiceEngine();output.mkdir();rows=[];sources=[]
    for voice_id in range(13):
        child=VOICE_ROOT/(args.name+f'_id{voice_id:02d}')
        m=engine.render(voice_id,child)
        for p in child.glob('*.wav'):shutil.copyfile(p,output/p.name)
        for p in child.glob('*.npz'):shutil.copyfile(p,output/p.name)
        rows+=m['records'];sources.append(str(child))
        print(json.dumps(m['records'][0]),flush=True)
        (output/'manifest.local.json').write_text(json.dumps({**m,'records':rows,'source_candidates':sources},indent=2),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--name',default='f0_full_v2')
    main(p.parse_args())
