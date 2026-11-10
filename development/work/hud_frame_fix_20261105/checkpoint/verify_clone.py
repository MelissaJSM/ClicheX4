"""최종 clone manifest를 입력으로 별도 디스크 추출/주소식/실제 CLI 거부 검사."""
import argparse,gzip,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_common import read_disc
from scripts.prepare_riko_ui import entry
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(folder):
    folder=folder.resolve()
    assert folder.is_relative_to(Path(__file__).parent)
    evidence=folder/'independent_verification.json'
    assert not evidence.exists()
    m=json.loads((folder/'manifest.json').read_text('utf8'))
    source,target,oldbin,newbin=[ROOT/m[k]for k in('source','output','source_bin','target_bin')]
    assert target.parent==folder
    assert digest(source)==m['source_sha256']and digest(target)==m['output_sha256']
    assert digest(oldbin)==m['source_bin_sha256']and digest(newbin)==m['target_bin_sha256']
    name=m['source_player_archive']
    old,new=[entry(read_disc(p,[name])[0][name],0x10206)for p in(oldbin,newbin)]
    a,b=[gzip.decompress(p.read_bytes())for p in(source,target)]
    assert len(a)==len(b)==4254418
    vr=2569183;mapping={}
    for i,(x,y)in enumerate(zip(old,new)):
        if x==y:continue
        row,col=divmod(i,128);stripe,yrow=divmod(row,80)
        at=vr+(176+yrow)*2048+640+stripe*128+col
        if a[at]!=y:mapping[at]=(a[at],y)
    diff={i:(x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y}
    assert diff==mapping
    assert a[442:442+2097152]==b[442:442+2097152]
    assert a[:vr]==b[:vr]and a[vr+1048576:]==b[vr+1048576:]
    atlas=b''.join(b[vr+(176+r%80)*2048+640+r//80*128:vr+(176+r%80)*2048+768+r//80*128]for r in range(880))
    assert atlas==new
    args={'--source':str(source),'--source-sha256':m['source_sha256'],'--source-bin':str(oldbin),
        '--source-bin-sha256':m['source_bin_sha256'],'--target-bin':str(newbin),
        '--target-bin-sha256':m['target_bin_sha256'],'--output':str(folder.parent/(folder.name+'_negative_cli_output'))}
    rejects=[]
    for option,value,error in [('--source-sha256','0'*64,'Source checkpoint hash differs'),
                              ('--source-bin-sha256','0'*64,'Source BIN hash differs'),
                              ('--target-bin-sha256','0'*64,'Target BIN hash differs'),
                              ('--output',str(source),'Output must be a fresh directory'),
                              ('--output',str(folder),'Output directory already exists')]:
        bad=dict(args);bad[option]=value
        command=[sys.executable,str(ROOT/'scripts/hud_frame_checkpoint.py')]
        for k,v in bad.items():command.extend((k,v))
        result=subprocess.run(command,capture_output=True,text=True)
        assert result.returncode!=0 and error in result.stderr,(option,result.stdout,result.stderr)
        assert not Path(args['--output']).exists()
        rejects.append(dict(option=option,expected_rejection=error,returncode=result.returncode,no_output_written=True))
    assert digest(source)==m['source_sha256']and digest(target)==m['output_sha256']
    result=dict(passed=True,source_sha256=m['source_sha256'],output_sha256=m['output_sha256'],
        independent_expected_VRAM_changes=len(mapping),actual_state_changes=len(diff),
        all_changed_bytes_are_exact_texture_deltas=True,entire_RAM_preserved=True,
        all_non_VRAM_including_SPU_preserved=True,complete_static_atlas_matches_target=True,
        actual_CLI_rejections=rejects,active_F1_or_cards_written=False,runtime_verified=False)
    evidence.write_text(json.dumps(result,indent=2)+'\n','utf8')
    print(json.dumps(result))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,required=True);a=parser.parse_args();main(a.folder)
