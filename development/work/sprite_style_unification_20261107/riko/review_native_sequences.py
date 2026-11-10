"""동결13 후보의 원래 애니메이션 연결표. 실제 입력/물리는 재현하지 않는다."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_sprite_playback import parse_sequence,TABLES,at,ZERO_SELECTOR
from scripts.build_sprite_style_album import zero_image,zero_palettes
W=ROOT/'work/sprite_style_unification_20261107';D=W/'riko/air_saber_native_sequences';D.mkdir(exist_ok=False)
plan=json.loads((W/'staging_br_v4.json').read_text('utf8'));exe=read_disc(ROOT/plan['source_bin'],('SLUS_005.61',))[0]['SLUS_005.61'];sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(exe)=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616'
old=(W/'riko/prepared_followup_cloth_v1/PL01_U.ARC').read_bytes();new=(W/'riko/prepared_air_saber_v1/PL01_U.ARC').read_bytes();assert sha(new)=='7b79453e89d3a9600ee117630a510844a5738c31bf3e3e3d5b6ebac35b739328'
rows=[]
for animation in [90,92,103]:
    seq=parse_sequence(exe,TABLES['zero'],animation);bank=at(exe,ZERO_SELECTOR+animation,1)[0];steps=seq['steps'];pages=[]
    for start in range(0,len(steps),8):
        subset=steps[start:start+8];sheet=Image.new('RGB',(192*len(subset),366),'#64717b');draw=ImageDraw.Draw(sheet)
        for col,step in enumerate(subset):
            for row,(label,data)in enumerate([('previous',old),('candidate',new)]):
                spec=dict(id=f'normal:b{bank}_{step["frame_ref"]:03}',bank=bank,ref=step['frame_ref'],form='normal')
                pic=zero_image(data,'riko',spec,zero_palettes(data)).crop((112,112,208,192)).resize((192,160),Image.Resampling.NEAREST)
                sheet.paste(pic,(col*192,row*183+22),pic);draw.text((col*192+4,row*183+4),f'{label} {step["frame_ref"]} / {step["duration_calls"]} calls',fill='white')
        path=D/f'anim{animation:03}_strip{start//8:02}.png';sheet.save(path);pages.append(str(path.relative_to(ROOT)))
    rows.append(dict(animation=animation,bank=bank,steps=steps,loop_to_position=seq['loop_to_position'],strips=pages))
(D/'sequence_manifest.json').write_text(json.dumps(dict(candidate_sha256=sha(new),exe_sha256=sha(exe),sequences=rows,fixed_world_origin=[160,160],same_integer_scale=2,gameplay_runtime_verified=False,physics_and_event_handlers_simulated=False),indent=2)+'\n','utf8')
print(json.dumps([{'animation':r['animation'],'bank':r['bank'],'steps':len(r['steps']),'strips':len(r['strips'])}for r in rows]))
