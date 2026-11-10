"""원본 기합의 F0 윤곽을 명시적으로 조건화하는 Riko 재제작 후보."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
from riko_voice_environment import configure,load_f0_model,ROOT,VOICE_ROOT


def main(args):
    configure()
    import torch
    import torchaudio
    import numpy as np
    import librosa
    import soundfile as sf
    from scipy.ndimage import median_filter
    output=(VOICE_ROOT/args.name).resolve()
    if output.parent!=VOICE_ROOT.resolve() or output.exists(): raise ValueError('Fresh candidate path required')
    output.mkdir()
    model,semantic_fn,f0_fn,vocoder,style_encoder,mel_fn,mel_args=load_f0_model()
    sr=mel_args['sampling_rate']; device='cuda'
    source_manifest=json.loads((VOICE_ROOT/'original/manifest.local.json').read_text('utf-8'))
    reference_path=ROOT/'character/ver_buki_riko/riko(zero)_voice.wav'
    if hashlib.sha256(reference_path.read_bytes()).hexdigest()!='d0ba1fde6fddb1440fb021dd2bf2c504ee3d0f2039e12d0dece1dd0fef23da46':
        raise ValueError('Reference changed')
    ref,_=librosa.load(reference_path,sr=sr,mono=True)
    reference16=librosa.resample(ref,orig_sr=sr,target_sr=16000)
    with torch.inference_mode():
        full_f0=f0_fn(torch.tensor(reference16).to(device),thred=.03)
    voiced_ref=full_f0[full_f0>1]
    median_ref=float(np.median(voiced_ref))
    reference_summary={'rmvpe_hz_percentiles_10_25_50_75_90':np.percentile(voiced_ref,[10,25,50,75,90]).tolist(),
                       'voiced_fraction':float(np.mean(full_f0>1))}
    print('REFERENCE_F0',json.dumps(reference_summary),flush=True)
    ref=ref[23*sr:34*sr];ref-=ref.mean()
    ref*=min(.15/max(float(np.sqrt(np.mean(ref**2))),1e-8),.94/max(float(np.max(np.abs(ref))),1e-8))
    sf.write(output/'reference_b.wav',ref,sr,subtype='PCM_16')
    tensor_ref=torch.tensor(ref)[None].to(device)
    tensor_ref16=torchaudio.functional.resample(tensor_ref,sr,16000)
    rows=[]
    with torch.inference_mode():
        ref_features=semantic_fn(tensor_ref16)
        ref_mel=mel_fn(tensor_ref)
        ref_pitch=f0_fn(tensor_ref16[0],thred=.03)
        features=torchaudio.compliance.kaldi.fbank(tensor_ref16,num_mel_bins=80,dither=0,sample_frequency=16000)
        style=style_encoder((features-features.mean(dim=0,keepdim=True))[None])
        prompt,*_=model.length_regulator(ref_features,ylens=torch.LongTensor([ref_mel.size(2)]).to(device),
            n_quantizers=3,f0=torch.from_numpy(ref_pitch)[None].to(device))
        for voice_id in map(int,args.ids.split(',')):
            info=next(x for x in source_manifest['commands'] if x['sound_id']==voice_id)
            source,_=librosa.load(VOICE_ROOT/'original'/(info['name']+'.wav'),sr=sr,mono=True)
            source=np.pad(source,(round(.20*sr),round(.25*sr)))
            tensor=torch.tensor(source)[None].to(device)
            tensor16=torchaudio.functional.resample(tensor,sr,16000)
            content=semantic_fn(tensor16);mel=mel_fn(tensor)
            pitch=f0_fn(tensor16[0],thred=.03)
            voiced=pitch>1
            if not voiced.any(): raise ValueError('No reliable F0 for '+info['name'])
            original_mid=float(np.median(pitch[voiced]))
            # Keep voicing boundaries and source contour. Explicit conditions
            # prevent the unconstrained model inventing a new high melody.
            log_relative=np.log(np.maximum(pitch,1)/original_mid)
            smoothed=median_filter(log_relative,size=3,mode='nearest')
            contour=np.clip(smoothed*args.contour_scale,-math.log(2)*4/12,math.log(2)*4/12)
            target_mid=median_ref*2**(args.semitones/12)
            target=np.where(voiced,np.exp(contour)*target_mid,0).astype(np.float32)
            condition,*_=model.length_regulator(content,ylens=torch.LongTensor([mel.size(2)]).to(device),
                n_quantizers=3,f0=torch.from_numpy(target)[None].to(device))
            combined=torch.cat([prompt,condition],dim=1)
            seed=20261026+voice_id;torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
            started=time.monotonic()
            with torch.autocast('cuda',dtype=torch.float16):
                generated_mel=model.cfm.inference(combined,torch.LongTensor([combined.size(1)]).to(device),
                    ref_mel,style,None,args.steps,inference_cfg_rate=args.guidance)
            generated_mel=generated_mel[:,:,ref_mel.size(-1):].float()+math.log(args.vocoder_gain)
            wave=vocoder(generated_mel).squeeze().float().cpu().numpy()
            if not np.isfinite(wave).all(): raise ValueError('Invalid waveform')
            generated16=librosa.resample(wave,orig_sr=sr,target_sr=16000)
            output_f0=f0_fn(torch.tensor(generated16).to(device),thred=.03)
            filename=info['name']+'_refb.wav'
            sf.write(output/filename,wave,sr,subtype='FLOAT')
            np.savez(output/(info['name']+'_pitch.npz'),source=pitch,target=target,generated=output_f0,reference=ref_pitch)
            row={'sound_id':voice_id,'reference':'b','file':filename,'seed':seed,'seconds':time.monotonic()-started,
                'sample_rate':sr,'model_samples':len(wave),'source_padding_seconds':[.20,.25],
                'source_median_f0_hz':original_mid,'target_median_f0_hz':target_mid,
                'generated_median_f0_hz':float(np.median(output_f0[output_f0>1])) if np.any(output_f0>1) else None,
                'peak':float(np.max(np.abs(wave))),'rms':float(np.sqrt(np.mean(wave**2)))}
            rows.append(row);print(json.dumps(row),flush=True)
            (output/'manifest.local.json').write_text(json.dumps({'parameters':vars(args),'reference_summary':reference_summary,
                'records':rows,'human_quality_accepted':False,'model':'Seed-VC explicit F0 44k'},indent=2),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--name',required=True)
    p.add_argument('--ids',default='2,3,4,9,11,12')
    p.add_argument('--steps',type=int,default=50)
    p.add_argument('--guidance',type=float,default=.7)
    p.add_argument('--vocoder-gain',type=float,default=.5)
    p.add_argument('--contour-scale',type=float,default=.7)
    p.add_argument('--semitones',type=float,default=0)
    main(p.parse_args())
