from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
D=P/'idle_style_match';D.mkdir(exist_ok=True)
B=P/'zero_based_rebuild'
sheet=Image.new('RGBA',(256,288))
for i,n in enumerate(range(7,21)):
    a=np.array(Image.open(B/f'frame_{n:03d}.png'));b=geometry[n][1]
    tile=Image.new('RGBA',(64,72));tile.alpha_composite(Image.open(B/f'frame_{n:03d}.png').convert('RGBA'),(32+b[0],40+b[1]))
    sheet.alpha_composite(tile,(i%4*64,i//4*72))
sheet.resize((1280,1440),Image.Resampling.NEAREST).save(D/'walk_edit_target.png')
print(D)
