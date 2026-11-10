from pathlib import Path
P=Path(__file__).parent
s=(P/'review_repair.py').read_text(encoding='utf-8').split("g=recipe['gait']")[0]
s=s.replace('riko_motion_20261023T195248689307Z','riko_motion_20261023T201438792298Z').replace("R=P/'gait_cape_repair'","R=P/'stride_revision'")
exec(s)
g=recipe['gait']['phase_assignment'];assert len(g)==14 and all(r['near_phase']==i and r['far_phase']==(i+7)%14 for i,r in enumerate(g))
ticks=recipe['run_ticks'];speeds=[]
for i in [1,2,3]:
 a,b=g[i]['near_foot'],g[i+1]['near_foot'];assert a[1]==b[1]==23
 speed=(b[0]-a[0])/ticks[i];assert abs(speed-2)<.12;speeds.append(speed)
old=json.loads((P/'gait_cape_repair/recipe.json').read_text())['gait']['phase_assignment'];span=lambda rows,key:max(r[key][0] for r in rows)-min(r[key][0] for r in rows)
report={'cape_connectivity':cape,'phase_count':14,'ticks':ticks,'phase_offset_ticks':16,'stance_speed_px_per_tick':speeds,'target_speed':2,'target_source':'Local decomp player_check.c:player_check_walk, FIXED(2); live velocity remains to be checked','old_near_foot_travel_px':span(old,'near_foot'),'new_near_foot_travel_px':span(g,'near_foot'),'foot_positions':g,'head_neck_foreground_exact':True,'tests_passed':41,'full_art_quality_approved':False}
(out/'art_quality_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
import shutil
shutil.copyfile(R/'stride_review.png',out/'motion_review.png')
images=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
for n in range(7,21):
 w=world(n,R,'frame');a=w[24:96,32:96];m=a!=0;rgba=np.zeros((72,64,4),dtype=np.uint8);rgba[m,:3]=colors[a[m]-1];rgba[m,3]=255;canvas=Image.new('RGBA',(512,320),(42,45,54,255));d=ImageDraw.Draw(canvas);d.text((8,3),'미리보기 · 1배 / 4배 · 원작 32 tick',font=font,fill='white');canvas.alpha_composite(Image.fromarray(rgba),(60,100));canvas.alpha_composite(Image.fromarray(rgba).resize((256,288),Image.Resampling.NEAREST),(225,30));images.append(canvas.convert('RGB'))
images[0].save(out/'gait_preview.gif',save_all=True,append_images=images[1:],duration=[round(t/60*1000) for t in ticks],loop=0,disposal=2)
prev=ROOT/'out/ver_buki_riko/riko_motion_20261023T200224432890Z';preserved=[]
for n in [0,1,2,3,4,5,6,*range(21,35),146,147,148]:
 name=f'{"idle" if n in [0,1,2,146,147,148] else "frame"}_{n:03d}.png';assert (prev/name).read_bytes()==(out/name).read_bytes();preserved.append(name)
(out/'stride_comparison.json').write_text(json.dumps({'previous_build':str(prev),'changed_frames':list(range(7,21)),'unchanged_pngs':preserved,'body_size_checks':'Native reference foreground preserved; pelvis translated with torso; uniform generated limb scale .11'},indent=2),encoding='utf-8')
print(json.dumps({'stance_speeds':speeds,'old_foot_travel':span(old,'near_foot'),'new_foot_travel':span(g,'near_foot'),'unchanged_pngs':len(preserved)}))
