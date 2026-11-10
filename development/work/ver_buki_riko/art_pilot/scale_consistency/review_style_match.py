from pathlib import Path
P=Path(__file__).parent
s=(P/'review.py').read_text(encoding='utf-8')
s=s.replace('riko_motion_20261023T143602957663Z','riko_motion_20261023T204944958766Z').replace('riko_motion_20261023T152218300431Z','riko_motion_20261023T210015989110Z')
s=s.replace('(3,4,*range(7,35))','range(7,21)').replace('(0,1,2,5,6,146,147,148)','(0,1,2,3,4,5,6,*range(21,35),146,147,148)')
exec(s)
import shutil
D=P/'idle_style_match'
for name in ['style_checks.json','comparison.png','style_comparison.gif','native_review.png']:
    shutil.copyfile(D/name,new/name)
recipe=json.loads((D/'recipe.json').read_text(encoding='utf-8'))
assert recipe['run_ticks']==[2,3,2,2,2,3,2]*2
for n in range(7,21):
    a=np.array(Image.open(old/f'frame_{n:03d}.png'));b=np.array(Image.open(new/f'frame_{n:03d}.png'))
    assert a.shape==b.shape
    assert np.array_equal(a[np.isin(a,[9,11,13])],b[np.isin(a,[9,11,13])])
    assert int(((a!=0)!=(b!=0)).sum())==(3 if n==17 else 0)
checks=json.loads((D/'style_checks.json').read_text(encoding='utf-8'))
summary={'changed_frames':list(range(7,21)),'unchanged_pngs':24,'changed_color_pixels':sum(r['changed_color_pixels'] for r in checks['records']),'dark_pixels_before':sum(r['dark_before'] for r in checks['records']),'dark_pixels_after':sum(r['dark_after'] for r in checks['records']),'pose_alpha_unchanged_except_frame17_detached3':True,'timing_ticks':32,'source_generated':'work/ver_buki_riko/art_pilot/scale_consistency/idle_style_match/generated_style.png','art_quality_approved':False}
(new/'style_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
