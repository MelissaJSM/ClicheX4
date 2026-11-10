"""Render the exact HTML documentation boards with a locally installed Chromium browser."""
from pathlib import Path
import argparse,subprocess,tempfile,time,os
from PIL import Image
def main():
    p=argparse.ArgumentParser();p.add_argument('--browser',type=Path,required=True);a=p.parse_args()
    folder=Path(__file__).resolve().parents[1]/'assets/showcase'
    for name in ['hero','shibuki','riko','nana','rin']:
        out=folder/(name+'.png');before=out.stat().st_mtime_ns if out.exists()else None
        with tempfile.TemporaryDirectory(prefix='cliche-showcase-')as profile:
            cmd=[str(a.browser),'--headless=new','--disable-gpu','--no-first-run','--hide-scrollbars','--force-device-scale-factor=1','--window-size=1600,1000','--virtual-time-budget=2000','--user-data-dir='+profile,'--screenshot='+str(out),(folder/(name+'.html')).as_uri()]
            subprocess.run(cmd,check=True,timeout=45,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt'else 0)
            limit=time.monotonic()+20
            while (not out.exists()or out.stat().st_mtime_ns==before)and time.monotonic()<limit:time.sleep(.2)
            if not out.exists()or out.stat().st_mtime_ns==before:raise RuntimeError('Browser did not produce '+name)
            if Image.open(out).size!=(1600,1000):raise ValueError('Unexpected viewport')
            print(out.name,flush=True)
if __name__=='__main__':main()
