"""실측한 아머 대기 저장의 자산만 갱신한다. 원본은 보존한다."""
import argparse,gzip,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import sha256
from scripts.analyze_shibuki_armor import entries
from src.psx_player import graphics_bank,decode_stream,composition_frame

def refresh(state,old,new,rampos):
    ram=state[rampos:rampos+0x200000];player=ram[0x1418c8:0x1418c8+0xe4]
    if len(ram)!=0x200000 or player[2]!=0 or player[0x17]!=5 or player[0x47] not in (0,115,116,117,118,119) or player[0xa7]!=15: raise ValueError('Expected full armor idle')
    oes,nes=entries(old),entries(new)
    if oes[9]!=nes[9]: raise ValueError('Palette refresh is unsupported')
    n=player[0x47];raws=[]
    for es in (oes,nes):
        f=graphics_bank(es[2],0,allow_bank_aliases=True)['frames'][n]
        raws.append(decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data)
    if raws[0]!=raws[1] or any(composition_frame(oes[3],b,n)!=composition_frame(nes[3],b,n) for b in (0,5,6,7,8)): raise ValueError('Active frame differs; VRAM refresh needed')
    dst=bytearray(state);allowed=bytearray(len(state));ranges=[]
    for kind in (2,3,9):
        before,after=oes[kind],nes[kind];pos=ram.find(before)
        if len(before)!=len(after) or pos<0 or ram.find(before,pos+1)>=0: raise ValueError('Asset not uniquely identified')
        start=rampos+pos;dst[start:start+len(after)]=after;allowed[start:start+len(after)]=bytes([1])*len(after)
        ranges.append({'entry':kind,'offset':start,'size':len(after),'before_sha256':sha256(before),'after_sha256':sha256(after)})
    changed=[i for i,(a,b) in enumerate(zip(state,dst)) if a!=b]
    if any(not allowed[i] for i in changed) or dst[rampos+0x1418c8:rampos+0x1418c8+0xe4]!=player: raise ValueError('Gameplay state changed')
    return bytes(dst),{'active_frame':n,'armor_mask':player[0xa7],'arm_type':player[0xb8],'changed_bytes':len(changed),'ranges':ranges,'player_preserved':True,'vram_preserved':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--source-sha256',required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    source,output,parent,build=[v.resolve() for v in (a.source,a.output,a.parent,a.build)]
    if not source.is_relative_to(ROOT/'work') or not output.is_relative_to(ROOT/'work') or output.exists() or source==output or any(not v.is_relative_to(ROOT/'out/ver_buki_riko') for v in (parent,build)): raise ValueError('Isolated paths required')
    data=source.read_bytes()
    if sha256(data)!=a.source_sha256: raise ValueError('Checkpoint hash mismatch')
    state=gzip.decompress(data)
    if len(state)!=4254418 or not state.startswith(b'ePSXe\x06\x00SLUS_005.61'): raise ValueError('Unsupported checkpoint')
    manifests=[json.loads((b/'manifest.json').read_text(encoding='utf-8')) for b in (parent,build)]
    if manifests[0]['task']!=manifests[1]['task'] or manifests[0]['task'] not in ('fourth_armor_shibuki','ultimate_armor_shibuki'):raise ValueError('Armor task mismatch')
    ultimate=manifests[0]['task']=='ultimate_armor_shibuki'
    arcs=[(b/('PL02_U.ARC' if ultimate else 'modified.arc')).read_bytes() for b in (parent,build)]
    if any(sha256(arc)!=m['modified_archive_sha256'] for m,arc in zip(manifests,arcs)): raise ValueError('Armor ARC mismatch')
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());exe=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.exe').read_bytes()
    addr=cfg['idle_sequence_address'];off=2048+addr-cfg['executable']['load_address'];anchor=exe[off:off+48];hit=state.find(anchor)
    if hit<0 or state.find(anchor,hit+1)>=0: raise ValueError('Ambiguous RAM')
    rampos=hit-(addr&0x1fffff)
    if ultimate and state[rampos+0x1721f7]!=1:raise ValueError('Expected Ultimate acquired save')
    dst,report=refresh(state,*arcs,rampos);result=gzip.compress(dst,mtime=0)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as f:f.write(result)
    report.update({'source':str(source.relative_to(ROOT)),'source_sha256':sha256(data),'output_sha256':sha256(result),'build':str(build.relative_to(ROOT)),'build_bin_sha256':manifests[1]['modified_bin']['sha256'],'ram_offset':rampos,'original_preserved':sha256(source.read_bytes())==a.source_sha256,'runtime_evidence_kind':'asset-refreshed checkpoint; not proof of fresh disc loading'})
    (output.parent/'refresh.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
