"""동일 슬롯/명령을 출발점으로 삼되 파형 ID와 음색 동일성을 가정하지 않는다."""
import json,re,struct,sys,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
from src.psx_spu_audio import decode_spu
OUT=Path(__file__).parent
DATA={s:json.loads((OUT/(s+'_inventory.json')).read_text('utf8'))for s in('us','jp','ver_buki_riko','ver_rin_nana')}
BANKS={s:{(r['path'],r['bank']['slot']):r for r in d['banks']}for s,d in DATA.items()}
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def jp_path(path):
    if re.search(r'/PL\d\d_U\.ARC;',path):return path.replace('_U.ARC','.ARC')
    return path.replace('_U','_0')
def tone_wave(row,tone):return next((w for w in row['bank']['waves']if w['wave_id']==tone['wave_id']),None)

def main(extract=True):
    pairs=[];unmatched=[];audition={};mode_changes={}
    for key,us in BANKS['us'].items():
        path,slot=key;pair=BANKS['jp'].get((jp_path(path),slot))
        if not pair:unmatched.append({'us':path,'slot':slot,'attempted_jp':jp_path(path)});continue
        jp=pair;u=us['bank'];j=jp['bank'];us_hash={w['sha256']for w in u['waves']};jp_hash={w['sha256']for w in j['waves']}
        us_pcm={w['pcm_sha256']for w in u['waves']};jp_pcm={w['pcm_sha256']for w in j['waves']}
        umap={(t['program'],t['tone']):t for t in u['tones']if t['active']};jmap={(t['program'],t['tone']):t for t in j['tones']if t['active']}
        td=[]
        for tk in sorted(umap.keys()|jmap.keys()):
            ut=umap.get(tk);jt=jmap.get(tk);uw=tone_wave(us,ut)if ut else None;jw=tone_wave(jp,jt)if jt else None
            if ut and jt and ut['record_hex']==jt['record_hex']and(uw['sha256']if uw else None)==(jw['sha256']if jw else None):continue
            tags=[]
            if not ut:tags.append('jp_only_active_tone')
            if not jt:tags.append('us_only_active_tone')
            if ut and jt:
                if jt['volume']>0 and ut['volume']==0:tags.append('US_tone_volume_zero')
                if jw and uw and jw['sha256']!=uw['sha256']:
                    tags.append('mapped_wave_bytes_different')
                    if jw['pcm_sha256']!=uw['pcm_sha256']:tags.append('mapped_decoded_signal_different')
                    if not uw['pcm_exact_silence']:tags.append('US_replacement_is_nonzero_not_proven_voice_or_SFX')
                    if jw['sha256']not in us_hash:tags.append('JP_wave_absent_from_corresponding_US_bank')
                if uw and uw['pcm_exact_silence']and jw and not jw['pcm_exact_silence']:tags.append('US_wave_exact_silence')
            td.append({'program':tk[0],'tone':tk[1],'tags':tags,'us':ut,'jp':jt,
                       'us_wave':uw,'jp_wave':jw,'actual_event_mapping_verified':False})
        cd=[]
        for i in range(max(u['command_count'],j['command_count'])):
            uc=u['commands'][i]if i<len(u['commands'])else None;jc=j['commands'][i]if i<len(j['commands'])else None
            if uc is None or jc is None or uc['hex']!=jc['hex']:cd.append({'id':i,'us':uc,'jp':jc})
        row={'us':path,'jp':jp['path'],'slot':slot,'us_header_entry':us['header_record'],'jp_header_entry':jp['header_record'],
             'us_body_entry':us['body_record'],'jp_body_entry':jp['body_record'],'headers_equal':us['header_sha256']==jp['header_sha256'],
             'bodies_equal':us['body_sha256']==jp['body_sha256'],'us_commands':u['command_count'],'jp_commands':j['command_count'],
             'us_waves':u['wave_count'],'jp_waves':j['wave_count'],'command_differences':cd,'tone_or_mapped_wave_differences':td,
             'jp_raw_missing_from_us_bank':[w for w in j['waves']if w['sha256']not in us_hash],
             'us_raw_missing_from_jp_bank':[w for w in u['waves']if w['sha256']not in jp_hash],
             'jp_decoded_missing_from_us_bank':[w['wave_id']for w in j['waves']if w['pcm_sha256']not in us_pcm],
             'interpretation':'상응 path/slot에서 차이를 찾았다는 사실이다. 파형 비동일만으로 누락·언어·발화 의미·복구 필요성을 확정하지 않는다.'}
        pairs.append(row)
        # Local ASR helper: all distinct non-player stage-slot2 source signals, not only muted tones.
        if slot==2:
            for source,src,otherhash in [('jp',jp,us_hash),('us',us,jp_hash)]:
                for w in src['bank']['waves']:
                    if w['sha256']in otherhash:continue
                    k=(source,w['sha256']);item=audition.setdefault(k,{'source':source,'sha256':w['sha256'],'bytes':w['bytes'],'pcm_samples':w['pcm_samples'],
                         'pcm_peak':w['pcm_peak'],'occurrences':[],'human_listening_completed':False,'speech_label':None})
                    item['occurrences'].append({'path':src['path'],'slot':slot,'wave_id':w['wave_id'],'body_offset':w['body_offset'],
                                               'body_entry':src['body_record'],'record':src['record'],
                                               'active_tones':[t for t in src['bank']['tones']if t['active']and t['wave_id']==w['wave_id']],
                                               'local_command_ids':[c['id']for c in src['bank']['commands']if c['operation_bits']==128 and c['target_bank']==slot and any(t['wave_id']==w['wave_id']for t in c['local_tones'])]})
    for mode in('ver_buki_riko','ver_rin_nana'):
        changes=[]
        for key,us in BANKS['us'].items():
            cur=BANKS[mode].get(key)
            if not cur:changes.append({'key':key,'missing':True});continue
            if cur['header_sha256']!=us['header_sha256']or cur['body_sha256']!=us['body_sha256']:
                changes.append({'path':key[0],'slot':key[1],'header_changed':cur['header_sha256']!=us['header_sha256'],
                                'body_changed':cur['body_sha256']!=us['body_sha256'],
                                'before_header_sha256':us['header_sha256'],'after_header_sha256':cur['header_sha256'],
                                'before_body_sha256':us['body_sha256'],'after_body_sha256':cur['body_sha256']})
        mode_changes[mode]=changes
    kor=[]
    for key,k in BANKS['jp'].items():
        if not key[0].startswith('/KOR/'):continue
        a=BANKS['jp'].get((key[0].replace('/KOR/','/ARC/'),key[1]))
        kor.append({'path':key[0],'slot':key[1],'arc_pair':bool(a),'audio_header_equal':a and a['header_sha256']==k['header_sha256'],'audio_body_equal':a and a['body_sha256']==k['body_sha256']})
    write(OUT/'comparison.json',{'pairs':pairs,'unmatched_us':unmatched,'current_vs_original_us':mode_changes,'jp_KOR_vs_ARC':kor})
    if not extract:
        print(json.dumps({'comparison_refreshed':True,'banks':len(pairs),'existing_asr_files_unchanged':True}))
        return
    folder=OUT/'asr_candidates';folder.mkdir(exist_ok=True);files={};rows=[]
    try:
        for(source,key),item in audition.items():
            if source not in files:
                f=(ROOT/DATA[source]['path']).open('rb');files[source]=(f,DiscReader(f,(ROOT/DATA[source]['path']).stat().st_size))
            f,d=files[source];o=item['occurrences'][0];r=o['record'];arc=d.read(r['lba'],r['size']);offset=o['body_entry']['offset']+o['body_offset'];raw=arc[offset:offset+item['bytes']]
            import hashlib
            assert hashlib.sha256(raw).hexdigest()==key
            label=Path(o['path']).name.split('.')[0];stem=f'{source}_{label}_wave{o["wave_id"]}_{key[:10]}'
            (folder/(stem+'.spu')).write_bytes(raw)
            pcm=np.array(decode_spu(raw).pcm,dtype='<i2')
            # Preliminary audition at22050 only. Native dispatcher note/pitch validated in a follow-up manifest.
            rate=22050
            with wave.open(str(folder/(stem+'.wav')),'wb')as w:w.setparams((1,2,rate,0,'NONE','not compressed'));w.writeframes(pcm.tobytes())
            item.update(raw_path=(folder/(stem+'.spu')).relative_to(ROOT).as_posix(),wav_path=(folder/(stem+'.wav')).relative_to(ROOT).as_posix(),
                        preview_sample_rate=rate,native_pitch_verified=False,preview_rate_warning='Preliminary22050Hz; do not use as native pitch evidence.')
            rows.append(item)
    finally:
        for f,_ in files.values():f.close()
    write(OUT/'asr_manifest.json',{'scope':'JP/US mapped nonplayer slot2 differing waveform candidates; includes effects and unused waves, no speech label inferred.',
                                 'rows':rows,'count':len(rows),'native_pitch_verified':False})
    print(json.dumps({'paired':len(pairs),'unmatched_us':unmatched,'different_banks':sum(not(r['headers_equal']and r['bodies_equal'])for r in pairs),
      'different_commands':sum(len(r['command_differences'])for r in pairs),'audition_unique_waves':len(rows),'current_changed_banks':{m:len(r)for m,r in mode_changes.items()},
      'kor_different':sum(not(r['audio_header_equal']and r['audio_body_equal'])for r in kor)}))

if __name__=='__main__':main(extract='--comparison-only'not in sys.argv)
