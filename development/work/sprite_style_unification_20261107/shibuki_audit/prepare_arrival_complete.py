"""승리 누적본에 등장9참조/광선 몸체/138포스 공유를 무손실 패킹한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from scripts.export_x_consistency import Archive,page
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash
from prepare_arrival_targets import make,REFS,PARENT_SHA
import pack_lowhp_return as engine

def targets(parent):
 a,wanted,owner,provenance=make(parent)
 manifest=json.loads((H/'arrival_targets01/art_manifest.json').read_text('utf8'))
 for name,expected in manifest.items():need(sha((H/name).read_bytes())==expected,'Native/source art changed: '+name)
 for n in REFS:
  for b,q in wanted[n].items():need(np.array_equal(q,np.array(Image.open(H/f'arrival_targets01/{n:03}_bank{b}_indices.png'))),'Source target reconstruction mismatch')
 return wanted,provenance

def pack(parent,wants):
 need(sha(parent)==PARENT_SHA,'Wrong victory checkpoint');expected,provenance=targets(parent);need(set(wants)==REFS,'Wrong arrival refs')
 for n in REFS:
  need(set(wants[n])=={0,5,6,7,8},'Wrong layer count')
  for b,v in wants[n].items():need(v.dtype==np.uint8 and v.shape==(384,384)and np.array_equal(v,expected[n][b]),'Wrong native target')
 oldsha,oldrefs=engine.ARC_SHA,engine.SELECTED
 try:
  engine.ARC_SHA=PARENT_SHA;engine.SELECTED=REFS;result,proof=engine.pack(parent,wants)
 finally:engine.ARC_SHA=oldsha;engine.SELECTED=oldrefs
 proof.pop('new_body_and_accepted_idle_head',None);proof.update(new_whole_art=True,old_coarse_head_body_overwrite=False,provenance=provenance,shared_132_repacked_same_display=True)
 return result,proof

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();out=H/args.output;need(out.is_relative_to(H)and not out.exists(),'Output conflict');out.mkdir()
 need(file_hash(SOURCE)==SOURCE_SHA,'Baseline changed');assets,_=read_disc(SOURCE,('PL00_U.ARC','ST0E_U1.ARC'))
 parent=(H/'prepared_victory_ladder01/PL00_U.ARC').read_bytes();ui=(H/'prepared_victory_ladder01/ST0E_U1.ARC').read_bytes();need(sha(ui)=='5afaa5877976c2d6c7ae38a3061c8b74401a04edaa6e8d639399c53028873695','UI dependency changed')
 try:result,proof=pack(parent,targets(parent)[0])
 except ValueError as e:write(out/'capacity_failure.json',dict(error=str(e),no_arc_written=True));raise
 (out/'PL00_U.ARC').write_bytes(result);(out/'ST0E_U1.ARC').write_bytes(ui);write(out/'verification.json',proof)
 write(out/'proposal.json',dict(project='ver_buki_riko',baseline_sha256=SOURCE_SHA,files={n:dict(path=(out/n).relative_to(ROOT).as_posix(),before=sha(assets[n]),after=sha(data))for n,data in[('PL00_U.ARC',result),('ST0E_U1.ARC',ui)]},replaces='prepared_victory_ladder01/proposal.json',selected_visual_refs=sorted(REFS),same_display_repacked=[132],unchanged_selection_from_victory=True))
 a=Archive(result);old=Archive(parent)
 for label,mask in(('base',0),('fourth',15)):
  keys=[133,135,136,137,138,139]if mask==0 else[138,139]
  page([(f'{n} {name}',q.composite(n,mask)[0])for n in keys for name,q in[('before',old),('actual',a)]],a.composite(0,mask)[0],out/f'{label}_comparison.png',cols=2,scale=4)
 for n in(138,139):page([(f'{n} mask{m:X}',a.composite(n,m)[0])for m in range(16)],a.composite(0,15)[0],out/f'partial_{n}.png',cols=4,scale=3)
 page([(f'{n} {name}',q.composite(n,0)[0])for n in(130,131,132,134,140)for name,q in[('before',old),('actual',a)]],a.composite(0,0)[0],out/'effects_comparison.png',cols=2,scale=4)
 print(json.dumps(dict(passed=True,sha256=sha(result),groups=proof['groups'],parts_slack=proof['parts_slack'],graphics=proof['graphics'])))
if __name__=='__main__':main()
