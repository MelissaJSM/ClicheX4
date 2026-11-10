from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
D=P/'walk_design_basis';worlds=np.load(D/'worlds_probe.npz');numbers=[22,24,25,27,33]
sheet=Image.new('RGBA',(216,160))
for i,n in enumerate(numbers):
    a=worlds[str(n)][20:100,28:100];m=a!=0;r=np.zeros((80,72,4),dtype=np.uint8);r[m,:3]=colors[a[m]-1];r[m,3]=255;sheet.alpha_composite(Image.fromarray(r),(i%3*72,i//3*80))
sheet.resize((1296,960),Image.Resampling.NEAREST).save(D/'fit_edit_target.png')
