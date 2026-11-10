"""확정 first-mode candidate04 입력만 주입하는 읽기 전용 32타일 감시 wrapper."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import overhaul_nana_buffer_watch as monitor
BUILD=ROOT/'out/ver_buki_riko/overhaul_20261105_candidate04/shibuki_riko.bin'
BIN_SHA='bcdc219a1fa90ed277eecdf7b28ac196489d3297f49914470bf45e0844db2171'

def main():
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--ram-base',type=lambda x:int(x,0),required=True);p.add_argument('--vram-base',type=lambda x:int(x,0),required=True);p.add_argument('--seconds',type=float,default=30);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();args.cpu_only=False
    # These are in-process input bindings, not edits to the shared helper or BIN.
    monitor.BUILD=BUILD;monitor.BIN_SHA=BIN_SHA
    monitor.main(args)
if __name__=='__main__':main()
