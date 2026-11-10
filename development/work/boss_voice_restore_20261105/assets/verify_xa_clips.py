"""Read the exact boss-intro XA ranges from both provided discs; never writes discs."""
from pathlib import Path
import hashlib,json,sys,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.psx_xa_audio import decode_groups,validate_audio_sector
OUT=Path(__file__).parent
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
    mapping=json.loads((OUT.parent/'calls/xa_mapping.json').read_text('utf8'))
    inventories={k:json.loads((OUT/(k+'_inventory.json')).read_text('utf8'))for k in('us','jp','ver_buki_riko','ver_rin_nana')}
    clips={};outdir=OUT/'xa_clips';outdir.mkdir(exist_ok=True)
    for region,inv in inventories.items():
        table=mapping['jp'if region=='jp'else'us'];seen={}
        with(ROOT/inv['path']).open('rb')as f:
            for boss in table['bosses']:
                for c in boss['clips']:
                    key=c['track']
                    if key in seen:continue
                    r=next(x['record']for x in inv['xa']if x['record']['name']==c['archive']+';1')
                    raw=[];groups=[];rel=[]
                    for i in range(c['start_table'],c['end_table']):
                        sector=i*8+c['channel'];rel.append(sector)
                        f.seek((r['lba']+sector)*2352);s=f.read(2352)
                        validate_audio_sector(s,channel=c['channel']);raw.append(s);groups.append(s[24:2328])
                    packed=b''.join(groups);pcm,_=decode_groups(packed)
                    name=f'{region}_track{key:02x}.wav'
                    if region in('us','jp'):
                        with wave.open(str(outdir/name),'wb')as w:
                            w.setparams((2,2,37800,0,'NONE','not compressed'));w.writeframes(pcm.astype('<i2').tobytes())
                    seen[key]={'track':key,'archive':r,'channel':c['channel'],'start':c['start_table'],'end':c['end_table'],
                      'relative_sectors':rel,'selected_sector_count':len(raw),'selected_raw_sha256':sha(b''.join(raw)),
                      'sound_groups_sha256':sha(packed),'pcm_sha256':sha(pcm.astype('<i2').tobytes()),
                      'samples_per_channel':len(pcm),'seconds':len(pcm)/37800,'peak':int(abs(pcm.astype(np.int32)).max()),
                      'rate':37800,'channels':2,'pcm_nonzero':bool(np.any(pcm)),
                      'wav_path':(outdir/name).relative_to(ROOT).as_posix()if region in('us','jp')else None,
                      'first_group_zero_history':True,'human_listening_completed':False}
        clips[region]=seen
    comparisons=[]
    for boss in mapping['us']['bosses']:
        for track in sorted(set(boss['track_ids'])):
            u,j=clips['us'][track],clips['jp'][track]
            comparisons.append({'boss':boss['boss'],'boss_index':boss['boss_index'],'track':track,
              'eight_boss':boss['boss_index']<8,'same_range':(u['start'],u['end'],u['channel'])==(j['start'],j['end'],j['channel']),
              'raw_equal':u['selected_raw_sha256']==j['selected_raw_sha256'],
              'adpcm_groups_equal':u['sound_groups_sha256']==j['sound_groups_sha256'],'pcm_equal':u['pcm_sha256']==j['pcm_sha256'],
              'us_nonzero':u['pcm_nonzero'],'current_modes_preserve_us':all(clips[m][track]['sound_groups_sha256']==u['sound_groups_sha256']for m in('ver_buki_riko','ver_rin_nana'))})
    write(OUT/'xa_clip_comparison.json',{'inputs':{r:{'path':i['path'],'sha256':i['sha256']}for r,i in inventories.items()},'clips':clips,'comparisons':comparisons,
      'scope':'Actual table-directed selected-channel sectors; source CD headers naturally differ, ADPCM and PCM are compared separately.',
      'human_listening_completed':False,'game_files_written':False})
    print(json.dumps({'eight_boss_distinct_clips':sum(x['eight_boss']for x in comparisons),
      'eight_boss_pcm_equal':sum(x['eight_boss']and x['pcm_equal']for x in comparisons),
      'eight_boss_adpcm_equal':sum(x['eight_boss']and x['adpcm_groups_equal']for x in comparisons),
      'eight_boss_us_nonzero':sum(x['eight_boss']and x['us_nonzero']for x in comparisons),
      'all_current_preserve_us':all(x['current_modes_preserve_us']for x in comparisons)}))
if __name__=='__main__':main()
