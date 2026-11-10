"""프로젝트 전용 로컬 F0 조건 추론. UI와 배치 제작이 같은 경로를 사용한다."""
import hashlib
import json
import math
from pathlib import Path
import time

from riko_voice_environment import configure, load_f0_model, ROOT, VOICE_ROOT


class VoiceEngine:
    def __init__(self):
        configure()
        import torch
        import librosa
        self.torch = torch
        self.model,self.semantic,self.f0,self.vocoder,self.style,self.mel,self.mel_args=load_f0_model()
        self.sr=self.mel_args['sampling_rate']
        self.original=json.loads((VOICE_ROOT/'original/manifest.local.json').read_text('utf-8'))
        path=ROOT/'character/ver_buki_riko/riko(zero)_voice.wav'
        if hashlib.sha256(path.read_bytes()).hexdigest()!='d0ba1fde6fddb1440fb021dd2bf2c504ee3d0f2039e12d0dece1dd0fef23da46':
            raise ValueError('Reference WAV changed')
        self.reference,_=librosa.load(path,sr=self.sr,mono=True)
        self.references={};self.sources={}

    def render(self, voice_id, output, *, reference_start=41.0, reference_end=47.0, semitones=0.0, contour_scale=.55, guidance=.7, steps=50):
        with self.torch.inference_mode():
            return self._render(voice_id,output,reference_start,reference_end,semitones,contour_scale,guidance,steps)

    def _render(self,voice_id,output,start,end,semitones,contour_scale,guidance,steps):
        import numpy as np
        import librosa
        import soundfile as sf
        import torchaudio
        from scipy.ndimage import median_filter
        torch=self.torch;sr=self.sr;device='cuda'
        if voice_id not in range(13) or not 0<=start<end<=48.136 or not 3<=end-start<=15:
            raise ValueError('Invalid voice or reference interval')
        if not -6<=semitones<=4 or not .15<=contour_scale<=1.0 or not .3<=guidance<=1.2 or steps!=50:
            raise ValueError('Parameter outside supported range')
        output=Path(output).resolve()
        if output.parent!=VOICE_ROOT.resolve() or output.exists(): raise ValueError('Fresh local output required')
        key=(start,end)
        if key not in self.references:
            ref=self.reference[round(start*sr):round(end*sr)].copy();ref-=ref.mean()
            ref*=min(.15/max(float(np.sqrt(np.mean(ref**2))),1e-8),.94/max(float(np.max(np.abs(ref))),1e-8))
            tensor=torch.tensor(ref)[None].to(device);tensor16=torchaudio.functional.resample(tensor,sr,16000)
            semantic=self.semantic(tensor16);mel=self.mel(tensor);pitch=self.f0(tensor16[0],thred=.03)
            voiced=pitch[pitch>1]
            if len(voiced)<50: raise ValueError('Reference has insufficient voiced speech')
            fbank=torchaudio.compliance.kaldi.fbank(tensor16,num_mel_bins=80,dither=0,sample_frequency=16000)
            style=self.style((fbank-fbank.mean(dim=0,keepdim=True))[None])
            prompt,*_=self.model.length_regulator(semantic,ylens=torch.LongTensor([mel.size(2)]).to(device),
                n_quantizers=3,f0=torch.from_numpy(pitch)[None].to(device))
            self.references[key]=(ref,mel,pitch,style,prompt,float(np.median(voiced)))
        ref,ref_mel,ref_pitch,style,prompt,median_ref=self.references[key]
        info=next(x for x in self.original['commands'] if x['sound_id']==voice_id)
        if voice_id not in self.sources:
            source,_=librosa.load(VOICE_ROOT/'original'/(info['name']+'.wav'),sr=sr,mono=True)
            padded=np.pad(source,(round(.20*sr),round(.25*sr)))
            tensor=torch.tensor(padded)[None].to(device);tensor16=torchaudio.functional.resample(tensor,sr,16000)
            self.sources[voice_id]=(self.semantic(tensor16),self.mel(tensor).size(2),self.f0(tensor16[0],thred=.03))
        content,mel_length,pitch=self.sources[voice_id]
        voiced=pitch>1;original_mid=float(np.median(pitch[voiced])) if voiced.any() else None
        target_mid=median_ref*2**(semitones/12)
        log_relative=np.log(np.maximum(pitch,1)/(original_mid or 1))
        contour=np.clip(median_filter(log_relative,size=3,mode='nearest')*contour_scale,-math.log(2)*4/12,math.log(2)*4/12)
        target=np.where(voiced,np.exp(contour)*target_mid,0).astype(np.float32)
        condition,*_=self.model.length_regulator(content,ylens=torch.LongTensor([mel_length]).to(device),
            n_quantizers=3,f0=torch.from_numpy(target)[None].to(device))
        combined=torch.cat([prompt,condition],dim=1)
        seed=20261026+voice_id;torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
        started=time.monotonic()
        with torch.autocast('cuda',dtype=torch.float16):
            mel=self.model.cfm.inference(combined,torch.LongTensor([combined.size(1)]).to(device),ref_mel,style,None,steps,
                inference_cfg_rate=guidance)
        wave=self.vocoder(mel[:,:,ref_mel.size(-1):].float()+math.log(.5)).squeeze().float().cpu().numpy()
        if not np.isfinite(wave).all() or np.any(np.abs(wave)>=.9999): raise ValueError('Invalid/clipped model output')
        generated_pitch=self.f0(torch.tensor(librosa.resample(wave,orig_sr=sr,target_sr=16000)).to(device),thred=.03)
        output.mkdir()
        filename=info['name']+'_refb.wav'
        sf.write(output/filename,wave,sr,subtype='FLOAT');sf.write(output/'reference_b.wav',ref,sr,subtype='PCM_16')
        np.savez(output/(info['name']+'_pitch.npz'),source=pitch,target=target,generated=generated_pitch,reference=ref_pitch)
        row={'sound_id':voice_id,'reference':'b','file':filename,'seed':seed,'seconds':time.monotonic()-started,
             'sample_rate':sr,'model_samples':len(wave),'source_padding_seconds':[.20,.25],
             'source_median_f0_hz':original_mid,'reference_median_f0_hz':median_ref,'target_median_f0_hz':target_mid,
             'generated_median_f0_hz':float(np.median(generated_pitch[generated_pitch>1])) if np.any(generated_pitch>1) else None,
             'peak':float(np.max(np.abs(wave))),'rms':float(np.sqrt(np.mean(wave**2)))}
        manifest={'parameters':{'reference_start':start,'reference_end':end,'semitones':semitones,'contour_scale':contour_scale,
            'steps':steps,'guidance':guidance,'vocoder_gain':.5},'records':[row],'human_quality_accepted':False,
            'model':'Seed-VC explicit F0 44k','reference_summary':{'median_f0_hz':median_ref}}
        (output/'manifest.local.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        return manifest
