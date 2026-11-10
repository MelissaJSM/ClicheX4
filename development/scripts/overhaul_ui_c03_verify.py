"""C03 최종 자원을 제작 패커와 독립적으로 읽어 보호 범위를 확인한다."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_player import graphics_bank,decode_stream,bank_offsets,composition_frame

def sha(x):return hashlib.sha256(x).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
def main(project):
    proposal_path=ROOT/f'work/overhaul_20261105/sprites/c03_final_v1/{project}/proposal.json'
    proposal=json.loads(proposal_path.read_text('utf8'));spec=proposal['files']['PL02_U.ARC']
    assert set(proposal['files'])=={'PL02_U.ARC'}
    source=ROOT/proposal['baseline'];assert digest(source)==proposal['baseline_sha256']
    with source.open('rb')as f:
        reader=DiscReader(f,source.stat().st_size);r=spec['record'];before=reader.read(r['lba'],r['size'])
    after=(ROOT/spec['path']).read_bytes();assert sha(before)==spec['before']and sha(after)==spec['after']
    assert len(before)==len(after)==spec['size']
    be,ae=psx_arc(before),psx_arc(after)
    assert [{k:v for k,v in e.items()if k!='sha256'}for e in be]==[{k:v for k,v in e.items()if k!='sha256'}for e in ae]
    other=[]
    for r in be:
        typ=int(r['type'],16)
        if typ in(2,3):continue
        a=r['offset'];b=a+r['size'];assert before[a:b]==after[a:b];other.append(r['type'])
    oldg,newg=entry(before,2),entry(after,2);oldc,newc=entry(before,3),entry(after,3)
    assert bank_offsets(oldg,allow_aliases=True)==bank_offsets(newg,allow_aliases=True)
    assert bank_offsets(oldc)==bank_offsets(newc)
    decoded=[];changed=[];bounds=[];selected=set(proposal['checks']['frames'])
    for bi in range(len(bank_offsets(oldg,allow_aliases=True))):
        a=graphics_bank(oldg,bi,allow_bank_aliases=True);b=graphics_bank(newg,bi,allow_bank_aliases=True)
        assert(a['base'],a['end'],len(a['frames']))==(b['base'],b['end'],len(b['frames']))
        if bi!=0:assert oldg[a['base']:a['end']]==newg[b['base']:b['end']]
        for of,nf in zip(a['frames'],b['frames']):
            raw=decode_stream(newg,nf['offset'],nf['limit'],nf['tile_count']*128)
            old=decode_stream(oldg,of['offset'],of['limit'],of['tile_count']*128)
            assert raw.end<=nf['limit']and raw.serialize()==newg[raw.start:raw.end]
            if raw.data!=old.data:
                assert bi==0 and nf['index']in selected;changed.append([bi,nf['index']])
            if bi==0:assert nf['tile_count']<=32
            decoded.append([bi,nf['index'],nf['tile_count'],sha(raw.data)])
        bounds.append({'bank':bi,'start':a['base'],'end':a['end'],'refs':len(a['frames'])})
    count=0;semantic_changed=[];post_frames=set(proposal['checks']['post_frames'])
    for bi in range(len(bank_offsets(oldc))):
        for n in range(composition_frame(oldc,bi,0)['bank_frame_count']):
            a=composition_frame(oldc,bi,n);b=composition_frame(newc,bi,n)
            def clean(c):return [{k:v for k,v in p.items()if k!='record_offset'}for p in c['parts']]
            if clean(a)!=clean(b):
                assert(bi==0 and n in selected)or(bi==5 and n in post_frames)
                semantic_changed.append([bi,n])
            count+=1
    words=struct.unpack_from('<64H',entry(after,9));post_changed=[];pre_changed=[];rendered=[]
    for n in range(237):
        if n in{105,*range(175,183)}:continue
        full=[]
        for arc in(before,after):
            im=Image.new('RGBA',(384,384))
            for bi in(0,8,5,7,6):
                a,_=render(arc,0,bi,n)
                im.alpha_composite(rgba(a,words if bi==0 else words[32:48]if bi==7 else words[16:32]))
            full.append(im)
        if full[0].tobytes()!=full[1].tobytes():post_changed.append(n)
        a,_=render(before,0,0,n);b,_=render(after,0,0,n)
        if not np.array_equal(a,b):pre_changed.append(n)
        rendered.append(n)
    assert set(post_changed)<=set(proposal['checks']['acquired_preserved_except'])
    shibuki=[]
    if project=='ver_buki_riko':
        for n in(1,2):
            candidate=np.array(Image.open(ROOT/f'work/overhaul_20261105/ui/c04_shibuki_ultimate/frame{n}_indexed.png'))
            expected=rgba(candidate,words[16:32]);actual=Image.new('RGBA',(384,384))
            for bi in(0,8,5,7,6):
                a,_=render(after,0,bi,n);actual.alpha_composite(rgba(a,words if bi==0 else words[32:48]if bi==7 else words[16:32]))
            assert actual.tobytes()==expected.tobytes();shibuki.append(n)
    dest=ROOT/f'work/overhaul_20261105/ui/c03_independent/{project}';dest.mkdir(parents=True,exist_ok=True)
    report={'project':project,'proposal':proposal_path.relative_to(ROOT).as_posix(),'before_sha256':sha(before),'after_sha256':sha(after),
        'baseline_disc_read_verified':True,'ARC_layout_unchanged':True,'non_graphics_entries_byte_identical':other,
        'palettes_timing_name_UI_preserved':True,'graphics_boundaries':bounds,'nonzero_graphics_banks_byte_identical':True,
        'decoded_references':len(decoded),'decode_details':decoded,'changed_decoded_refs':changed,'player_buffer_max_32tiles':True,
        'composition_references_checked':count,'changed_compositions':semantic_changed,'composition_bank_boundaries_unchanged':True,
        'full_RGBA_refs_checked':len(rendered),'full_RGBA_changed_declared_only':post_changed,
        'declared_exceptions_actually_unchanged':sorted(set(proposal['checks']['acquired_preserved_except'])-set(post_changed)),
        'pre_indices_changed':pre_changed,
        'Shibuki_1_2_matches_UI_candidate_full_RGBA':shibuki,'PL00_nova_legs_resource_conflict':False,
        'runtime_verified':False,'limitations':['정적 최종 ARC 재디코딩이다. 실제 BIN 재생 또는 미사용 참조 도달성을 추가로 증명하지 않는다.']}
    (dest/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({k:v for k,v in report.items()if k not in('decode_details','changed_decoded_refs','changed_compositions','pre_indices_changed')},ensure_ascii=False))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('project',choices=['ver_rin_nana','ver_buki_riko']);main(parser.parse_args().project)
