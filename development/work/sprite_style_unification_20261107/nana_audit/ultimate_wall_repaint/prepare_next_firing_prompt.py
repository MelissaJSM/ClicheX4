from pathlib import Path
D=Path(__file__).resolve().parent
p=(D/'prompt_firing_a_before_v1.txt').read_text('utf8')
p=p.replace('Cell order is 56 top left, 58 top right, 60 bottom left. The muzzle is 18, 19 and 19 native pixels left of the eye respectively','Cell order is 62 top left, 64 top right, 66 bottom left. The muzzle is 22, 24 and 22 native pixels left of the eye respectively')
(D/'prompt_firing_b_before_v1.txt').write_text(p,encoding='utf8')
