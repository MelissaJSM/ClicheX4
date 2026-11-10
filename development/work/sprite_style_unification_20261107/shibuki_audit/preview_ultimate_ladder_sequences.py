"""원표의 프레임 순서만 표시하는 사다리 후보 검토. 물리/실기 재현 아님."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
def main():
    out=H/'ultimate_ladder_sequence_probe01';need(not out.exists(),'Fresh preview');out.mkdir();src=H/'ultimate_ladder_contacts01';ap=ROOT/'work/sprite_style_unification_20261107/zero_audit/ultimate_ladder_aliases01/report.json';j=json.loads(ap.read_text('utf8'));a=Archive((H/'prepared_ultimate_dash01/PL02_U.ARC').read_bytes());rows=[]
    for seq in j['original_exe_sequences']:
        if seq['id']not in(27,28,29,31,32):continue
        steps=seq['steps'];pics=[]
        for form,mask in [('before',15),('after',0)]:
            frames=[];durations=[]
            for s in steps:
                n=s['frame'];p=src/f'{form}_{n:03}.png';new=Image.open(p).convert('RGBA')if p.exists()else a.composite(n,mask)[0];old=a.composite(n,mask)[0];pics.append((f'{form} {n} / {s["calls"]} calls',new));v=Image.new('RGB',(384,320),(29,34,44));d=ImageDraw.Draw(v);d.text((8,5),f'FRAME ORDER ONLY: id{seq["id"]} {form} ref{n}',fill='white');d.text((8,20),'60 calls/s assumed; no actor movement/input',fill='white')
                for x,label,im in [(20,'parent',old),(204,'new candidate',new)]:
                    cut=im.crop((128,128,192,192)).resize((160,160),Image.Resampling.NEAREST);v.paste(cut,(x,65),cut);d.text((x,46),label,fill='white');d.line((x,145,x+160,145),fill=(65,72,85))
                frames.append(v);durations.append(max(1,round(s['calls']*1000/60)))
            frames[0].save(out/f'anim{seq["id"]}_{form}.webp',save_all=True,append_images=frames[1:],duration=durations,loop=0,lossless=True)
            rows.append({'id':seq['id'],'form':form,'steps':steps,'duration_ms':durations,'native_tick_unit':'원 animate 함수호출 횟수','playback_clock_assumption':60,'external_events_reproduced':False,'actor_vertical_movement_reproduced':False,'preview_loop_policy':'파일끝에서검토반복.원표말단/입력탈출을게임처럼재현한다는뜻아님.','new_refs':[s['frame']for s in steps if(src/f'{form}_{s["frame"]:03}.png').exists()]})
        page(pics,a.composite(0,15)[0],out/f'anim{seq["id"]}_contacts.png',cols=4,scale=3)
    write(out/'report.json',{'source_animation_report_sha256':sha(ap.read_bytes()),'candidate_report_sha256':sha((src/'report.json').read_bytes()),'rows':rows,'scope':'원프레임순서/호출수의시각검토용.물리이동/사다리입력/실제GPU/메모리검증아님.','runtime_verified':False,'actually_watched_animation':False})
if __name__=='__main__':main()
