from pathlib import Path
P=Path(__file__).parent
s=(P/'review_repair.py').read_text(encoding='utf-8').split("g=recipe['gait']")[0]
s=s.replace('riko_motion_20261023T195248689307Z','riko_motion_20261023T203252658674Z').replace("R=P/'gait_cape_repair'","R=P/'coherent_walk'")
exec(s)
import shutil
previous=ROOT/'out/ver_buki_riko/riko_motion_20261023T201438792298Z'
preserved=[]
for n in [0,1,2,3,4,5,6,*range(21,35),146,147,148]:
    name=f'{"idle" if n in [0,1,2,146,147,148] else "frame"}_{n:03d}.png'
    assert (previous/name).read_bytes()==(out/name).read_bytes();preserved.append(name)
for n in range(7,21):assert (previous/f'frame_{n:03d}.png').read_bytes()!=(out/f'frame_{n:03d}.png').read_bytes()
records=recipe['coherent_body']['records']
assert len(records)==14 and all(r['ground_y']==23 and r['uniform_scale']==.17 and not r['waist_composite'] and not r['separate_hip_translation'] and not r['parts_outside'] for r in records)
connect=[{'frame':n,'components':[len(g) for g in components(world(n,R,'frame'))]} for n in range(7,21)]
report={'cape_connectivity':cape,'whole_body_recipe':recipe['coherent_body'],'run_components':connect,'native_frame_count':14,'ticks':recipe['run_ticks'],'duration_ticks':sum(recipe['run_ticks']),'head_neck_foreground_exact':True,'palette_parts_timing_preserved':True,'full_art_quality_approved':False,'gait_foot_speed_automatic_proof':False}
(out/'art_quality_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(out/'coherent_comparison.json').write_text(json.dumps({'previous_build':str(previous),'changed_frames':list(range(7,21)),'unchanged_pngs':preserved},indent=2),encoding='utf-8')
shutil.copyfile(R/'native_review.png',out/'motion_review.png')
images=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
for n in range(7,21):
    canvas=Image.new('RGBA',(600,330),(42,45,54,255));draw=ImageDraw.Draw(canvas)
    draw.text((10,3),'합성 미리보기: 이전 / 수정 / 수정 1배',font=font,fill='white')
    for folder,x in [(previous,10),(R,260)]:
        w=world(n,folder,'frame');a=w[24:96,32:96];m=a!=0;rgba=np.zeros((72,64,4),dtype=np.uint8);rgba[m,:3]=colors[a[m]-1];rgba[m,3]=255;tile=Image.fromarray(rgba)
        canvas.alpha_composite(tile.resize((256,288),Image.Resampling.NEAREST),(x,30))
        if folder==R:canvas.alpha_composite(tile,(525,125))
    images.append(canvas.convert('RGB'))
images[0].save(out/'gait_before_after.gif',save_all=True,append_images=images[1:],duration=[round(t/60*1000) for t in recipe['run_ticks']],loop=0,disposal=2)
print(json.dumps({'preserved_pngs':len(preserved),'changed_frames':14,'cape':cape,'run_connectivity':connect}))
