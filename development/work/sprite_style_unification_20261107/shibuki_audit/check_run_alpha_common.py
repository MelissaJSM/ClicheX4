"""alpha 공통층 후보의 원화160층과1024부분조합 exact를 검사한다."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,write,sha
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import repack_parts
from repack_part_records_lossless import repack as repack_global
from probe_run_occluded_tile_union import tiles_of,render,decode_parts

def main():
    src=H/'base_run_alpha_common01/result.json';j=json.loads(src.read_text('utf8'));old=json.loads((H/'base_run_complete_pack05/progress.json').read_text('utf8'));origbytes=sum(x['new']for x in old['compressed_group_sizes']);a=Archive((H/'prepared_dash_base01/PL00_U.ARC').read_bytes());variants=[]
    for mode in('both','minimum'):
        choices=[next(x for x in g['options']if x['common_banks']==[0,6])if mode=='both'else min((x for x in g['options']if x['passed']),key=lambda x:x['bytes'])for g in j['groups']]
        parts={b:{}for b in(0,5,6,7,8)};layers=0;partials=0
        for v in choices:
            tiles=tiles_of(bytes.fromhex(v['raw']))
            for n in v['refs']:
                got={};want={}
                for b in parts:
                    raw=bytes.fromhex(v['parts'][str(b)][str(n)]);parts[b][n]=raw;got[b]=render(tiles,decode_parts(raw.hex()));want[b]=np.array(Image.open(H/f'base_run_complete_targets01/{n:03}_bank{b}_indices.png'));need(np.array_equal(got[b],want[b]),'Target layer differs');layers+=1
                for mask in range(16):
                    for arm in(1,2):
                        # The two arm selectors use the same newly registered
                        # layer for this group; actual generic draw is a later gate.
                        aa=got[0].copy();bb=want[0].copy()
                        for bit,b in((1,5),(2,6),(4,7),(8,8)):
                            if mask&bit:aa[got[b]>0]=got[b][got[b]>0];bb[want[b]>0]=want[b][want[b]>0]
                        need(np.array_equal(aa,bb),'Partial differs');partials+=1
        nc=a.c;slack={};errors={}
        for b,rr in parts.items():
            try:
                try:nc,slack[b]=repack_parts(nc,b,rr)
                except ValueError:nc,slack[b],_=repack_global(nc,b,rr)
            except ValueError as ex:errors[b]=str(ex)
        size=sum(v['bytes']for v in choices);variants.append({'mode':mode,'compressed_selected_bytes':size,'saved_vs_pack05':origbytes-size,'exact_layers':layers,'exact_structural_partial_combinations':partials,'parts_slack':slack,'parts_errors':errors,'chosen_common_banks':[v['common_banks']for v in choices]})
    report={'analysis_only':True,'resource_written':False,'source_sha256':sha(src.read_bytes()),'variants':variants,'native_and_runtime_verified':False};write(H/'base_run_alpha_common01/verification.json',report);print(json.dumps(report))
if __name__=='__main__':main()
