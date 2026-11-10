from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
R=P/'gait_cape_repair';U=P/'upper_body_repair';U.mkdir(exist_ok=True)
sheet=Image.new('RGBA',(192,144))
for j,n in enumerate([7,10,12,14,17,19]):
 a=np.array(Image.open(R/f'frame_{n:03d}.png'));b=geometry[n][1];w=np.zeros((128,128),dtype=np.uint8);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=a;a=w[24:96,32:96];rgba=np.zeros((72,64,4),dtype=np.uint8);m=a!=0;rgba[m,:3]=colors[a[m]-1];rgba[m,3]=255;sheet.alpha_composite(Image.fromarray(rgba),(j%3*64,j//3*72))
sheet.resize((1536,1152),Image.Resampling.NEAREST).save(U/'upper_edit_reference.png')
print(U)
