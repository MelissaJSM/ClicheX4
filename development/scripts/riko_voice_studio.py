"""Riko 로컬 음성 청취·조절 UI. 127.0.0.1에서만 열고 입력 자산을 변경하지 않는다."""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import queue
import secrets
import shutil
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlparse

ROOT=Path(__file__).resolve().parents[1]
VOICE=ROOT/'work/ver_buki_riko/voice_production/v1'
sys.path.insert(0,str(ROOT))
from scripts.preview_riko_voice import LABELS
BASE=VOICE/'packed_f0_v2b'
DEFAULT_BUILD='out/ver_buki_riko/riko_voice_20261026T013031276819Z'
GAME_PYTHON=Path(shutil.which('python') or '')
STATE_PATH=VOICE/'studio_state.local.json'
TOKEN=secrets.token_urlsafe(24)
LOCK=threading.RLock()
JOBS=queue.Queue()
STATE={}


def stamp(): return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
def save_state():
    temp=STATE_PATH.with_suffix('.tmp')
    temp.write_text(json.dumps(STATE,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(STATE_PATH)
def patch_job(job_id,**values):
    with LOCK:
        STATE['jobs'][job_id].update(values);save_state()
def run_checked(command,log):
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:
        tail=log.read_text('utf-8',errors='replace').splitlines()[-2:]
        raise ValueError(' / '.join(tail))


def make_package(selections,name):
    source=json.loads((VOICE/'original/manifest.local.json').read_text('utf-8'))
    body=bytearray((VOICE/'original/source_bank.adpcm').read_bytes())
    output=VOICE/name
    if output.exists():raise ValueError('Output already exists')
    output.mkdir();rows=[]
    for info in source['commands']:
        selected=selections[str(info['sound_id'])]
        folder=(VOICE/selected['folder']).resolve()
        if folder.parent!=VOICE.resolve():raise ValueError('Invalid selected folder')
        manifest=json.loads((folder/'manifest.local.json').read_text('utf-8'))
        row=next(x for x in manifest['commands'] if x['sound_id']==info['sound_id'])
        data=(folder/(info['name']+'.adpcm')).read_bytes()
        if len(data)!=info['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('Selected sample changed')
        start=info['body_offset'];body[start:start+len(data)]=data
        for suffix in ('.adpcm','.wav','_pcm.wav','.vag'):
            p=folder/(info['name']+suffix)
            if p.exists():shutil.copyfile(p,output/p.name)
        rows.append({**row,'selection':selected})
    (output/'voice_bank.adpcm').write_bytes(body)
    (output/'manifest.local.json').write_text(json.dumps({'body_sha256':hashlib.sha256(body).hexdigest(),
        'body_bytes':len(body),'commands':rows,'selections':selections,'human_quality_accepted':False},indent=2),encoding='utf-8')
    return output


def worker():
    engine=None
    while True:
        job_id=JOBS.get()
        try:
            with LOCK:job=dict(STATE['jobs'][job_id])
            if job['kind']=='render':
                if engine is None:
                    patch_job(job_id,status='running',message='로컬 모델을 A6000에 올리는 중… 첫 실행은 조금 더 걸립니다.')
                    from riko_voice_engine import VoiceEngine
                    engine=VoiceEngine()
                    with LOCK:STATE['engine']='ready';save_state()
                patch_job(job_id,status='running',message='참고 음색과 원본 기합으로 생성 중…')
                candidate=VOICE/job_id
                params=job['parameters']
                engine.render(job['voice_id'],candidate,**{k:params[k] for k in ('reference_start','reference_end','semitones','contour_scale','guidance')})
                packed=job_id+'_packed'
                patch_job(job_id,message='게임 길이·압축·끝맺음 검사 중…')
                run_checked([sys.executable,str(ROOT/'scripts/pack_riko_voice.py'),'--candidate',job_id,'--output',packed,
                    '--ids',str(job['voice_id']),'--gain-db',str(params['gain_db'])],VOICE/(job_id+'_pack.log'))
                patch_job(job_id,status='done',message='완료 · 게임용 압축 결과를 들어보세요.',folder=packed)
            elif job['kind']=='build':
                patch_job(job_id,status='running',message='선택한 13개 음성으로 별도 BIN을 만드는 중…')
                package=make_package(job['selections'],job_id+'_package')
                log=VOICE/(job_id+'_build.log')
                run_checked([str(GAME_PYTHON),str(ROOT/'scripts/build_riko_voice.py'),'--packed',str(package)],log)
                result=json.loads(log.read_text('utf-8').splitlines()[-1]);build=Path(result['output'])
                # Pointer changes only after the build verifies all sectors.
                pointer=ROOT/'projects/ver_buki_riko/current_build.json'
                previous=json.loads(pointer.read_text('utf-8'))
                (VOICE/(job_id+'_previous_pointer.json')).write_bytes(pointer.read_bytes())
                updated={**previous,'kind':'riko_gameplay_voice_v2','build':str(build.relative_to(ROOT)).replace('\\','/'),
                    'cue':str((build/'riko_motion.cue').relative_to(ROOT)).replace('\\','/'),'bin_sha256':result['sha256'],
                    'previous_build':previous['build'],'previous_bin_sha256':previous['bin_sha256'],
                    'voice_package':str(package.relative_to(ROOT)).replace('\\','/'),'voice_quality_user_review_pending':True,
                    'voice_runtime_verified':False,'session':None,'session_closed':True,'report':'docs/RIKO_VOICE_PRODUCTION.md'}
                pointer.write_text(json.dumps(updated,ensure_ascii=False,indent=2),encoding='utf-8')
                with LOCK:STATE['build']=str(build.relative_to(ROOT)).replace('\\','/');save_state()
                patch_job(job_id,status='done',message='별도 게임 빌드 완료. 새로 실행해서 확인할 수 있습니다.',build=STATE['build'])
            elif job['kind']=='launch':
                patch_job(job_id,status='running',message='게임 실행 중…')
                run_checked([str(GAME_PYTHON),str(ROOT/'scripts/emulator_session.py'),'launch','--cue',str(ROOT/job['build']/'riko_motion.cue')],
                    VOICE/(job_id+'_launch.log'))
                patch_job(job_id,status='done',message='게임을 실행했습니다. 이전 F3 상태에는 옛 음성이 들어 있을 수 있습니다.')
        except Exception as error:
            patch_job(job_id,status='error',message=str(error))
        finally:JOBS.task_done()


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def json_response(self,value,status=200):
        data=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def file_response(self,path,content_type):
        data=path.read_bytes();start=0;end=len(data)-1;status=200
        requested=self.headers.get('Range')
        if requested:
            import re
            m=re.fullmatch(r'bytes=(\d+)-(\d*)',requested)
            if not m:return self.json_response({'error':'Invalid range'},416)
            start=int(m[1]);end=min(end,int(m[2])) if m[2] else end
            if start>end:return self.json_response({'error':'Invalid range'},416)
            status=206
        self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Accept-Ranges','bytes')
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{len(data)}')
        self.send_header('Content-Length',str(end-start+1));self.end_headers();self.wfile.write(data[start:end+1])
    def allowed_host(self):return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
    def do_GET(self):
        if not self.allowed_host():return self.json_response({'error':'Local host only'},403)
        url=urlparse(self.path)
        try:
            if url.path=='/':return self.file_response(ROOT/'ui/voice_studio/index.html','text/html; charset=utf-8')
            if url.path=='/api/state':
                with LOCK:return self.json_response({**STATE,'token':TOKEN,'labels':LABELS})
            if url.path=='/audio':
                query=parse_qs(url.query);kind=query.get('kind',[''])[0];voice_id=int(query.get('id',['0'])[0])
                if voice_id not in range(13):raise ValueError('Invalid voice')
                stem=f'voice_{voice_id:02d}.wav'
                if kind=='reference':path=ROOT/'character/ver_buki_riko/riko(zero)_voice.wav'
                elif kind=='original':path=VOICE/'original'/stem
                elif kind=='previous':path=VOICE/'packed_v5'/stem
                elif kind=='base':path=BASE/stem
                elif kind=='selected':
                    with LOCK:path=VOICE/STATE['selections'][str(voice_id)]['folder']/stem
                elif kind in ('job','jobref'):
                    with LOCK:job=STATE['jobs'][query['job'][0]]
                    if job['kind']!='render' or job['status']!='done':raise ValueError('Audio not ready')
                    path=VOICE/job['folder']/f'voice_{job["voice_id"]:02d}.wav' if kind=='job' else VOICE/query['job'][0]/'reference_b.wav'
                else:raise ValueError('Unknown audio')
                return self.file_response(path,'audio/wav')
            return self.json_response({'error':'Not found'},404)
        except (ValueError,KeyError,FileNotFoundError) as error:return self.json_response({'error':str(error)},400)
    def do_POST(self):
        origin=self.headers.get('Origin')
        if not self.allowed_host() or self.headers.get('X-Voice-Token')!=TOKEN or origin not in (None,f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
            return self.json_response({'error':'Local UI token required'},403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=4096:raise ValueError('Invalid request length')
            data=json.loads(self.rfile.read(length))
            with LOCK:
                if self.path=='/api/select':
                    job=STATE['jobs'][data['job']]
                    if job['kind']!='render' or job['status']!='done':raise ValueError('Candidate is not ready')
                    STATE['selections'][str(job['voice_id'])]={'folder':job['folder'],'job':data['job'],'parameters':job['parameters'],'user_selected':True}
                    save_state();return self.json_response({'ok':True})
                if self.path=='/api/reset':
                    voice_id=int(data['voice_id'])
                    if voice_id not in range(13):raise ValueError('Invalid voice')
                    STATE['selections'][str(voice_id)]={'folder':BASE.name,'job':None,'user_selected':False}
                    save_state();return self.json_response({'ok':True})
                if any(x['status'] in ('queued','running') for x in STATE['jobs'].values()):
                    raise ValueError('현재 작업을 마친 뒤 다시 눌러주세요.')
                job_id='studio_'+stamp()
                if self.path=='/api/render':
                    voice_id=int(data['voice_id']);params={k:float(data[k]) for k in ('reference_start','reference_end','semitones','contour_scale','gain_db','guidance')}
                    if voice_id not in range(13) or not 0<=params['reference_start']<params['reference_end']<=48.136 or not 3<=params['reference_end']-params['reference_start']<=15:
                        raise ValueError('참고 구간은 3~15초 길이로 골라주세요.')
                    if not -6<=params['semitones']<=4 or not .15<=params['contour_scale']<=1 or not -12<=params['gain_db']<=3 or not .3<=params['guidance']<=1.2:
                        raise ValueError('Unsupported adjustment range')
                    job={'kind':'render','voice_id':voice_id,'parameters':params,'status':'queued','message':'생성 대기 중…'}
                elif self.path=='/api/build':job={'kind':'build','selections':json.loads(json.dumps(STATE['selections'])),'status':'queued','message':'빌드 대기 중…'}
                elif self.path=='/api/launch':job={'kind':'launch','build':STATE['build'],'status':'queued','message':'실행 대기 중…'}
                else:raise ValueError('Unknown action')
                STATE['jobs'][job_id]=job;save_state();JOBS.put(job_id)
            self.json_response({'job':job_id})
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as error:self.json_response({'error':str(error)},400)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8766)
    args=p.parse_args()
    if not (BASE/'manifest.local.json').is_file():raise ValueError('Verified base package is missing')
    global STATE
    if STATE_PATH.exists():STATE=json.loads(STATE_PATH.read_text('utf-8'))
    else:STATE={'engine':'not_loaded','build':DEFAULT_BUILD,'jobs':{},'selections':{str(i):{'folder':BASE.name,'job':None,'user_selected':False} for i in range(13)}}
    for job in STATE['jobs'].values():
        if job['status'] in ('queued','running'):job.update(status='error',message='서버 재시작으로 중단됨. 다시 생성해 주세요.')
    STATE['engine']='not_loaded';save_state()
    if GAME_PYTHON.resolve()==Path(sys.executable).resolve():raise ValueError('Launch with the isolated Python executable; keep the system Python on PATH for game builds')
    threading.Thread(target=worker,daemon=True).start()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Riko Voice Studio: http://127.0.0.1:{args.port}',flush=True)
    server.serve_forever()


if __name__=='__main__':main()
