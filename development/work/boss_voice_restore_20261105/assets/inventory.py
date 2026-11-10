"""제공 JP/US와 현재 두 모드의 모든 ARC sound bank/XA 구조 읽기 전수 목록."""
import hashlib,json,struct,sys,wave
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.inventory_riko_voice import parse_bank
from src.psx_spu_audio import decode_spu

OUT=Path(__file__).parent
SOURCES={'us':('MegaMan X4.bin','3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'),
 'jp':('Rockman X4.bin','a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1')}
for mode,stem,expected in [('ver_buki_riko','shibuki_riko','5a57b31c7a4410d697183a01b2246a28344c847cefb331d27aad56135e7a924d'),
                         ('ver_rin_nana','rin_nana','de818d585fe1a4455d9b07551f3161b24357e3a1a2343d84102628a1fde55679')]:
    pointer=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'))
    assert pointer['sha256']==expected
    SOURCES[mode]=(pointer['build']+'/'+stem+'.bin',expected)

def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
WAVES={};BANK_BYTES={}
def wave_meta(raw):
    key=sha(raw)
    if key not in WAVES:
        decoded=decode_spu(raw);pcm=np.array(decoded.pcm,dtype='<i2')
        if len(pcm):
            energy=pcm.astype(float)**2;peak=int(np.max(abs(pcm.astype(np.int32))))
            nz=np.flatnonzero(pcm)
            rms=float(np.sqrt(energy.mean()))
        else:peak=0;nz=[];rms=0.
        WAVES[key]={'bytes':len(raw),'pcm_sha256':sha(pcm.tobytes()),'pcm_samples':len(pcm),
                    'pcm_peak':peak,'pcm_rms_int16':rms,'pcm_exact_silence':peak==0,
                    'nonzero_first_sample':int(nz[0])if len(nz)else None,'nonzero_last_sample':int(nz[-1])if len(nz)else None,
                    'played_blocks':decoded.played_blocks,'end_flag':decoded.end_flag,
                    'block_flags':dict(Counter(map(str,raw[1::16]))),'last16_hex':raw[-16:].hex()}
    return WAVES[key]

def detail(header,body):
    q=parse_bank(header,body,False);vo=q['vab_offset'];tb=vo+32+128*16
    programs=[];active_programs=[]
    for i in range(128):
        p=header[vo+32+i*16:vo+48+i*16]
        if p[0]:active_programs.append(i)
        programs.append({'id':i,'tones':p[0],'volume':p[1],'priority':p[2],'mode':p[3],'pan':p[4],'record_hex':p.hex()})
    assert len(active_programs)==q['program_count']
    tones=[]
    for dense,logical in enumerate(active_programs):
        for j in range(16):
            pos=tb+(dense*16+j)*32;t=header[pos:pos+32];wid=struct.unpack_from('<H',t,22)[0]
            tones.append({'program':logical,'packed_program':dense,'tone':j,'active':j<programs[logical]['tones'],
              'header_offset':pos,'record_hex':t.hex(),'priority':t[0],'mode':t[1],'volume':t[2],'pan':t[3],
              'center_note':t[4],'fine':t[5],'min_note':t[6],'max_note':t[7],
              'adsr1':struct.unpack_from('<H',t,16)[0],'adsr2':struct.unpack_from('<H',t,18)[0],
              'declared_program':struct.unpack_from('<H',t,20)[0],'wave_id':wid})
    for w in q['waves']:
        raw=body[w['body_offset']:w['body_offset']+w['bytes']];w.update(wave_meta(raw))
        w['active_tones']=[{'program':t['program'],'tone':t['tone'],'volume':t['volume'],'pan':t['pan'],'center_note':t['center_note'],'min_note':t['min_note']}for t in tones if t['active']and t['wave_id']==w['wave_id']]
    commands=[]
    for i in range(q['command_count']):
        c=header[8+i*4:12+i*4];target=c[0]&63;program=c[1]&127;first=c[2]>>4;count=((c[3]>>5)&3)+1
        selected={(program+(first+n)//16,(first+n)%16)for n in range(count)}
        mapped=[t for t in tones if(t['program'],t['tone'])in selected]if target==q['slot']else[]
        commands.append({'id':i,'header_offset':8+i*4,'hex':c.hex(),'operation_bits':c[0]&192,
                         'target_bank':target,'program':program,'first_tone':first,'tone_count':count,
                         'volume_modifier_flag':bool(c[1]&128),'priority_low_nibble':c[2]&15,'channel':c[3]&31,
                         'local_tones':[{'program':t['program'],'tone':t['tone'],'active':t['active'],'wave_id':t['wave_id'],'volume':t['volume']}for t in mapped],
                         'resolution':'local'if target==q['slot']else'cross_bank_requires_loaded_context'})
    q.update(vab_header_hex=header[vo:vo+32].hex(),vab_master_volume=header[vo+24],vab_master_pan=header[vo+25],
             active_programs=active_programs,programs=programs,tones=tones,commands=commands)
    return q

def main():
    previous=json.loads((ROOT/'work/overhaul_20261105/audio/audit.json').read_text('utf8'))
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'sources':{},'scope':'All ARC entries signature scan and all XA streams, no volume-only filter.',
            'process_accessed':False,'game_files_written':False,'human_listening_completed':False}
    for source,(rel,expected)in SOURCES.items():
        path=ROOT/rel;before=digest(path);assert before==expected
        with path.open('rb')as f:
            disc=DiscReader(f,path.stat().st_size);info=disc.inspect();banks=[];archives=[];unpaired=[];streams=[];other_audio=[]
            for rec in info['files']:
                if rec['directory']:continue
                if rec['name'].endswith('.ARC;1'):
                    raw=disc.read(rec['lba'],rec['size'])
                    try:entries=psx_arc(raw)
                    except(ValueError,struct.error)as exc:
                        archives.append({'record':rec,'parsed':False,'reason':str(exc)});continue
                    candidates=[]
                    for idx,e in enumerate(entries):
                        h=raw[e['offset']:e['offset']+e['size']]
                        if len(h)<8:continue
                        packed,length=struct.unpack_from('<II',h);vo=packed&0xffffff;slot=packed>>24
                        if h[vo:vo+4]!=b'pBAV':continue
                        body_candidates=[(j,v)for j,v in enumerate(entries)if int(v['type'],16)>>16==2 and (int(v['type'],16)>>8)&255==slot and v['size']==length]
                        if len(body_candidates)!=1:
                            unpaired.append({'path':rec['path'],'header_entry':idx,'slot':slot,'body_candidates':body_candidates});continue
                        bi,be=body_candidates[0];body=raw[be['offset']:be['offset']+be['size']]
                        try:q=detail(h,body)
                        except(ValueError,struct.error,AssertionError)as exc:
                            unpaired.append({'path':rec['path'],'header_entry':idx,'body_entry':bi,'slot':slot,'error':repr(exc)});continue
                        item={'path':rec['path'],'record':rec,'archive_sha256':sha(raw),'header_entry':idx,'body_entry':bi,
                              'header_record':e,'body_record':be,'header_sha256':sha(h),'body_sha256':sha(body),'bank':q}
                        banks.append(item);candidates.append(idx);BANK_BYTES[(source,rec['path'],slot)]=(h,body)
                    archives.append({'record':rec,'parsed':True,'entry_count':len(entries),'sound_headers':candidates})
                elif rec['name'].endswith('.XA;1'):
                    f.seek(rec['lba']*2352);raw=f.read(((rec['size']+2047)//2048)*2352);assert len(raw)%2352==0
                    sectors=np.frombuffer(raw,dtype=np.uint8).reshape(-1,2352);audio=sectors[(sectors[:,18]&4)!=0]
                    groups=Counter(tuple(map(int,x))for x in audio[:,[16,17,19]])
                    stream={'record':rec,'raw_sha256':sha(raw),'raw_bytes':len(raw),'raw_sector_count':len(sectors),
                            'duplicate_subheaders_all_equal':bool(np.array_equal(sectors[:,16:20],sectors[:,20:24])),'formats':[]}
                    prior=next((r for r in previous['xa'].get(source,[])if r['path']==rec['path']and r['raw_sha256']==stream['raw_sha256']),None)
                    for(file_no,ch,coding),count in sorted(groups.items()):
                        sub=audio[(audio[:,16]==file_no)&(audio[:,17]==ch)&(audio[:,19]==coding)]
                        fmt={'file':file_no,'channel':ch,'coding':coding,'sectors':count,'sample_rate':{0:37800,1:18900}.get((coding>>2)&3),
                             'channels':{0:1,1:2}.get(coding&3),'adpcm_bits':{0:4,1:8}.get((coding>>4)&3),'sound_groups_sha256':sha(sub[:,24:2328].copy().tobytes())}
                        if prior:
                            old=next((r for r in prior['channels']if r['channel']==ch and r['sectors']==count),None)
                            if old:fmt['prior_pcm_measurement_same_exact_raw']=old
                        stream['formats'].append(fmt)
                    streams.append(stream)
                elif any(x in rec['name']for x in('.VAB','.VH','.VB','.VAG')):other_audio.append(rec)
            assert not unpaired,(source,unpaired)
            after=digest(path);assert before==after
            entry={'path':rel,'sha256':before,'size':path.stat().st_size,'volume_id':info['volume_id'],
              'system_files':[r for r in info['files']if r['name'].startswith(('SLUS','SLPS','SLPM','SYSTEM'))],
              'directories':[r['path']for r in info['files']if r['directory']],
              'arc_count':len(archives),'bank_count':len(banks),'archives':archives,'unpaired_sound_signatures':unpaired,
              'banks':banks,'xa':streams,'other_named_audio':other_audio,'input_unchanged_after_read':True}
            report['sources'][source]=entry;write(OUT/(source+'_inventory.json'),entry)
            print(json.dumps({'source':source,'banks':len(banks),'arcs':len(archives),'xa':len(streams),'unpaired':len(unpaired)}),flush=True)
    write(OUT/'inventory.json',report);write(OUT/'unique_wave_metrics.json',WAVES)
    print(json.dumps({'inventory_complete':True,'unique_raw_waves':len(WAVES)}),flush=True)

if __name__=='__main__':main()
