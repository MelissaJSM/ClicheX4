from pathlib import Path
P=Path(__file__).parent
s=(P/'review.py').read_text(encoding='utf-8')
s=s.replace('riko_motion_20261023T143602957663Z','riko_motion_20261023T210015989110Z').replace('riko_motion_20261023T152218300431Z','riko_motion_20261023T211436315688Z')
s=s.replace('(3,4,*range(7,35))','(0,1,2,3,4,5,6,*range(21,35),146,147,148)').replace('(0,1,2,5,6,146,147,148)','range(7,21)')
exec(s)
import shutil
D=P/'walk_design_basis';worlds=np.load(D/'worlds_final.npz');w={int(k):v for k,v in worlds.items()}
assert np.array_equal(w[0][1:80],w[147][:79])
assert np.array_equal(w[0][80:],w[147][80:])
assert np.array_equal(w[0],w[1]) and np.array_equal(w[0],w[2]) and np.array_equal(w[0],w[146])
assert int((w[147]!=w[148]).sum())==8
for n in [*range(27,33),147,0,148]:
    assert next(x for x in json.loads((D/'final_fit_checks.json').read_text())['checks'] if x['frame']==n)['outside']==0
for name in ['final_review.png','final_fit_checks.json','fit_registration.json','idle_revision.json']:
    shutil.copyfile(D/name,new/name)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
board=Image.new('RGBA',(1080,564),(42,45,54,255));draw=ImageDraw.Draw(board)
nums=[147,7,22,27,33];labels=['대기','보행 보존','점프','낙하','착지']
for row,folder in enumerate([old,new]):
    for col,(n,label) in enumerate(zip(nums,labels)):
        prefix='idle' if n==147 else 'frame';im=Image.open(folder/f'{prefix}_{n:03d}.png').convert('RGBA')
        if n==147:bounds=(-24,-24,32,24)
        else:
            manifest=json.loads((new/'manifest.json').read_text());from scripts.repack_zero import read_inputs
            from src.psx_frame_edit import frame_coverage
            _,_,_,_,gfx,parts,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z');f=graphics_bank(gfx,0)['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
            _,_,bounds=frame_coverage(raw,f['tile_count'],composition_frame(parts,0,n))
        tile=Image.new('RGBA',(72,80));tile.alpha_composite(im,(36+bounds[0],44+bounds[1]))
        board.alpha_composite(tile.resize((216,240),Image.Resampling.NEAREST),(col*216,row*282+34));draw.text((col*216+6,row*282+8),f'{"이전" if row==0 else "수정"} · {label}',font=font,fill='white')
board.save(new/'design_before_after.png')
seq=[0,146,147,148,0,146,147,148,0,1,2,1];ticks=[21,12,42,12,54,12,42,12,24,3,3,3];images=[]
for n in seq:
    canvas=Image.new('RGBA',(512,240),(42,45,54,255));d=ImageDraw.Draw(canvas);d.text((8,4),'합성 미리보기 · 이전 / 수정',font=font,fill='white')
    for x,folder in [(8,old),(264,new)]:canvas.alpha_composite(Image.open(folder/f'idle_{n:03d}.png').convert('RGBA').resize((224,192),Image.Resampling.NEAREST),(x,35))
    images.append(canvas.convert('RGB'))
images[0].save(new/'idle_before_after.gif',save_all=True,append_images=images[1:],duration=[round(t/60*1000) for t in ticks],loop=0,disposal=2)
heights={str(n):int(np.nonzero(a)[0].max()-np.nonzero(a)[0].min()+1) for n,a in w.items()}
summary={'walk_14_png_byte_identical':True,'changed_other_references':24,'head_neck_foreground_same_scale':True,'idle_height':heights['147'],'run_frame7_height':heights['7'],'opaque_heights_by_frame':heights,'whole_pose_height_normalized':False,'torso_pelvis_breathe_together_1px':True,'lower_shin_and_boots_fixed_from_world_y':16,'blink_changed_pixels':8,'all38_single_component':True,'full_bone_length_equality_automatically_proven':False,'art_quality_review_pending':True}
(new/'design_checks.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
