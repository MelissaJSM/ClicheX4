"""Assemble documentation, inspect frozen code, and seal the local release ZIP."""
import hashlib
import json
import marshal
from pathlib import Path
import shutil
import sys
import types
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.steam_distribution import digest,json_bytes
from PyInstaller.archive.readers import CArchiveReader

from scripts.steam_distribution_release import BUILD,STAGE,OUT,RELEASE


def main():
    for name in ('README_KO.txt','CHANGELOG_KO.txt','THIRD_PARTY.txt'):
        shutil.copyfile(ROOT/'docs/distribution'/name,OUT/name)
    python=Path(sys.base_prefix)
    licenses={
        'Python-3.13.txt':python/'LICENSE.txt',
        'TclTk.txt':python/'tcl/tk8.6/license.terms',
        'PyInstaller.txt':ROOT/'work/tools/release_env/Lib/site-packages/pyinstaller-6.22.3.dist-info/licenses/COPYING.txt',
        'Apache-2.0.txt':ROOT/'work/tools/release_env/Lib/site-packages/packaging-26.3.dist-info/licenses/LICENSE.APACHE'}
    (OUT/'licenses').mkdir(exist_ok=True)
    for name,p in licenses.items():shutil.copyfile(p,OUT/'licenses'/name)
    source_files=[STAGE/n for n in ('main.py','release_paths.py','release_config.py')]
    source_files+=list((STAGE/'src').glob('*.py'))+list((STAGE/'scripts').glob('*.py'))+list((STAGE/'runtime_specs').rglob('*.json'))
    assert len(source_files)==35,len(source_files)
    with zipfile.ZipFile(OUT/'source_review.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(source_files):z.writestr(p.relative_to(STAGE).as_posix(),p.read_bytes())
        z.writestr('BUILD.txt',
            '검토용 소스: 별도 폴더에 압축 해제한 뒤 Python 3.13 x64 환경에서 실행합니다.\n'
            'pip install pyinstaller==6.22.3 pyinstaller-hooks-contrib==2026.9\n'
            'pyinstaller --windowed --onedir --name ClicheX4 --add-data "runtime_specs;runtime_specs" '
            + ' '.join('--hidden-import scripts.'+m for m in ['steam_title_position','steam_portrait_routes','steam_dialogue_outfits','steam_ultimate_player','steam_menu_outfits','steam_audio_runtime','steam_effect_colors'])
            + ' main.py\n'
            '배포본 patches.zip을 만들어진 ClicheX4.exe 옆에 놓습니다.\n'
            '차이 패치의 해시가 release_config.py의 값과 일치해야 합니다.\n'
            '원본 게임과 패치 그래픽 제작 자료는 이 검토용 소스에 포함하지 않습니다.\n')
    forbidden=[b'rpio_dev',b'rpio_d~',b'c:\\users\\',b'c:/users/']
    def check_bytes(raw,label):
        low=raw.lower()
        for s in forbidden:
            if s in low or s.decode().encode('utf-16le') in low:raise AssertionError('Private path: '+label)
    for p in OUT.rglob('*'):
        if not p.is_file() or p.name=='SHA256SUMS.txt':continue
        check_bytes(p.read_bytes(),str(p.relative_to(OUT)))
        if p.suffix=='.zip':
            with zipfile.ZipFile(p) as z:
                for info in z.infolist():check_bytes(z.read(info),p.name+'!'+info.filename)
    # Compressed bytecode needs separate inspection; a raw EXE scan is insufficient.
    a=CArchiveReader(str(OUT/'ClicheX4.exe'));pyz=a.open_embedded_archive('PYZ.pyz');count=0
    def codecheck(value,label):
        nonlocal count
        if isinstance(value,types.CodeType):
            count+=1;check_bytes(value.co_filename.encode('utf8'),label)
            for c in value.co_consts:codecheck(c,label)
        elif isinstance(value,str):check_bytes(value.encode('utf8'),label)
        elif isinstance(value,bytes):check_bytes(value,label)
        elif isinstance(value,(tuple,frozenset)):
            for c in value:codecheck(c,label)
    for name in pyz.toc:
        codecheck(pyz.extract(name),name)
    for name,entry in a.toc.items():
        if entry[-1]=='s':codecheck(marshal.loads(a.extract(name)),name)
    assert not any(p.suffix.lower() in ('.arc','.bin','.cue','.webp','.ttf','.otf') for p in OUT.rglob('*') if p.is_file())
    assert not any(p.name.lower() in ('rxc1.exe','savedata.dat','config.ini','text.bin') for p in OUT.rglob('*'))
    sums=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='SHA256SUMS.txt':sums.append(digest(p.read_bytes())+'  '+p.relative_to(OUT).as_posix())
    (OUT/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf8')
    target=OUT.parent/(OUT.name+'.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(OUT.parent).as_posix())
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    report={'release':RELEASE,'archive':target.relative_to(ROOT).as_posix(),
            'bytes':target.stat().st_size,'sha256':digest(target.read_bytes()),
            'file_count':len(sums)+1,'source_files':len(source_files),'code_objects_audited':count,
            'private_paths_found':False,'raw_games_saves_references_fonts_found':False,
            'zip_crc_passed':True,'external_upload_performed':False}
    (BUILD/'release_report.json').write_bytes(json_bytes(report))
    target.with_suffix('.zip.sha256').write_text(report['sha256']+'  '+target.name+'\n',encoding='ascii')
    print(json.dumps(report))


if __name__=='__main__':main()
