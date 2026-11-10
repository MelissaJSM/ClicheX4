"""Prepare current X/Force and Ultimate assets. Ultimate native selector remains separate."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,graphics_bank,decode_stream,indexed_atlas
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_player import dynamic_texture,static_texture
WORK=ROOT/'work/steam_port_20261109'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def verify_original_cof(tex,cof,gfx,bank_id):
    count=struct.unpack_from('<I',cof,17+cof[16])[0]
    ys=struct.unpack_from('<256I',cof,21+cof[16])
    bank=graphics_bank(gfx,bank_id,allow_bank_aliases=True)
    matches=[]
    for f in bank['frames'][:count]:
        packed=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        pixels,locations,h=indexed_atlas(packed,f['tile_count'])
        start=20+ys[f['index']]*256
        if start+len(pixels)>len(tex):raise ValueError('Original COF out of TEX range')
        if any(tex[start+j]!=v for j,v in enumerate(pixels) if locations[j] is not None):
            raise ValueError('Native COF entries do not match PS1 indexed pixels')
        matches.append(f['index'])
    return {'bank':bank_id,'native_count':count,'ps1_count':len(bank['frames']),'verified_native_indices':matches,
            'trailing_ps1_entries':'separate expanded mapping; native use not yet verified'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version',default='v1')
    args=p.parse_args()
    if args.version not in ('v1','v2','v3'):raise ValueError('Invalid version')
    inventory=json.loads((ROOT/'work/steam_port_research_20261109/inventory.json').read_text(encoding='utf-8'))
    originals,_=read_disc(Path(inventory['ps1_original']['path']),['PL00_U.ARC','PL02_U.ARC'])
    reports=[]
    for mode,suffix in [('ver_rin_nana',''),('ver_buki_riko','_eng')]:
        pointer=json.loads((ROOT/'projects'/mode/'current_build.json').read_text(encoding='utf-8'))
        source_bin=(ROOT/pointer['cue']).with_suffix('.bin')
        with source_bin.open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=pointer['sha256']:raise ValueError('Current PS1 source mismatch')
        sources,_=read_disc(source_bin,list(originals))
        for player in ('pl00','pl02'):
            name=player.upper()+'_U.ARC';source=sources[name];original=originals[name]
            target=player+suffix+'.arc'
            arc=SteamArc((WORK/'original/nativeDX10/X4/romPC'/target).read_bytes(),inventory['archives'][target]['sha256'])
            def find(name,magic):return next(e for e in arc.entries if e.name==name and e.payload[:4]==magic)
            updates={};rows=[];mapping=[]
            pat=find('X4\\pat\\pl\\'+player.upper(),b'PAT\0')
            if pat_from_ps1(entry(original,3))!=pat.payload:raise ValueError('Original PAT mismatch')
            updates[pat.key]=pat_from_ps1(entry(source,3))
            gfx=entry(source,2);original_gfx=entry(original,2)
            for bank_id in range(len(bank_offsets(gfx,allow_aliases=True))):
                internal=f'X4\\chr\\pl\\{player}\\{player}_{bank_id:03d}'
                tex,cof=find(internal,b'TEX\0'),find(internal,b'COF\0')
                mapping.append(verify_original_cof(tex.payload,cof.payload,original_gfx,bank_id))
                nt,nc,row=dynamic_texture(tex.payload,cof.payload,gfx,bank_id,allow_count_expansion=True,allow_npot_height=True)
                if bank_id==3:
                    # Charged Frost Tower uses tile base32 in the native renderer.
                    # PS1 repeats an upload for frames10..20; those references are
                    # NOT native COF Y offsets. Expanding them adds Y32 twice and
                    # samples transparent rows64+. Keep the verified native table.
                    of=graphics_bank(original_gfx,3,allow_bank_aliases=True)['frames']
                    nf=graphics_bank(gfx,3,allow_bank_aliases=True)['frames']
                    if len(of)!=len(nf):raise ValueError('Changed Frost frame count requires a new mapping')
                    for a,b in zip(of,nf):
                        if a['tile_count']!=b['tile_count'] or decode_stream(original_gfx,a['offset'],a['limit'],a['tile_count']*128).data!=decode_stream(gfx,b['offset'],b['limit'],b['tile_count']*128).data:
                            raise ValueError('Changed Frost artwork requires a new mapping')
                    if nt!=tex.payload:raise ValueError('Native Frost texture correspondence differs')
                    nc=cof.payload
                    row.update(native_cof_preserved=True,reason='Charged Frost tile base32 is applied separately')
                updates[tex.key]=nt;updates[cof.key]=nc;rows.append(row)
            tex=find('X4\\chr\\com\\COM00_000',b'TEX\0')
            updates[tex.key]=static_texture(tex.payload,entry(original,0x10206),entry(source,0x10206))
            col=find('X4\\col\\pl\\charge'+player[-2:],b'COL\0')
            if col.payload[12:]!=entry(original,9):raise ValueError('Original COL mismatch')
            updates[col.key]=col.payload[:12]+entry(source,9)
            result=arc.rebuild(updates)
            out=ROOT/'out'/mode/f'steam_x_20261109_{args.version}/nativeDX10/X4/romPC'/target
            out.parent.mkdir(parents=True,exist_ok=True)
            if out.exists() and out.read_bytes()!=result:raise ValueError('Existing output differs')
            out.write_bytes(result)
            changed=[{'name':e.name,'type':hex(e.kind),'before':sha(e.payload),'after':sha(updates[e.key])}
                     for e in arc.entries if e.key in updates and e.payload!=updates[e.key]]
            report={'mode':mode,'player':player,'target_arc':target,'source_bin':str(source_bin.relative_to(ROOT)),
                    'source_bin_sha256':pointer['sha256'],'original_sha256':sha(arc.raw),'output':str(out.relative_to(ROOT)),
                    'output_sha256':sha(result),'size':len(result),'changed_entries':changed,
                    'original_cof_correspondence':mapping,'dynamic_banks':rows,'runtime_verified':False,
                    'ultimate_selector_ported':False,'install_eligible':player=='pl00'}
            reports.append(report)
            print({'mode':mode,'player':player,'changed':len(changed),'bank0_height':rows[0]['new_height'],'install_eligible':report['install_eligible']})
    (WORK/'x_builds_prepared.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (WORK/'x_force_builds.json').write_text(json.dumps([r for r in reports if r['install_eligible']],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
