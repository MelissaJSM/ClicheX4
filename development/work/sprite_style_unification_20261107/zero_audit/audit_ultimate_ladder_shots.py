"""Read original US ladder shot frame relations; no producer modules or writes."""
from pathlib import Path
import hashlib, json, struct, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
D = Path(__file__).parent
O = D/'ultimate_ladder_shots01'
O.mkdir(exist_ok=True)
assets, _ = read_disc(ROOT/'MegaMan X4.bin', ('PL00_U.ARC','PL02_U.ARC','SLUS_005.61'))
sha = lambda b: hashlib.sha256(b).hexdigest()
old = json.loads((D/'ultimate_ladder_aliases01/report.json').read_text('utf8'))
rows=[]; extra_comparisons=[]
def bbox(m):
    ys,xs=np.nonzero(m)
    return [int(xs.min()-160),int(ys.min()-160),int(xs.max()-159),int(ys.max()-159)] if len(xs) else None
for name,data in assets.items():
    if not name.endswith('.ARC'):continue
    a=Archive(data)
    for n in (149,150,154,155):
        f=a.banks[0]['frames'][n]
        row={'archive':name,'ref':n,'stream':{k:v for k,v in f.items() if k!='raw'},'layers':{}}
        for b in (0,5,6,7,8):
            x=a.layer(n,b)[0]; ref=a.layer(149,b)[0]; mask=x!=ref
            row['layers'][str(b)]={'parts':composition_frame(a.c,b,n)['parts'],
                'difference_to_149':int(mask.sum()),'difference_bbox':bbox(mask),
                'pixel_diff':[{'x':int(xx-160),'y':int(yy-160),'149':int(ref[yy,xx]),'target':int(x[yy,xx])}for yy,xx in zip(*np.nonzero(mask))]}
        rows.append(row)
    for left,right in ((149,150),(150,155),(154,155)):
        layers={}
        for b in (0,5,6,7,8):
            s=a.layer(left,b)[0];t=a.layer(right,b)[0];delta=s!=t
            layers[str(b)]={'difference_pixels':int(delta.sum()),'bbox':bbox(delta)}
        extra_comparisons.append({'archive':name,'source':left,'target':right,'layers':layers})
    board=Image.new('RGB',(4*276,2*380),'#263345');dr=ImageDraw.Draw(board)
    for j,n in enumerate((149,150,154,155)):
        for k,mask in enumerate((0,15)):
            im=a.composite(n,mask,1)[0].crop((128,112,192,200)).resize((256,352),Image.Resampling.NEAREST)
            board.paste(im,(j*276+10,k*380+22),im)
            dr.text((j*276+5,k*380+3),f'{name} ref{n} mask{mask}',fill='white')
    board.save(O/(name.replace('.ARC','')+'.png'))
exe=assets['SLUS_005.61']; base=struct.unpack_from('<I',exe,24)[0]
at=lambda address,size:exe[address-base+2048:address-base+2048+size]
cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
code=[{'pc':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}for i in cs.disasm(at(0x800387f4,0x60),0x800387f4)]
assert any(i['operands']=='$v0, $zero, 0x5d'for i in code)
r={'scope':'원US 두 ARC 사다리149/150/154/155 정적 조립·색인 관계. 새그림/실기 검증 아님.',
   'input_hashes':{n:sha(b)for n,b in assets.items()},'prior_native_sequence_evidence':{'path':str((D/'ultimate_ladder_aliases01/report.json').relative_to(ROOT)),'sha256':sha((D/'ultimate_ladder_aliases01/report.json').read_bytes())},
   'sequences':[x for x in old['original_exe_sequences']if x['id']in(28,29,92,93)],'frames':rows,'comparisons':extra_comparisons,
   'caller':{'native_function':hex(0x800387f4),'instructions':code,'shot_type_table_address':'0x800F8D44','shot_type_table_bytes':at(0x800f8d44,24).hex(),'note':'last_shot_type로92/93을고른다.93의첫150 유지시간은attack_pose_timer-8로덮어써지므로표96을실제항상96호출로설명하지않는다.'},
   'actual_sheet_views':True,'viewed_sheets':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in sorted(O.glob('PL0?_U.png'))],
   'conclusions':[
       '150은149와동일raw이며base의머리·앞팔쪽기록만바뀐다. base y>=4의하체와PL00 leg8전체는정확동일하다. Ultimate overlay5는원전신아머를포함하므로변경범위를base의팔박스로제한할수없다.',
       '155는150의짧은사격반동그림이다. 원표92/93 모두150→155→150이며,몸체/하체도새로조립한별도stream이라149+새팔전체exact라는관계는성립하지않는다.',
       '실제두판에서155는뻗은팔을뒤로당겨총열을약간위로젖히고허리·한쪽발도변한반동이다.154는고개를숙인사다리상단전환그림으로155의몸체짝이아니다.154는28/29표에서153/183과연결된다.',
       '현재수용base의149몸체공통정책은새제작범위의선택이며원US155복원이아니다. 새Ultimate에서도이를택하면몸체고정/팔반동의미를명시하고원손·총구좌표및150→155→150순서를확인한다. 원US반동의하체움직임을모두그대로재현했다는표현은피한다.'
   ],'limits':['원US색인·조립·원표/호출자명령읽기와두비교판실제열람이다. MIPS실행·새원화제작·게임실기는없다.','새155전신의최종정책결정은담당자/루트미술검토이며이보고서가새폼최종수용을대체하지않는다.']}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
for r in rows:print(r['archive'],r['ref'],r['stream'],[(b,l['difference_to_149'],l['difference_bbox'])for b,l in r['layers'].items()])
print('sequences',json.dumps([x for x in old['original_exe_sequences']if x['id']in(92,93)]))
