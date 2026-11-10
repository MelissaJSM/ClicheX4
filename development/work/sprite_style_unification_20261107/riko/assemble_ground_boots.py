"""원본에서 같은 부츠 픽셀만 입증해 공유하고 각 자세 상체를 보호한다."""
from pathlib import Path
import sys, json, hashlib, struct
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.overhaul_sprites_audit import render, rgba
from scripts.prepare_riko_ui import entry
D = Path(__file__).resolve().parent / 'ground_boots19'
OUT = D / 'targets02'
OUT.mkdir(exist_ok=False)
reg = json.loads((D / 'registered01/registration.json').read_text('utf8'))
sha = lambda b: hashlib.sha256(b).hexdigest()
arc = (ROOT / reg['source_arc']).read_bytes()
assert sha(arc) == reg['source_sha256']
masters = {}
for r in reg['frames']:
    p = ROOT / r['target']
    assert sha(p.read_bytes()) == r['target_sha256']
    masters[r['ref']] = np.array(Image.open(p))
# (175,174) belongs to the cape boundary, not to the boot.
masters[91][174,175] = render(arc, 0, 0, 91)[0][174,175]
mapping = {61: (61,0), 71: (71,0), 75:(71,0), 91:(91,0), 93:(91,1),
           95:(91,1), 97:(91,0), 99:(91,0), 101:(91,0)}
targets = {}
rows = []
for n,(master,dx) in mapping.items():
    before = render(arc,0,0,n)[0]
    original_master = render(arc,0,0,master)[0]
    edited_master = masters[master]
    y,x = np.where(original_master != edited_master)
    assert np.array_equal(before[y,x+dx],original_master[y,x]), f'Boot sharing mismatch {n}'
    after = before.copy()
    after[y,x+dx] = edited_master[y,x]
    assert np.array_equal(after>0,before>0)
    assert np.array_equal(after[:172],before[:172])
    p = OUT / f'b0_{n:03}_indices.png'
    Image.fromarray(after).save(p)
    rows.append(dict(bank=0,ref=n,target=str(p.relative_to(ROOT)),target_sha256=sha(p.read_bytes()),
                     boot_master=master,translation_from_boot_master=[dx,0],
                     original_changed_texels_match_master=True,changed_pixels=int(len(x)),
                     all_other_texels_and_alpha_exact=True))
    targets[n]=after
for label,row in [('normal',0),('black',13)]:
    pal=struct.unpack_from('<16H',entry(arc,9),row*32)
    for start in range(0,len(targets),4):
        items=list(targets.items())[start:start+4]
        sheet=Image.new('RGB',(1152,400*len(items)),'#64717b');draw=ImageDraw.Draw(sheet)
        for j,(n,q)in enumerate(items):
            for c,(title,a)in enumerate([('idle',render(arc,0,0,147)[0]),('before',render(arc,0,0,n)[0]),('boot detail',q)]):
                im=rgba(a,pal).crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST)
                sheet.paste(im,(c*384,j*400+16),im);draw.text((c*384+4,j*400+2),f'{n} {title}',fill='white')
        sheet.save(OUT/f'{label}_comparison_{start//4:02}.png')
(OUT/'registration.json').write_text(json.dumps(dict(source_arc=reg['source_arc'],source_sha256=reg['source_sha256'],
    generated_sha256=reg['generated_sha256'],frames=rows,material_only_repair=True,
    discarded_redundant_authored_95=True,original_gameplay_contacts_exact=True,
    full_art_unification_complete=False,runtime_verified=False),indent=2)+'\n','utf8')
print(json.dumps({'refs':list(targets),'changed_pixels':sum(r['changed_pixels']for r in rows)}))
