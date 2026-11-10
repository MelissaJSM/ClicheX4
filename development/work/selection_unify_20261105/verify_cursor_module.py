"""공통 커서 모듈을 현재 두 입력에서 메모리 안에서 검사한다."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_common import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.selection_common_cursor import patch,verify_palette

def sha(data):return hashlib.sha256(data).hexdigest()
def refuse(call,expected):
    try:call()
    except ValueError as error:
        assert str(error)==expected
        return expected
    raise AssertionError('Invalid input accepted')

def main():
    result={}
    for mode,path in [('ver_buki_riko','out/ver_buki_riko/hud_reference_details_20261105_v8/shibuki_riko.bin'),
                      ('ver_rin_nana','out/ver_rin_nana/hud_rin_optical_20261105_v9/rin_nana.bin')]:
        assets,_=read_disc(ROOT/path,['ST0E_U1.ARC','COL0E_U1.ARC'])
        source=assets['ST0E_U1.ARC'];palette=assets['COL0E_U1.ARC'];parts=entry(source,10)
        target,report=patch(source);newparts=entry(target,10);palette_report=verify_palette(palette)
        changed=[i for i,(a,b)in enumerate(zip(parts,newparts))if a!=b]
        assert changed==report['changed_part_offsets'] and len(changed)==216
        assert all(newparts[i]==((parts[i]&0xF3)|8)for i in changed)
        assert replace_entry(target,10,parts)==source and len(target)==len(source)
        assert entry(source,0x10102)==entry(target,0x10102)
        twice,again=patch(target);assert twice==target and again['changed_flag_bytes']==0
        errors=[]
        bad=bytearray(parts);off=changed[0];bad[off]=(bad[off]&~12)|12
        errors.append(refuse(lambda:patch(replace_entry(source,10,bytes(bad))),'Unexpected cursor palette binding'))
        # A name/header now references the same records as frame8: must refuse.
        bad=bytearray(parts);bank1=struct.unpack_from('<I',parts,4)[0]
        bad[bank1+2*4:bank1+3*4]=parts[bank1+8*4:bank1+9*4]
        errors.append(refuse(lambda:patch(replace_entry(source,10,bytes(bad))),'Cursor record is shared outside target frames'))
        badpal=bytearray(entry(palette,5));badpal[194]^=1
        errors.append(refuse(lambda:verify_palette(replace_entry(palette,5,bytes(badpal))),
                             'Selection row6 is not the common grayscale ramp'))
        errors.append(refuse(lambda:patch(source[:-1]),'Unexpected selection ARC size'))
        result[mode]={'source_BIN':path,'source_arc_sha256':sha(source),'target_arc_sha256':sha(target),
          'verification':report,'palette_readonly_verification':palette_report,
          'independent_flags_only_byte_comparison':True,'idempotent':True,
          'negative_rejections':errors,'ARC_COL_or_BIN_files_written':False}
    dest=Path(__file__).parent/'cursor_module_checks.json';assert not dest.exists()
    dest.write_text(json.dumps({'passed':True,'modes':result,'emulator_or_saves_touched':False},ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'passed':True,'modes':2,'flag_bytes_per_mode':216,'negative_cases':8,'idempotent':True}))
if __name__=='__main__':main()
