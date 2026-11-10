"""패킹 결과를 다시 읽어 전후 의상·총구·전체 표시조합과 입력 거부를 검증한다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
import pack_native as producer
from scripts.export_x_consistency import DRAW_ORDER
from scripts.discover_inputs import psx_arc

def composed(a,layers,mask,arm):
    out=np.asarray(a.rgba(layers[0])).copy()
    for bit,pb in DRAW_ORDER:
        if mask&bit:
            part=np.asarray(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16))
            visible=part[:,:,3]>0;out[visible]=part[visible]
    return out

def main():
    out=D/'packed_wall_candidate_v1';td=D/'joint_native_targets_v1'
    a=Archive((D.parent/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes())
    b=Archive((out/'PL02_U.ARC').read_bytes());need(sha(a.data)==producer.BEFORE,'Parent')
    need(sha(b.data)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031','Candidate')
    meta=json.loads((td/'manifest.json').read_text('utf8'))
    targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in producer.REFS for pb in producer.PBS}
    producer.validate_targets(targets,meta)
    alpha=images=nonselected=selected=muzzles=0;records=[]
    for n in range(237):
        if n in producer.PLACEHOLDERS:continue
        old={pb:a.layer(n,pb)[0]for pb in producer.PBS}
        new={pb:b.layer(n,pb)[0]for pb in producer.PBS}
        expected={pb:targets.get((n,pb),old[pb])for pb in producer.PBS}
        for pb in producer.PBS:need(np.array_equal(new[pb],expected[pb]),f'Layer {n}/{pb}')
        if n in producer.REFS:
            before=np.array(Image.open(td/f'before_{n:03}.png'));after=np.array(Image.open(td/f'after_{n:03}.png'))
            need(np.array_equal(np.asarray(b.composite(n,15)[0]),np.asarray(a.rgba(before,16))),f'Before CLUT {n}')
            need(np.array_equal(np.asarray(b.composite(n,0)[0]),np.asarray(a.rgba(after,0))),f'After CLUT {n}')
            alpha+=2
        for arm in(1,2):
            for mask in range(16):
                actual=np.asarray(b.composite(n,mask,arm)[0]);want=composed(a,expected,mask,arm)
                need(np.array_equal(actual,want),f'RGBA {n}/{mask}/{arm}');images+=1
                selected+=n in producer.REFS;nonselected+=n not in producer.REFS
                if n in producer.REFS and not n%2:
                    bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'))
                    yy,xx=np.nonzero(bar);gx=int(xx.min());my=float(np.median(yy[xx==gx]));Y,X=np.indices(bar.shape)
                    gate=(X>=gx)&(X<gx+8)&(Y>=my-3)&(Y<=my+5)
                    need(np.array_equal(actual[gate],np.asarray(a.rgba(bar,16))[gate]),f'Original muzzle {n}/{mask}/{arm}');muzzles+=1
        if n in producer.REFS:records.append({'ref':n,'before_rgba_sha256':sha(np.asarray(b.composite(n,15)[0]).tobytes()),'after_rgba_sha256':sha(np.asarray(b.composite(n,0)[0]).tobytes()),'tile_count':b.banks[0]['frames'][n]['tile_count']})
    # Every former alias outside this group remains exact; new paired aliases agree.
    pair_checks=[]
    for n in range(55,67,2):
        f,g=b.banks[0]['frames'][n:n+2];need(f['offset']==g['offset']and f['tile_count']==g['tile_count']==32,'Paired alias')
        pair_checks.append({'refs':[n,n+1],'offset':f['offset'],'tile_count':32})
    layout=lambda data:[{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(data)]
    need(layout(a.data)==layout(b.data),'ARC directory/layout')
    need(digest(D/'packed_wall_diagnostic_v1/PL02_U.ARC')==digest(out/'PL02_U.ARC'),'Independent invocation reproduction')
    rejected=[]
    def reject(name,call):
        try:call()
        except (ValueError,KeyError,TypeError):rejected.append(name)
        else:raise ValueError('Invalid input accepted: '+name)
    bad=bytearray(a.data);bad[-1]^=1
    reject('wrong_parent',lambda:producer.validate_source(bytes(bad)))
    reject('existing_output',lambda:producer.validate_output(out))
    reject('outside_output',lambda:producer.validate_output(ROOT/'unauthorized_candidate'))
    for name,mut in [('manifest_parent',lambda m:m.update(source_arc_sha256='0'*64)),('duplicate_manifest_ref',lambda m:m['frames'].__setitem__(0,m['frames'][1])),('manifest_pixel_hash',lambda m:m['frames'][0].update(base_sha256='0'*64))]:
        m=copy.deepcopy(meta);mut(m);reject(name,lambda m=m:producer.validate_targets(targets,m))
    t=dict(targets);t.pop((55,0));reject('missing_target',lambda:producer.validate_targets(t,meta))
    t=dict(targets);t[55,0]=t[55,0].copy();t[55,0][160,160]^=1;reject('pixel_mutation',lambda:producer.validate_targets(t,meta))
    t=dict(targets);t[55,0]=np.zeros((383,384),np.uint8);reject('wrong_shape',lambda:producer.validate_targets(t,meta))
    t=dict(targets);t[55,0]=t[55,0].astype(np.uint16);reject('wrong_depth',lambda:producer.validate_targets(t,meta))
    t=dict(targets);t[55,0]=t[55,0].copy();t[55,0][0,0]=16;reject('invalid_palette_index',lambda:producer.validate_targets(t,meta))
    t=dict(targets);t[55,0]=t[55,0].copy();t[55,0][0,0]=1;m=copy.deepcopy(meta);m['frames'][0]['base_sha256']=sha(t[55,0].tobytes());reject('outside_packing_window',lambda:producer.validate_targets(t,m))
    write(out/'extended_verification.json',{'passed':True,'parent_sha256':sha(a.data),'candidate_sha256':sha(b.data),'manifest_sha256':digest(td/'manifest.json'),'rgba_combinations_checked':images,'selected_combinations_checked':selected,'unchanged_combinations_checked':nonselected,'before_after_target_rgba_checked':alpha,'original_muzzle_rgba_checked':muzzles,'paired_streams':pair_checks,'frames':records,'directory_layout_unchanged':True,'reproduced_same_arc':True,'negative_cases':rejected,'runtime_verified':False,'scope':'228 유효 참조 × 16 표시마스크 × 팔형2를 실제 다시 합성했다. 얼티밋 정상 표시는 획득전15/획득후0이며 나머지 마스크는 구조 회귀 검사이다. 실제 게임/CPU 실행과 구분한다.'})
    print(json.dumps({'passed':True,'rgba':images,'selected':selected,'muzzles':muzzles,'rejections':len(rejected)}),flush=True)
if __name__=='__main__':main()
