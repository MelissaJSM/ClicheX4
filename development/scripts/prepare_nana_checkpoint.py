"""나나 대기 체크포인트의 그래픽만 갱신한다. 진행·프로그램·VRAM은 그대로다."""
import argparse,gzip,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame

def refresh(state,old,new,rampos,refresh_body_palettes=False):
 ram=state[rampos:rampos+0x200000];player=ram[0x1418c8:0x1418c8+0xe4]
 if len(ram)!=0x200000 or len(player)!=0xe4 or player[2]!=0 or player[0x17]!=5 or player[0x47]not in (0,115,116,117,118,119) or player[0xa7]!=0:raise ValueError('Expected base Nana idle checkpoint')
 n=player[0x47]
 def entries(arc):return {int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)}
 before,after=entries(old),entries(new)
 kinds=[2,3]
 if before[9]!=after[9]:
  if not refresh_body_palettes:raise ValueError('Palette changed; fresh boot required')
  if player[0x93]!=0:raise ValueError('Body palette refresh requires default weapon')
  from scripts.prepare_shibuki_weapon_palette import edited_palette
  expected,_=edited_palette(before[9])
  if after[9]!=expected or before[9][:32]!=after[9][:32]:raise ValueError('Palette change exceeds known body rows')
  kinds.append(9)
 active=[]
 for es in (before,after):
  f=graphics_bank(es[2],0,allow_bank_aliases=True)['frames'][n];active.append(decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data)
 if active[0]!=active[1] or composition_frame(before[3],0,n)!=composition_frame(after[3],0,n):raise ValueError('Active frame changed; VRAM refresh required')
 if ram[0x16dea8:0x16dea8+len(active[0])]!=active[0]:raise ValueError('Active texture differs from parent')
 dst=bytearray(state);allowed=bytearray(len(state));ranges=[]
 for kind in kinds:
  a,b=before[kind],after[kind];offset=ram.find(a)
  if len(a)!=len(b) or offset<0 or ram.find(a,offset+1)>=0:raise ValueError('Parent graphic entry not uniquely identified')
  pos=rampos+offset;dst[pos:pos+len(b)]=b;allowed[pos:pos+len(b)]=bytes([1])*len(b);ranges.append({'entry':kind,'offset':pos,'size':len(b),'before_sha256':sha256(a),'after_sha256':sha256(b)})
 changes=[i for i,(a,b) in enumerate(zip(state,dst))if a!=b]
 if any(not allowed[i]for i in changes) or dst[rampos+0x1418c8:rampos+0x1418c8+0xe4]!=player:raise ValueError('Non-graphic state changed')
 return bytes(dst),{'active_frame':n,'changed_bytes':len(changes),'asset_ranges':ranges,'player_and_nonasset_bytes_preserved':True,'active_texture_and_palette_preserved':True,'body_palette_source_refreshed':9 in kinds,'ram_offset':rampos}

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--source-sha256',required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--refresh-body-palettes',action='store_true');a=p.parse_args();source,output,parent,build=[v.resolve()for v in (a.source,a.output,a.parent,a.build)]
 if not source.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') or not output.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') or output.exists() or output==source or any(not v.is_relative_to(ROOT/'out/ver_rin_nana')for v in (parent,build)):raise ValueError('Isolated Nana checkpoint paths required')
 data=source.read_bytes()
 if sha256(data)!=a.source_sha256:raise ValueError('Source checkpoint changed')
 state=gzip.decompress(data)
 if len(state)!=4254418 or not state.startswith(b'ePSXe\x06\x00SLUS_005.61'):raise ValueError('Unsupported checkpoint')
 manifests=[json.loads((b/'manifest.json').read_text('utf8'))for b in (parent,build)];arcs=[(b/'modified.arc').read_bytes()for b in (parent,build)]
 if any(m['task']!='x_nana' or sha256(arc)!=m['modified_archive_sha256']for m,arc in zip(manifests,arcs)):raise ValueError('Nana build identity mismatch')
 cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());exe=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.exe').read_bytes();addr=cfg['idle_sequence_address'];off=2048+addr-cfg['executable']['load_address'];anchor=exe[off:off+48];hit=state.find(anchor)
 if hit<0 or state.find(anchor,hit+1)>=0:raise ValueError('Ambiguous RAM anchor')
 updated,report=refresh(state,*arcs,hit-(addr&0x1fffff),refresh_body_palettes=a.refresh_body_palettes);packed=gzip.compress(updated,mtime=0);output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('xb')as f:f.write(packed)
 report.update(source=source.relative_to(ROOT).as_posix(),source_sha256=sha256(data),output_sha256=sha256(packed),parent=parent.relative_to(ROOT).as_posix(),build=build.relative_to(ROOT).as_posix(),build_sha256=manifests[1]['modified_bin']['sha256'],original_preserved=digest(source)==a.source_sha256,runtime_evidence_kind='graphics-refreshed checkpoint; not fresh disc loading proof')
 (output.parent/'refresh.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))
if __name__=='__main__':main()
