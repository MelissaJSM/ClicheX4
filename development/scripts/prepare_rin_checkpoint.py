"""두 번째 모드 전용 체크포인트의 그래픽만 갱신한다. 게임 진행·VRAM은 보존한다."""
import argparse,gzip,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.build_rin_idle import entry,sha
from src.psx_player import graphics_bank,decode_stream,composition_frame

def refresh(state,old,new,rampos):
    ram=state[rampos:rampos+0x200000]
    if len(ram)!=0x200000:raise ValueError('RAM outside state')
    player=ram[0x1418c8:0x1418c8+0xe4];n=player[0x47]
    if player[2]!=1 or player[0x17]!=5 or n not in (0,1,2,146,147,148):raise ValueError('Expected Rin idle checkpoint')
    before={k:entry(old,k)[1] for k in (2,3,9)};after={k:entry(new,k)[1] for k in (2,3,9)}
    if before[9]!=after[9]:raise ValueError('Palette changed; a fresh boot is required')
    for b in (0,1):
        if graphics_bank(before[2],b)!=graphics_bank(after[2],b):raise ValueError('Graphics addresses changed')
    active=[]
    for es in (before,after):
        f=graphics_bank(es[2],0)['frames'][n]
        active.append(decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data)
    if active[0]!=active[1] or composition_frame(before[3],0,n)!=composition_frame(after[3],0,n):raise ValueError('Active pose changed; a fresh boot is required')
    if ram[0x16dea8:0x16dea8+len(active[0])]!=active[0]:raise ValueError('Active decoded texture does not match')
    dst=bytearray(state);allowed=bytearray(len(state));ranges=[]
    for kind in (2,3):
        a,b=before[kind],after[kind];offset=ram.find(a)
        if len(a)!=len(b) or offset<0 or ram.find(a,offset+1)>=0:raise ValueError('Asset not uniquely identified in RAM')
        pos=rampos+offset;dst[pos:pos+len(b)]=b;allowed[pos:pos+len(b)]=bytes([1])*len(b)
        ranges.append({'entry':kind,'offset':pos,'size':len(b),'before_sha256':sha(a),'after_sha256':sha(b)})
    changed=[i for i,(a,b) in enumerate(zip(state,dst)) if a!=b]
    if any(not allowed[i] for i in changed) or dst[rampos+0x1418c8:rampos+0x1418c8+0xe4]!=player:raise ValueError('Gameplay state changed')
    return bytes(dst),{'active_frame':n,'changed_bytes':len(changed),'asset_ranges':ranges,'player_and_nonasset_bytes_preserved':True,'active_texture_and_palette_preserved':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--source-sha256',required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    source,output,parent,build=[v.resolve() for v in (a.source,a.output,a.parent,a.build)]
    if not source.is_relative_to(ROOT/'work/ver_rin_nana') or not output.is_relative_to(ROOT/'work/ver_rin_nana/checkpoints') or output.exists() or source==output or any(not v.is_relative_to(ROOT/'out/ver_rin_nana') for v in (parent,build)):raise ValueError('Isolated Rin paths required')
    data=source.read_bytes()
    if sha(data)!=a.source_sha256:raise ValueError('Checkpoint source hash mismatch')
    state=gzip.decompress(data)
    if len(state)!=4254418 or not state.startswith(b'ePSXe\x06\x00SLUS_005.61'):raise ValueError('Unsupported checkpoint')
    manifests=[json.loads((d/'manifest.json').read_text('utf-8')) for d in (parent,build)];arcs=[(d/'modified.arc').read_bytes() for d in (parent,build)]
    if any(m['task']!='zero_rin' or sha(arc)!=m['modified_archive_sha256'] for arc,m in zip(arcs,manifests)):raise ValueError('Build identity mismatch')
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'))
    exe=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.exe').read_bytes()
    addr=profile['zero_animation_table_address'];load=struct.unpack_from('<I',exe,0x18)[0];off=2048+addr-load;anchor=exe[off:off+64];hit=state.find(anchor)
    if len(anchor)!=64 or hit<0 or state.find(anchor,hit+1)>=0:raise ValueError('Ambiguous executable anchor')
    rampos=hit-(addr&0x1fffff);result,report=refresh(state,*arcs,rampos);packed=gzip.compress(result,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as stream:stream.write(packed)
    report.update({'source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(data),'output_sha256':sha(packed),'parent':parent.relative_to(ROOT).as_posix(),'build':build.relative_to(ROOT).as_posix(),'build_sha256':manifests[1]['modified_bin']['sha256'],'ram_offset':rampos,'source_preserved':digest(source)==a.source_sha256,'runtime_evidence_kind':'asset-refreshed checkpoint; not proof of fresh disc loading'})
    (output.parent/'refresh.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps(report))

if __name__=='__main__':main()
