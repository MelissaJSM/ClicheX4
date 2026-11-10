"""사용자 F1의 진행 상태를 보존하고 테스트 사본의 X 그래픽만 새 ARC로 갱신한다."""
import argparse,gzip,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import locate_vram

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--source-sha256',required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 source=args.source.resolve();output=args.output.resolve();build=args.build.resolve()
 if not source.is_relative_to(ROOT/'work') or not output.is_relative_to(ROOT/'work') or output.exists() or source==output or not build.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Isolated source/output required')
 data=source.read_bytes()
 if sha256(data)!=args.source_sha256:raise ValueError('Save changed')
 state=gzip.decompress(data)
 if len(state)!=4254418 or not state.startswith(b'ePSXe\x06\x00SLUS_005.61'):raise ValueError('Unsupported state')
 cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());extract=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';old=(extract/'original.arc').read_bytes();new=(build/'modified.arc').read_bytes();manifest=json.loads((build/'manifest.json').read_text())
 if sha256(old)!=cfg['archive']['sha256'] or sha256(new)!=manifest['modified_archive_sha256']:raise ValueError('Unexpected ARC')
 exe=(extract/'original.exe').read_bytes();addr=cfg['idle_sequence_address'];off=2048+addr-cfg['executable']['load_address'];anchor=exe[off:off+48];hit=state.find(anchor)
 if hit<0 or state.find(anchor,hit+1)>=0:raise ValueError('Ambiguous RAM')
 rampos=hit-(addr&0x1fffff);ram=state[rampos:rampos+0x200000];player=ram[0x1418c8:0x1418c8+0xe4]
 if player[2]!=0 or player[0x17]!=5 or player[0x47]!=0:raise ValueError('Expected base X idle checkpoint')
 dst=bytearray(state);allowed=bytearray(len(state));ranges=[]
 def replace(pos,before,after,kind):
  if len(before)!=len(after) or state[pos:pos+len(before)]!=before:raise ValueError('Asset range mismatch')
  dst[pos:pos+len(after)]=after;allowed[pos:pos+len(after)]=bytes([1])*len(after);ranges.append({'kind':kind,'offset':pos,'size':len(after),'before_sha256':sha256(before),'after_sha256':sha256(after)})
 def entries(arc):
  return {int(e['type'],16):arc[e['offset']:e['offset']+e['size']] for e in psx_arc(arc)}
 oldes,newes=entries(old),entries(new)
 for kind in (2,3,9):
  before=oldes[kind];pos=ram.find(before)
  if pos<0 or ram.find(before,pos+1)>=0:raise ValueError('Asset entry is not unique in RAM')
  replace(rampos+pos,before,newes[kind],f'RAM ARC entry {kind}')
 oldpal,newpal=oldes[9][:32],newes[9][:32];palhits=[];pos=0
 while True:
  pos=ram.find(oldpal,pos)
  if pos<0:break
  replace(rampos+pos,oldpal,newpal,'RAM base palette copy');palhits.append(pos);pos+=32
 if len(palhits)!=5:raise ValueError('Unexpected base palette copies')
 desc=graphics_bank(oldes[2],0,allow_bank_aliases=True)['frames'][0];newdesc=graphics_bank(newes[2],0,allow_bank_aliases=True)['frames'][0]
 if desc['tile_count']!=newdesc['tile_count']:raise ValueError('Active texture tile count changed')
 before=decode_stream(oldes[2],desc['offset'],desc['limit'],desc['tile_count']*128).data;after=decode_stream(newes[2],newdesc['offset'],newdesc['limit'],newdesc['tile_count']*128).data;pos=ram.find(before)
 if pos<0 or ram.find(before,pos+1)>=0:raise ValueError('Active texture buffer not unique')
 replace(rampos+pos,before,after,'RAM decoded idle texture');video=locate_vram(state,before,desc['tile_count']);offset=0
 for first in range(0,desc['tile_count'],16):
  width=min(16,desc['tile_count']-first)*8
  for row in range(16):
   pos=video+(first//16*16+row)*2048+320*2;replace(pos,before[offset:offset+width],after[offset:offset+width],'VRAM active player tile row');offset+=width
 clut=struct.unpack_from('<H',player,0x42)[0];pos=video+(clut>>6)*2048+(clut&63)*32;replace(pos,oldpal,newpal,'VRAM base player CLUT')
 changed=[i for i,(x,y) in enumerate(zip(state,dst)) if x!=y]
 if any(not allowed[i] for i in changed) or dst[rampos+0x1418c8:rampos+0x1418c8+0xe4]!=player:raise ValueError('Non-graphic state changed')
 output.parent.mkdir(parents=True,exist_ok=True);result=gzip.compress(bytes(dst),mtime=0)
 with output.open('xb') as f:f.write(result)
 report={'source':str(source.relative_to(ROOT)),'source_sha256':sha256(data),'output_sha256':sha256(result),'build':str(build.relative_to(ROOT)),'build_bin_sha256':manifest['modified_bin']['sha256'],'ram_offset':rampos,'vram_offset':video,'changed_bytes':len(changed),'asset_ranges':ranges,'gameplay_state_preserved':True,'player_object_preserved':True,'original_save_preserved':sha256(source.read_bytes())==args.source_sha256,'runtime_evidence_kind':'asset-refreshed checkpoint; does not itself prove fresh disc loading'}
 (output.parent/'refresh.json').write_text(json.dumps(report,indent=2));print(json.dumps({'output':str(output),'sha256':sha256(result),'changed_bytes':len(changed),'gameplay_state_preserved':True}))
if __name__=='__main__':main()
