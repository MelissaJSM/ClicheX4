"""승리4참조/선택18을 사다리 누적 고정본 위에 무손실 패킹한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from scripts.export_x_consistency import Archive,page
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_disc import file_hash
import pack_lowhp_return as engine
from sync_victory_selection import patch as patch_ui
PARENT_SHA='76f19a188ad58dd447eec058b669f8d62a4b8c00f957de3b229aeaa67f37495b';REFS=set(range(204,208))

def targets():
 manifest=H/'victory_parts01/art_manifest.json';need(sha(manifest.read_bytes())=='f8308711855117ab2ace31b6512e4e863a7373b3a2618701651483854b5f6cdd','Native art manifest changed')
 for name,expected in json.loads(manifest.read_text('utf8')).items():need(sha((H/name).read_bytes())==expected,'Frozen source art changed')
 return {n:{b:np.array(Image.open(H/f'victory_parts01/{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}for n in REFS}

def pack(parent,wants):
 need(sha(parent)==PARENT_SHA,'Wrong ladder checkpoint');need(set(wants)==REFS,'Wrong victory refs')
 expected=targets()
 for n in REFS:
  need(set(wants[n])=={0,5,6,7,8},'Wrong layers')
  for b,v in wants[n].items():need(v.dtype==np.uint8 and v.shape==(384,384)and np.array_equal(v,expected[n][b]),'Wrong native target')
 oldsha,oldrefs=engine.ARC_SHA,engine.SELECTED
 try:
  engine.ARC_SHA=PARENT_SHA;engine.SELECTED=REFS;result,proof=engine.pack(parent,wants)
 finally:engine.ARC_SHA=oldsha;engine.SELECTED=oldrefs
 proof.pop('new_body_and_accepted_idle_head',None);proof.update(new_whole_art=True,old_coarse_head_body_overwrite=False)
 return result,proof

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();out=H/args.output;need(out.is_relative_to(H)and not out.exists(),'Output conflict');out.mkdir()
 need(file_hash(SOURCE)==SOURCE_SHA,'Baseline changed');assets,_=read_disc(SOURCE,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))
 parent=(H/'prepared_ladder_wall_front02/PL00_U.ARC').read_bytes();old_ui=(H/'prepared_ladder_wall_front02/ST0E_U1.ARC').read_bytes()
 try:result,proof=pack(parent,targets());ui,uiproof,old,new=patch_ui(parent,result,old_ui,entry(assets['COL0E_U1.ARC'],5))
 except ValueError as e:write(out/'capacity_failure.json',dict(error=str(e),no_arc_written=True));raise
 (out/'PL00_U.ARC').write_bytes(result);(out/'ST0E_U1.ARC').write_bytes(ui);write(out/'verification.json',proof);write(out/'ui_verification.json',uiproof)
 write(out/'proposal.json',dict(project='ver_buki_riko',baseline_sha256=SOURCE_SHA,files={name:dict(path=(out/name).relative_to(ROOT).as_posix(),before=sha(assets[name]),after=sha(data))for name,data in [('PL00_U.ARC',result),('ST0E_U1.ARC',ui)]},replaces='prepared_ladder_wall_front02/proposal.json'))
 before=Archive(parent);after=Archive(result)
 for label,mask in [('base',0),('fourth',15)]:page([(f'{n} {name}',a.composite(n,mask)[0])for n in sorted(REFS)for name,a in [('before',before),('actual',after)]],after.composite(0,mask)[0],out/f'{label}_comparison.png',cols=2,scale=4)
 for n in REFS:page([(f'{n} mask{m:X}',after.composite(n,m)[0])for m in range(16)],after.composite(0,15)[0],out/f'partial_{n:03}.png',cols=4,scale=3)
 page([('selection18 before',after.rgba(old)),('selection18 after',after.rgba(new)),('game207 after',after.composite(207,0)[0])],after.composite(0,0)[0],out/'selection18_comparison.png',cols=3,scale=4)
 print(json.dumps(dict(passed=True,game_sha256=sha(result),ui_sha256=sha(ui),groups=proof['groups'],slack=proof['parts_slack'],ui=uiproof)))
if __name__=='__main__':main()
