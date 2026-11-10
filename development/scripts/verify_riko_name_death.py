"""Audit the two-file revision against the user's accepted illustration build."""
import argparse,json,struct
from pathlib import Path
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.project import digest,write_json
from src.psx_death_orbs import recolor_death_orbs
from src.psx_player import composition_frame
from src.psx_ui_atlas import aliased_composition,local_composition,write_tile
from src.psx_static_effect import compose_static


def verify(previous,build,out):
    old=json.loads((previous/'manifest.json').read_text('utf8'))
    new=json.loads((build/'manifest.json').read_text('utf8'))
    assert old['source_sha256']==new['source_sha256']
    changed=[];resources={};allowed_lbas=set()
    with (previous/old['bin_file']).open('rb') as a,(build/new['bin_file']).open('rb') as b:
        da=DiscReader(a,(previous/old['bin_file']).stat().st_size)
        db=DiscReader(b,(build/new['bin_file']).stat().st_size)
        for r in da.inspect()['files']:
            if r.get('directory') or not r['size']:continue
            if not (r['path'].startswith('/ARC/') or r['path']=='/SLUS_005.61;1'):continue
            x,y=da.read(r['lba'],r['size']),db.read(r['lba'],r['size'])
            if x!=y:
                changed.append(r['path']);resources[r['path']]=(x,y)
                allowed_lbas.update(range(r['lba'],r['lba']+(r['size']+2047)//2048))
        a.seek(0);b.seek(0);lba=0;changed_sectors=[]
        while x:=a.read(2352*256):
            y=b.read(len(x));assert len(y)==len(x)
            if x!=y:
                for off in range(0,len(x),2352):
                    if x[off:off+2352]!=y[off:off+2352]:
                        sector=lba+off//2352;assert sector in allowed_lbas;changed_sectors.append(sector)
            lba+=len(x)//2352
        assert not b.read(1)
    assert set(changed)=={'/ARC/PL01_U.ARC;1','/ARC/ST0E_U1.ARC;1'}
    before,after=resources['/ARC/PL01_U.ARC;1']
    expected,report=recolor_death_orbs(before);assert expected==after
    for kind in (2,9,0x10007,0x10,0x11,0x12,0x15):assert entry(before,kind)==entry(after,kind)
    original=Path('work/ver_buki_riko/zero_extract/20261023T062408235550Z/original.arc').read_bytes()
    assert sha256(original)=='35414320eff2bb0a196b88f70ccd69ecfe9adb25c4ed5c82f24a96efd3c35359'
    recolor_death_orbs(original)
    badparts=bytearray(entry(before,3));part=composition_frame(bytes(badparts),1,105)['parts'][0]
    badparts[part['record_offset']+2]^=1
    badtex=bytearray(entry(before,0x10206));write_tile(badtex,205,bytes([15])*256)
    rejected=[]
    for label,invalid in [('repeat',after),('source_geometry',replace_entry(before,3,bytes(badparts))),
                          ('source_pixels',replace_entry(before,0x10206,bytes(badtex)))]:
        try:recolor_death_orbs(invalid)
        except ValueError:rejected.append(label)
        else:raise AssertionError('Invalid orb input accepted: '+label)
    before,after=resources['/ARC/ST0E_U1.ARC;1']
    g,h=entry(before,0x10102),entry(after,0x10102);p,q=entry(before,10),entry(after,10)
    assert g[:40960]==h[:40960] and g[90112:]==h[90112:]
    untouched=[]
    for n in range(aliased_composition(p,1,0)['bank_frame_count']):
        if n in (4,7):continue
        a=compose_static(g[40960:90112],local_composition(aliased_composition(p,1,n)))[:3]
        b=compose_static(h[40960:90112],local_composition(aliased_composition(q,1,n)))[:3]
        assert a==b;untouched.append(n)
    pngs=list(previous.glob('*.png'))
    assert all(digest(p)==digest(build/p.name) for p in pngs)
    saves=json.loads((out.parent/'saves_before.json').read_text('utf8'))
    save_checks=[{'path':r['path'],'unchanged':digest(Path(r['path']))==r['sha256']} for r in saves]
    result={'previous_bin_sha256':digest(previous/old['bin_file']),'bin_sha256':digest(build/new['bin_file']),
        'changed_files':changed,'changed_raw_sectors_from_previous':changed_sectors,
        'preserved_pngs':len(pngs),'protected_selection_frames':untouched,
        'selection_illustration_and_x_unchanged':True,'death_orbs':report,'negative_checks_rejected':rejected,
        'all_palettes_executable_and_compressed_body_unchanged':True,'save_checks':save_checks}
    write_json(out,result);print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('previous','build','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();verify(a.previous,a.build,a.output)
