"""Run each region's actual note2pitch2, keeping provisional ASR files unchanged."""
from pathlib import Path
import hashlib,json,struct,sys,wave
import numpy as np
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN
from unicorn import mips_const as m
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
from src.psx_spu_audio import decode_spu
OUT=Path(__file__).parent
def sha(b):return hashlib.sha256(b).hexdigest()
CONFIG={'us':(0x800e2598,0x142f88,0x166bef,0x166bf4,0x11c9e8,'SLUS_005.61;1'),
        'jp':(0x800e2774,0x143068,0x166ccf,0x166cd4,0x11cadc,'SLPS_009.02;1')}
def pitch(exe,region,tone):
    addr,ptr,index1,index2,table,_=CONFIG[region]
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000)
    load=struct.unpack_from('<I',exe,24)[0]&0x1fffffff;u.mem_write(load,exe[2048:])
    u.mem_write(ptr,struct.pack('<I',0x801a0000));u.mem_write(index1,b'\0');u.mem_write(index2,b'\0');u.mem_write(0x1a0000,tone)
    for reg,value in((m.UC_MIPS_REG_SP,0x801ff000),(m.UC_MIPS_REG_RA,0x80001000),(m.UC_MIPS_REG_A0,tone[6]),(m.UC_MIPS_REG_A1,tone[5])):u.reg_write(reg,value)
    u.emu_start(addr,0x80001000,count=10000)
    assert u.reg_read(m.UC_MIPS_REG_PC)==0x80001000
    return u.reg_read(m.UC_MIPS_REG_V0)&0xffff
def main():
    input=json.loads((OUT/'asr_manifest.json').read_text('utf8'));exes={};proof={}
    for r,cfg in CONFIG.items():
        inv=json.loads((OUT/(r+'_inventory.json')).read_text('utf8'));path=ROOT/inv['path']
        with path.open('rb')as f:
            d=DiscReader(f,path.stat().st_size);rec=next(q for q in inv['system_files']if q['name']==cfg[-1]);exe=d.read(rec['lba'],rec['size'])
        assert exe==(OUT.parent/'calls'/cfg[-1].split(';')[0]).read_bytes()
        offset=cfg[0]-0x80010000+2048;body=exe[offset:offset+252]
        exes[r]=exe;proof[r]={'exe_sha256':sha(exe),'native_function_address':hex(cfg[0]),'native_function_sha256':sha(body),'native_function_bytes':252,
            'sdk_tone_pointer':hex(cfg[1]),'sdk_program_index':hex(cfg[2]),'sdk_tone_index':hex(cfg[3]),'pitch_table_address':hex(cfg[4]),
            'pitch_table_sha256':sha(exe[cfg[4]-0x10000+2048:cfg[4]-0x10000+2048+384])}
    # The two function interiors are byte-identical apart from relocated globals/table/jump.
    offsets=(4,12,28,204,216)
    uc=bytearray(exes['us'][CONFIG['us'][0]-0x80010000+2048:CONFIG['us'][0]-0x80010000+2048+252]);jc=bytearray(exes['jp'][CONFIG['jp'][0]-0x80010000+2048:CONFIG['jp'][0]-0x80010000+2048+252])
    differences=[i for i in range(0,252,4)if uc[i:i+4]!=jc[i:i+4]]
    assert differences==list(offsets),differences
    assert proof['us']['pitch_table_sha256']==proof['jp']['pitch_table_sha256']
    directory=OUT/'native_previews';directory.mkdir(exist_ok=True);rows=[];tone_cases=0
    for old in input['rows']:
        row=dict(old);raw=(ROOT/row['raw_path']).read_bytes();assert sha(raw)==row['sha256'];pcm=np.asarray(decode_spu(raw).pcm,dtype='<i2');variants={}
        for occurrence in row['occurrences']:
            for tone in occurrence['active_tones']:
                t=bytes.fromhex(tone['record_hex']);v=pitch(exes[row['source']],row['source'],t);tone_cases+=1
                rate=v*44100/4096;assert 0<v<=0x3fff
                item=variants.setdefault(v,{'pitch':v,'sample_rate_exact':rate,'wav_rate':round(rate),'native_pitch_verified':True,'tones':[]})
                item['tones'].append({'path':occurrence['path'],'wave_id':occurrence['wave_id'],'program':tone['program'],'tone':tone['tone'],'note':t[6],
                    'fine':t[5],'center':t[4],'volume':t[2],'pan':t[3],'adsr1':tone['adsr1'],'adsr2':tone['adsr2'],'local_command_ids':occurrence['local_command_ids']})
        for p,v in variants.items():
            dest=directory/(Path(row['raw_path']).stem+f'_pitch{p:04x}.wav')
            with wave.open(str(dest),'wb')as w:w.setparams((1,2,v['wav_rate'],0,'NONE','not compressed'));w.writeframes(pcm.tobytes())
            v['wav_path']=dest.relative_to(ROOT).as_posix();v['seconds']=len(pcm)/v['sample_rate_exact']
        row['native_variants']=list(variants.values());row['native_pitch_verified']=bool(variants)
        row['waveform_is_loop_or_oneshot_proof']='Original ADPCM unchanged. Preview decodes until first terminal flag; envelopes/mix/loop repetitions are not synthesized.'
        if len(variants)==1:
            v=next(iter(variants.values()));row['wav_path']=v['wav_path'];row['preview_sample_rate']=v['wav_rate'];row['preview_rate_warning']=None
        elif not variants:row['preview_rate_warning']='No active tone references this wave in compared banks; original22050 preview remains provisional.'
        else:row['preview_rate_warning']='Multiple actual pitch variants; use native_variants, not prior provisional wav_path.'
        rows.append(row)
    report={'rows':rows,'count':len(rows),'source_routine_proof':proof,'routine_different_words':differences,'native_tone_cases':tone_cases,
        'single_native_variant_count':sum(len(r['native_variants'])==1 for r in rows),'multiple_native_variant_count':sum(len(r['native_variants'])>1 for r in rows),
        'no_active_tone_count':sum(not r['native_variants']for r in rows),'human_listening_completed':False,
        'scope':'Actual region SDK note2pitch2 using source dispatcher tone.min_note and fine. WAV excludes SPU ADSR, stereo pan and concurrent sound mixing.'}
    (OUT/'asr_native_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({k:report[k]for k in('count','native_tone_cases','single_native_variant_count','multiple_native_variant_count','no_active_tone_count')}))
if __name__=='__main__':main()
