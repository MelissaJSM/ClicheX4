"""ClichéX4 verified XOR patch format. Standard library only; originals are read-only."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, sys, tempfile, zipfile

CHUNK=1024*1024
FORMAT='clichex4-xor-v1'
MODES={'ver_buki_riko':'shibuki_riko','ver_rin_nana':'rin_nana'}
def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def xor(a,b):
    if len(a)!=len(b):raise ValueError('Length mismatch')
    return (int.from_bytes(a,'little') ^ int.from_bytes(b,'little')).to_bytes(len(a),'little')
def create(source,target,output,mode,source_sha,target_sha):
    source,target,output=map(Path,(source,target,output))
    if mode not in MODES:raise ValueError('Unknown mode')
    if source.stat().st_size!=target.stat().st_size:raise ValueError('Image sizes differ')
    if digest(source)!=source_sha or digest(target)!=target_sha:raise ValueError('Build input hash mismatch')
    m={'format':FORMAT,'mode':mode,'size':source.stat().st_size,'source_sha256':source_sha,'target_sha256':target_sha,'output_stem':MODES[mode]}
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('manifest.json',json.dumps(m,indent=2))
        with source.open('rb') as a,target.open('rb') as b,z.open('delta.xor','w') as d:
            while block:=a.read(CHUNK):d.write(xor(block,b.read(len(block))))
    return m
def validate(z):
    if sorted(z.namelist())!=['delta.xor','manifest.json']:raise ValueError('Invalid patch entries')
    if z.getinfo('manifest.json').file_size>8192:raise ValueError('Invalid manifest size')
    m=json.loads(z.read('manifest.json'))
    if m.get('format')!=FORMAT or m.get('mode') not in MODES:raise ValueError('Unsupported patch')
    if m.get('output_stem')!=MODES[m['mode']]:raise ValueError('Unsafe output name')
    if type(m.get('size')) is not int or not 0<m['size']<=800_000_000 or m['size']%2352:raise ValueError('Invalid disc size')
    if z.getinfo('delta.xor').file_size!=m['size']:raise ValueError('Invalid delta length')
    for k in ['source_sha256','target_sha256']:
        if not isinstance(m.get(k),str) or len(m[k])!=64 or any(c not in '0123456789abcdef' for c in m[k]):raise ValueError('Invalid hash')
    return m
def apply(source,patch,output=None):
    """output is a NEW directory. No existing directory or file is overwritten."""
    source,patch=Path(source).resolve(),Path(patch).resolve()
    destination=Path(output).absolute() if output else None
    if destination and (destination.exists() or destination.is_symlink()):raise FileExistsError('Output directory already exists; choose a new folder')
    staging=None
    try:
        with zipfile.ZipFile(patch) as z:
            m=validate(z)
            if source.stat().st_size!=m['size'] or digest(source)!=m['source_sha256']:raise ValueError('지원 원본이 아닙니다. 미국판 SLUS_005.61 원본 SHA-256을 확인하세요.')
            if destination:
                destination.parent.mkdir(parents=True,exist_ok=True)
                staging=Path(tempfile.mkdtemp(prefix='.clichex4-',dir=destination.parent))
            result=hashlib.sha256();original=hashlib.sha256();count=0
            sink=(staging/(m['output_stem']+'.bin')).open('xb') if staging else None
            try:
                with source.open('rb') as f,z.open('delta.xor') as delta:
                    while a:=f.read(CHUNK):
                        b=xor(a,delta.read(len(a)));original.update(a);result.update(b);count+=len(b)
                        if sink:sink.write(b)
                    if delta.read(1):raise ValueError('Trailing delta bytes')
            finally:
                if sink:sink.close()
            if count!=m['size'] or original.hexdigest()!=m['source_sha256'] or result.hexdigest()!=m['target_sha256']:raise ValueError('Patch validation failed; no final output produced')
            if staging:
                stem=m['output_stem']
                (staging/(stem+'.cue')).write_text(f'FILE "{stem}.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n','ascii')
                (staging/'build.json').write_text(json.dumps(m,indent=2)+'\n','utf8')
                # Windows refuses rename to an existing destination. Check again to avoid overwrite.
                if destination.exists():raise FileExistsError(destination)
                staging.rename(destination);staging=None
            return {**m,'verified':True,'output_created':bool(destination)}
    finally:
        # Delete only the temporary folder created by this call, within the chosen parent.
        if staging and staging.resolve().parent==destination.parent.resolve() and staging.name.startswith('.clichex4-'):
            shutil.rmtree(staging)
def gui():
    import tkinter as tk
    from tkinter import filedialog,messagebox,ttk
    import threading
    app=tk.Tk();app.title('ClichéX4 · PS1 패치');app.geometry('620x430');app.resizable(False,False)
    root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).parent
    source=tk.StringVar();folder=tk.StringVar();mode=tk.StringVar(value='ver_buki_riko');status=tk.StringVar(value='원본 미국판 BIN을 선택하세요. 기존 파일은 덮어쓰지 않습니다.')
    frame=ttk.Frame(app,padding=22);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='ClichéX4 · 스텔라이브 팬 모드',font=('Malgun Gothic',17,'bold')).pack(anchor='w',pady=(0,12))
    for label,key in [('텐코 시부키 / 유즈하 리코','ver_buki_riko'),('하나코 나나 / 아오쿠모 린','ver_rin_nana')]:ttk.Radiobutton(frame,text=label,variable=mode,value=key).pack(anchor='w')
    for label,var,select in [('원본 BIN',source,lambda:filedialog.askopenfilename(filetypes=[('PS1 BIN','*.bin')])),('출력 상위 폴더',folder,filedialog.askdirectory)]:
        row=ttk.Frame(frame);row.pack(fill='x',pady=10);ttk.Label(row,text=label,width=14).pack(side='left');ttk.Entry(row,textvariable=var).pack(side='left',fill='x',expand=True);ttk.Button(row,text='선택',command=lambda v=var,s=select:v.set(s())).pack(side='right')
    ttk.Label(frame,textvariable=status,wraplength=565).pack(fill='x',pady=12)
    def start():
        if not source.get() or not folder.get():messagebox.showerror('입력 확인','원본 BIN과 출력 상위 폴더를 선택하세요.');return
        selected=mode.get();src=source.get();dest=Path(folder.get())/MODES[selected];button.config(state='disabled');status.set('원본·차이 패치·출력 해시를 검사하고 있습니다…')
        def worker():
            try:
                apply(src,root/(selected+'.cxp'),dest)
                app.after(0,lambda:status.set('완료: '+str(dest)+'\n에뮬레이터에서는 생성된 CUE를 여세요.'))
            except Exception as e:app.after(0,lambda msg=str(e):messagebox.showerror('패치 중단',msg))
            finally:app.after(0,lambda:button.config(state='normal'))
        threading.Thread(target=worker,daemon=True).start()
    button=ttk.Button(frame,text='검사 후 새 BIN / CUE 만들기',command=start);button.pack(pady=7)
    ttk.Label(frame,text='스텔라이브 관련 콘텐츠의 권리는 스텔라이브 및 각 권리자에게 있으며 요청 시 삭제될 수 있습니다.\n원작 게임의 저작권 및 소유권은 CAPCOM에 있습니다. 비공식 팬 모드입니다.',wraplength=570,font=('Malgun Gothic',9)).pack(pady=12)
    app.mainloop()
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--patch',type=Path);p.add_argument('--output',type=Path);p.add_argument('--report',type=Path);p.add_argument('--verify',action='store_true');a=p.parse_args()
    if not a.source:gui();return
    try:
        if not a.patch or (not a.verify and not a.output):raise ValueError('--patch and --output (or --verify) required')
        result=apply(a.source,a.patch,None if a.verify else a.output)
        if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n','utf8')
        elif sys.stdout:print(json.dumps(result))
    except Exception as e:
        if a.report:a.report.write_text(json.dumps({'verified':False,'error':str(e)},ensure_ascii=False)+'\n','utf8')
        elif sys.stderr:print(str(e),file=sys.stderr)
        raise SystemExit(1)
if __name__=='__main__':main()
