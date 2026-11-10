from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
D=P/'zero_based_rebuild';D.mkdir(exist_ok=True)
source=P/'stride_revision'
sheet=Image.new('RGBA',(128,144));cells=[]
for k,n in enumerate([7,10,14,17]):
    sprite=Image.open(source/f'original_{n:03d}.png').convert('RGBA');b=geometry[n][1]
    cell=Image.new('RGBA',(64,72));cell.alpha_composite(sprite,(32+b[0],40+b[1]));cells.append(cell)
    sheet.alpha_composite(cell,(k%2*64,k//2*72))
sheet.resize((768,864),Image.Resampling.NEAREST).save(D/'zero_key_poses.png')
full=Image.new('RGBA',(256,288))
for k,n in enumerate(range(7,21)):
    sprite=Image.open(source/f'original_{n:03d}.png').convert('RGBA');b=geometry[n][1]
    cell=Image.new('RGBA',(64,72));cell.alpha_composite(sprite,(32+b[0],40+b[1]));full.alpha_composite(cell,(k%4*64,k//4*72))
full.resize((1280,1440),Image.Resampling.NEAREST).save(D/'zero_full_cycle.png')
(D/'reference.json').write_text(json.dumps({'kind':'locally extracted original Zero pose reference','frame_numbers':[7,10,14,17],'source_build_sha256':'3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','local_world_origin_in_cell':[32,40],'cell_native_size':[64,72],'sent_to_builtin_imagegen':True,'user_direction':'기본 제로처럼 걷는다는 느낌을 살려봐'},ensure_ascii=False,indent=2),encoding='utf-8')
