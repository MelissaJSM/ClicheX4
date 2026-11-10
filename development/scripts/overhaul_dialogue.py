"""C-05: 실제 적용 대사의 화자 이름만 즉시 출력. 번역/글꼴/본문/배치 보존."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_common import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_korean_text import LEGACY,glyph_bitmap

BASES={
 'ver_buki_riko':('out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin','8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a','work/ver_buki_riko/korean_v1/dialogue_full_v5/proposal.json'),
 'ver_rin_nana':('out/ver_rin_nana/nana_ultimate_nova_20261104T185708218838Z/rin_nana.bin','5dd089c181cd141955f8e98e3a6b028f24253f2ca4179ed34e194f6a276047f0','out/ver_rin_nana/rin_common_20261029T051459667484Z/common/dialogue/proposal.json')}
SPEAKERS={'텐코 시부키','유즈하 리코','하나코 나나','아오쿠모 린','커넬','제너럴','더블','시그마','아이리스','강지 사장','스파이더','월러스','머쉬룸','드라군','스팅레이','피콕','아울','비스트'}

def patch_resource(raw,metadata):
    text=entry(raw,0x15);font,count,code=struct.unpack_from('<III',text,132)
    if text[128:132]!=b'KOR1' or count!=len(metadata['glyphs']):raise ValueError('Unknown font directory')
    if text[font:font+18*count]!=b''.join(glyph_bitmap(c) for c in metadata['glyphs']):raise ValueError('Font metadata differs')
    inverse={v:k for k,v in LEGACY.items()};inverse.update({256+i:c for i,c in enumerate(metadata['glyphs'])})
    out=bytearray(text);pos=0;previous=None;pages=[];allowed=set()
    for page in metadata['pages']:
        mi,pi=page['message'],page['page']
        if mi!=previous:pos=struct.unpack_from('<H',text,mi*2)[0];previous=mi
        lines=[];words=[];positions=[];line=''
        while True:
            if pos>=code:raise ValueError('Page escaped text payload')
            w=struct.unpack_from('<H',text,pos)[0];positions.append(pos);pos+=2;words.append(w);line+=inverse[w&2047]
            if w&0xe000:lines.append((line,words,positions));line='';words=[];positions=[]
            if w&0xa000:break
        if [x[0] for x in lines]!=page['lines']:raise ValueError('Translation metadata differs')
        if len(lines)<2 or lines[0][0] not in SPEAKERS:continue
        name,head,offsets=lines[0]
        if not head[-1]&0x4000:raise ValueError('Missing header/body boundary')
        changed=[]
        for w,off in zip(head[:-1],offsets[:-1]):
            if w&0x1000:
                struct.pack_into('<H',out,off,w&~0x1000);allowed.add(off+1);changed.append(off)
        # Final header yield/newline, entire body, all glyph IDs, sides and
        # page/end controls remain byte-exact. No font/EXE patch is needed.
        pages.append(dict(message=mi,page=pi,name=name,header_words=len(head),
                          changed_words=changed,body_start=lines[1][2][0],header_end_yield=bool(head[-1]&0x1000)))
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(text,out))):raise ValueError('Changed outside speaker flags')
    updated=replace_entry(raw,0x15,bytes(out))
    return updated,dict(pages_checked=len(metadata['pages']),speakers_checked=len(pages),
        changed_pages=sum(bool(p['changed_words']) for p in pages),changed_bytes=len(allowed),
        glyphs_body_controls_font_and_helper_preserved=True,pages=pages)

def prepare(output,cpu=False):
    output=output.resolve()
    if not output.is_relative_to(ROOT/'work/overhaul_20261105') or output.exists():raise ValueError('Fresh isolated output required')
    output.mkdir(parents=True);result={}
    for project,(source,expected,metadata_path) in BASES.items():
        source=ROOT/source
        if digest(source)!=expected:raise ValueError('Baseline hash differs')
        current,records=read_disc(source,['SLUS_005.61','PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'])
        metadata=json.loads((ROOT/metadata_path).read_text('utf8'))['dialogue']
        dest=output/project;before=dest/'before';after=dest/'after';before.mkdir(parents=True);after.mkdir()
        files={};checks={};cpu_cases=[]
        for name,old in current.items():
            (before/name).write_bytes(old)
            if name.endswith('.ARC'):new,checks[name]=patch_resource(old,metadata[name])
            else:new=old
            (after/name).write_bytes(new)
            if new!=old:files[name]=dict(before=sha256(old),after=sha256(new),size=len(new),path=(after/name).relative_to(ROOT).as_posix(),record=records[name])
        if cpu:
            from scripts.verify_korean_typewriter_cpu import run_emitter
            for name,r in checks.items():
                for p in r['pages']:
                    if not p['changed_words']:continue
                    args=(name,p['message'])
                    old=run_emitter(before,*args,False,page=p['page'])
                    new=run_emitter(after,*args,False,page=p['page'])
                    body_before=run_emitter(before,*args,True,page=p['page'])
                    body_after=run_emitter(after,*args,True,page=p['page'])
                    expected_words=p['header_words']+(not p['header_end_yield'])
                    if old['words_consumed']!=1 or new['words_consumed']!=expected_words or new['native_state']!=2 or new['countdown']!=4:raise ValueError(('Header CPU mismatch',old,new))
                    if body_before!=body_after or body_after['words_consumed']!=1:raise ValueError('Body CPU behavior changed')
                    cpu_cases.append(dict(before=old,after=new,body=body_after))
        report=dict(project=project,issue='C-05',baseline=source.relative_to(ROOT).as_posix(),baseline_sha256=expected,
            files=files,checks=checks,cpu_cases=cpu_cases,cpu_calls=len(cpu_cases)*4,
            native_emitter='0x8002328c',gpu_audio_allocation_mocked=True,runtime_verified=False)
        (dest/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
        result[project]=dict(files=len(files),changed_pages=sum(x['changed_pages'] for x in checks.values()),cpu_calls=len(cpu_cases)*4)
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--cpu',action='store_true');a=p.parse_args();prepare(a.output,a.cpu)
