from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
D=P/'walk_design_basis';D.mkdir(exist_ok=True)
B=ROOT/'out/ver_buki_riko/riko_motion_20261023T210015989110Z'
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
def tile(n):
    prefix='idle' if n in [0,1,2,146,147,148] else 'frame'
    picture=Image.open(B/f'{prefix}_{n:03d}.png').convert('RGBA')
    if n in [0,1,2,146,147,148,5,6]:b=(-24,-24,32,24)
    else:b=geometry[n][1]
    canvas=Image.new('RGBA',(72,80));canvas.alpha_composite(picture,(36+b[0],44+b[1]));return canvas
numbers=[147,7,11,14,21,22,24,25,27,33,34,3,4]
board=Image.new('RGBA',(5*288,3*340),(42,45,54,255));draw=ImageDraw.Draw(board)
for i,n in enumerate(numbers):
    board.alpha_composite(tile(n).resize((288,320),Image.Resampling.NEAREST),(i%5*288,i//5*340+20));draw.text((i%5*288+4,i//5*340),str(n),font=font,fill='white')
board.save(D/'before_comparison.png')
walk=Image.new('RGBA',(72*3,80))
for i,n in enumerate([7,11,14]):walk.alpha_composite(tile(n),(i*72,0))
walk.resize((1080,400),Image.Resampling.NEAREST).save(D/'walk_style_reference.png')
tile(147).resize((576,640),Image.Resampling.NEAREST).save(D/'idle_target.png')
targets=[21,22,24,25,27,33,34,3,4]
sheet=Image.new('RGBA',(72*3,80*3))
for i,n in enumerate(targets):sheet.alpha_composite(tile(n),(i%3*72,i//3*80))
sheet.resize((1080,1200),Image.Resampling.NEAREST).save(D/'motion_targets.png')
(D/'layout.json').write_text(json.dumps({'cell':[72,80],'world_origin':[36,44],'motion_targets':targets,'style_frames':[7,11,14]},indent=2))
print(D)
