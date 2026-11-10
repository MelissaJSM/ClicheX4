"""실제 ADPCM에서 복원한 원본/Riko 비교 청취 자료를 만든다."""
import argparse
import html
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
LABELS=['피격 후보 A','피격 후보 B','점프 계열','기본 세이버','점프·연속 공격 계열',
        '빙열참·연속 공격 계열','뇌신격','2단 점프 등','벽·사다리 공격 등','용염인·질풍아',
        '낙봉파','저체력','사망']


def main(args):
    import numpy as np
    import soundfile as sf
    import librosa
    root=ROOT/'work/ver_buki_riko/voice_production/v1'
    packed=root/args.packed
    output=ROOT/'out/ver_buki_riko'/args.build/'voice_review'
    if output.exists(): raise ValueError('Preview already exists')
    output.mkdir()
    rows=[]; sequence=[]; timeline=[]; cursor=0
    for voice_id,label in enumerate(LABELS):
        stem=f'voice_{voice_id:02d}'
        tags=[]
        for kind,folder in [('original',root/'original'),('riko',packed)]:
            name=f'{stem}_{kind}.wav'
            shutil.copyfile(folder/(stem+'.wav'),output/name)
            data,rate=sf.read(output/name,dtype='float32')
            data=librosa.resample(data,orig_sr=rate,target_sr=22050)
            timeline.append({'sound_id':voice_id,'label':label,'kind':kind,'start_seconds':cursor/22050,'duration_seconds':len(data)/22050})
            sequence.extend([data,np.zeros(11025,dtype=np.float32)])
            cursor+=len(data)+11025
            tags.append(f'<td><audio controls preload="none" src="{name}"></audio></td>')
        sequence.append(np.zeros(11025,dtype=np.float32));cursor+=11025
        rows.append(f'<tr><th>{voice_id:02d} · {html.escape(label)}</th>{"".join(tags)}</tr>')
    sf.write(output/'original_then_riko.wav',np.concatenate(sequence),22050,subtype='PCM_16')
    (output/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf-8')
    page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>Riko 플레이 음성 비교</title>
<style>body{max-width:1000px;margin:40px auto;padding:0 20px;background:#101c25;color:#ebf5f3;font:16px/1.6 system-ui}table{border-collapse:collapse;width:100%}td,th{padding:12px;border-bottom:1px solid #38525c;text-align:left}a{color:#8ff5dc}audio{max-width:280px;width:100%}h1{font-size:26px}</style>
<h1>Riko 플레이 음성 · 첫 적용 후보</h1>
<p>왼쪽은 원본, 오른쪽은 게임에 삽입한 Riko 음성입니다. 같은 음량 기준으로 비교하며 자동 재생하지 않습니다.</p>
<p>PS1 ADPCM 압축 후의 음성입니다. 실제 게임의 잔향·음량 엔벨로프는 포함하지 않습니다. 사망 음성은 단일 파형 미리보기이며 게임에서는 원래의 좌우 음높이 효과가 유지됩니다.</p>
<p>동작 이름은 정적 호출 분석 기준이며 일부는 여러 행동에서 공유합니다. 청취 품질과 모든 동작의 실기 검증은 아직 최종 수용 전입니다.</p>
<p><a href="original_then_riko.wav">전체 이어 듣기: 각 ID마다 원본 → Riko</a></p>
<table><thead><tr><th>음성</th><th>원본 Zero</th><th>Riko 후보</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table></html>'''
    (output/'index.html').write_text(page,encoding='utf-8')
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packed',default='packed_v5')
    p.add_argument('--build',required=True)
    main(p.parse_args())
