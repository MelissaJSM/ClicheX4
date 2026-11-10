import gzip,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_common import read_disc
from scripts.prepare_riko_ui import entry
def sha(b):return hashlib.sha256(b).hexdigest()
source=ROOT/'work/overhaul_20261105/hud_frame_followup/live_progress/SLUS_005.61.000'
target=ROOT/'work/hud_frame_fix_20261105/checkpoint/nana_final_v1/SLUS_005.61.000'
oldbin=ROOT/'out/ver_rin_nana/overhaul_20261105_candidate04/rin_nana.bin'
newbin=ROOT/'out/ver_rin_nana/hud_frame_fix_20261105_v1/rin_nana.bin'
old,new=[entry(read_disc(p,['PL02_U.ARC'])[0]['PL02_U.ARC'],0x10206)for p in(oldbin,newbin)]
a,b=[gzip.decompress(p.read_bytes())for p in(source,target)]
vr=2569183; mapping={}
for i,(x,y)in enumerate(zip(old,new)):
    if x==y:continue
    row,col=divmod(i,128);stripe,yrow=divmod(row,80)
    at=vr+(176+yrow)*2048+640+stripe*128+col
    mapping[at]=(x,y)
diff={i:(x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y}
assert diff==mapping and len(diff)==25
assert a[442:442+2097152]==b[442:442+2097152]
assert a[:vr]==b[:vr]and a[vr+1048576:]==b[vr+1048576:]
atlas=b''.join(b[vr+(176+r%80)*2048+640+r//80*128:vr+(176+r%80)*2048+768+r//80*128]for r in range(880))
assert atlas==new
manifest=json.loads(target.with_name('manifest.json').read_text('utf8'))
assert sha(target.read_bytes())==manifest['output_sha256']
args={'--source':str(source),'--source-sha256':sha(source.read_bytes()),'--source-bin':str(oldbin),
      '--source-bin-sha256':'1a2d97272bb0dde2395aa7f1daa9136dd247125456090ff519fe3c484e3be2e2',
      '--target-bin':str(newbin),'--target-bin-sha256':'2c3cf873615cab8c84fd7a5dc8a6260d95e6bea26b84de5c87d08651e6ce53dc',
      '--output':str(target.parent.parent/'negative_cli_output')}
rejects=[]
for option,value,error in [('--source-sha256','0'*64,'Source checkpoint hash differs'),
                           ('--source-bin-sha256','0'*64,'Source BIN hash differs'),
                           ('--target-bin-sha256','0'*64,'Target BIN hash differs'),
                           ('--output',str(source),'Output must be a fresh directory'),
                           ('--output',str(target.parent),'Output directory already exists')]:
    bad=dict(args);bad[option]=value
    command=[sys.executable,str(ROOT/'scripts/hud_frame_checkpoint.py')]
    for k,v in bad.items():command.extend((k,v))
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode!=0 and error in result.stderr,(option,result.stdout,result.stderr)
    assert not Path(args['--output']).exists()
    rejects.append(dict(option=option,expected_rejection=error,returncode=result.returncode,no_output_written=True))
result=dict(passed=True,source_sha256=sha(source.read_bytes()),output_sha256=sha(target.read_bytes()),
    independent_expected_VRAM_changes=len(mapping),actual_state_changes=len(diff),all_changed_bytes_are_exact_texture_deltas=True,
    entire_RAM_preserved=True,all_non_VRAM_including_SPU_preserved=True,complete_static_atlas_matches_target=True,
    actual_CLI_rejections=rejects,active_F1_or_cards_written=False,runtime_verified=False)
target.with_name('independent_verification.json').write_text(json.dumps(result,indent=2)+'\n','utf8')
print(json.dumps(result))
