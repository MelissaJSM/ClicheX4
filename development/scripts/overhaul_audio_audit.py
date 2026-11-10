"""US/제공 JP/두 모드의 실제 음향 자원을 읽기 전용으로 대조한다."""
import hashlib,json,sys,struct
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.inventory_riko_voice import parse_bank
from src.psx_spu_audio import decode_spu
from src.psx_xa_audio import decode_groups,validate_audio_sector
D=ROOT/'work/overhaul_20261105/audio'
SOURCES={
 'us':('MegaMan X4.bin','3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'),
 'jp':('Rockman X4.bin','a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1'),
 'ver_buki_riko':('out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.bin','8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a'),
 'ver_rin_nana':('out/ver_rin_nana/nana_ultimate_nova_20261104T185708218838Z/rin_nana.bin','5dd089c181cd141955f8e98e3a6b028f24253f2ca4179ed34e194f6a276047f0')}
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def entry(arc,e):return arc[e['offset']:e['offset']+e['size']]
def bank_commands(h,b):
    q=parse_bank(h,b,False);cmd=[]
    for i in range(q['command_count']):
        c=h[8+4*i:12+4*i];program=c[1]&127;first=c[2]>>4;n=((c[3]>>5)&3)+1;tones=[]
        for t in range(first,first+n):
            if program>=q['program_count'] or t>=16:continue
            off=q['vab_offset']+32+128*16+(program*16+t)*32;r=h[off:off+32]
            tones.append(dict(program=program,tone=t,record_hex=r.hex(),wave_id=struct.unpack_from('<H',r,22)[0],volume=r[2],center=r[4],fine=r[5],note=r[6]))
        cmd.append(dict(id=i,hex=c.hex(),bank=c[0]&63,tones=tones))
    q['commands']=cmd;return q
def main():
    D.mkdir(parents=True,exist_ok=True);data={};report={'sources':{},'arc_banks':{},'xa':{}}
    for name,(rel,expected) in SOURCES.items():
        p=ROOT/rel;actual=digest(p);assert actual==expected
        with p.open('rb') as f:
            reader=DiscReader(f,p.stat().st_size);disc=reader.inspect();report['sources'][name]={'path':rel,'sha256':actual,'volume':disc['volume_id']}
            data[name]={};banks=[];streams=[]
            for rec in disc['files']:
                path=rec['path']
                if path.startswith('/ARC/') and path.endswith('.ARC;1'):
                    a=reader.read(rec['lba'],rec['size'])
                    try:es=psx_arc(a)
                    except ValueError:continue
                    for i,e in enumerate(es[:-1]):
                        h=entry(a,e);b=entry(a,es[i+1])
                        try:q=bank_commands(h,b)
                        except (ValueError,struct.error,IndexError):continue
                        row=dict(path=path,header_entry=i,header_sha256=sha(h),body_sha256=sha(b),bank=q)
                        for w in q['waves']:
                            raw=b[w['body_offset']:w['body_offset']+w['bytes']]
                            # A zeroed ADPCM residual is exact mute only after decoding.
                            pcm=decode_spu(raw).pcm
                            w['decoded_peak']=max(map(abs,pcm),default=0)
                        banks.append(row);data[name][(path,q['slot'])]=(h,b,q,rec)
                        if path=='/ARC/PL01_U.ARC;1' and q['slot']==0 and name=='us':
                            d=D/'native_sfx';d.mkdir(exist_ok=True)
                            for w in q['waves']:
                                raw=b[w['body_offset']:w['body_offset']+w['bytes']]
                                sf.write(d/f"wave_{w['wave_id']:02}.wav",np.array(decode_spu(raw).pcm,dtype=np.int16),22050,subtype='PCM_16')
                if path.startswith('/XA/') and any(s in path for s in ('VOICE','BOS')):
                    f.seek(rec['lba']*2352);raw=f.read(((rec['size']+2047)//2048)*2352)
                    row=dict(path=path,lba=rec['lba'],iso_size=rec['size'],raw_sha256=sha(raw),channels=[])
                    for ch in range(8):
                        sectors=[raw[o:o+2352] for o in range(0,len(raw),2352) if raw[o+17]==ch and raw[o+18]&4]
                        for s in sectors:validate_audio_sector(s,channel=ch)
                        pcm,_=decode_groups(b''.join(s[24:2328] for s in sectors));sig=pcm.astype(float)/32768
                        row['channels'].append(dict(channel=ch,sectors=len(sectors),seconds=len(pcm)/37800,peak=int(np.max(abs(pcm.astype(np.int32)))),rms=float(np.sqrt(np.mean(sig*sig))),pcm_sha256=sha(pcm.tobytes())))
                        if name in ('us','jp'):
                            d=D/'xa_audition'/name;d.mkdir(parents=True,exist_ok=True)
                            sf.write(d/(rec['name'].split('.')[0]+f'_ch{ch}.wav'),pcm,37800,subtype='PCM_16')
                    streams.append(row)
            report['arc_banks'][name]=banks;report['xa'][name]=streams
        print(name,len(banks),'banks',len(streams),'streams',flush=True)
    differences=[]
    for (path,slot),(h,b,q,rec) in data['us'].items():
        jp_path=path.replace('_U.ARC','.ARC').replace('_U0.ARC','_00.ARC').replace('_U1.ARC','_01.ARC').replace('D_1U','D_1_')
        pair=data['jp'].get((jp_path,slot))
        if pair:
            hh,bb,qq,_=pair
            if h!=hh or b!=bb:
                differences.append(dict(us=path,jp=jp_path,slot=slot,headers_equal=h==hh,bodies_equal=b==bb,us_header=len(h),jp_header=len(hh),us_body=len(b),jp_body=len(bb),us_commands=q['command_count'],jp_commands=qq['command_count'],us_waves=q['wave_count'],jp_waves=qq['wave_count'],us_silent=[w['wave_id'] for w in q['waves'] if w['decoded_peak']==0],jp_silent=[w['wave_id'] for w in qq['waves'] if w['decoded_peak']==0]))
    report['us_jp_bank_differences']=differences
    (D/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'different_banks':differences},indent=2),flush=True)
if __name__=='__main__':main()
