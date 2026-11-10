"""네 경계 셀의 원화 alpha/실제 팔레트 투표 출처를 별도 기록한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,helper,need

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',default='v1');args=ap.parse_args()
    need(args.version in('v1','v2'),'버전');out=D/f'ultimate_boundary_audit_{args.version}';out.mkdir(exist_ok=False)
    a=Archive((N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC').read_bytes())
    pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
    regs={}
    for name in ['ultimate_air_registered_v1','ultimate_charge_registered_v3','ultimate_recovery_registered_v1']:
        j=json.loads((D/name/'registration.json').read_text('utf8'))
        for q in j['frames']:regs[q['ref'],q['form']]=(j,q)
    frames=json.loads((D/'ultimate_costume_pair_probe_v2/registration.json').read_text('utf8'))['frames']
    if args.version=='v2':
        extra=json.loads((D/'ultimate_costume_pair_probe_v3/registration.json').read_text('utf8'))['frames']
        for q in extra:
            f=next(f for f in frames if f['ref']==q['ref'])
            for row in q['outside_new_before_alpha']:
                if row not in f['outside_new_before_alpha']:f['outside_new_before_alpha'].append(row)
    records=[];rows=[]
    for f in frames:
        if not f['outside_new_before_alpha']:continue
        n=f['ref'];meta,q=regs[n,'before'];art=ROOT/meta['source_art_path']
        need(digest(art)==meta['source_art_sha256'],'출처 해시')
        cell=Image.open(art).convert('RGBA').crop(tuple(q['crop']));ar=np.array(cell);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255
        labs=np.empty(alpha.shape,np.uint8)
        for y in range(len(labs)):labs[y]=1+((rgb[y,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
        weights=np.stack([np.array(Image.fromarray(np.where(labs==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
        coverage=np.array(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX))
        old=np.array(Image.open(D/f'ultimate_weapon_probe_v1/before_{n:03}_indices.png'));candidate=old.copy()
        for x,y,afterv in f['outside_new_before_alpha']:
            dx,dy=q['whole_translation'];sx,sy=x-dx+48,y-dy+48
            cov=float(coverage[sy,sx]);scores=weights[:,sy,sx];winner=int(scores.argmax()+1)
            need(.4<=cov<.5,'경계 등록 범위');need(old[y+160,x+160]==0,'기존 투명')
            candidate[y+160,x+160]=winner
            records.append({'ref':n,'world':[x,y],'source_native_cell':[sx,sy],'source_art':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_crop':q['crop'],'whole_translation':q['whole_translation'],
                'source_alpha_coverage':cov,'source_palette_votes':[float(v)for v in scores],'source_palette_winner':winner,'after_donor_value':afterv,'manual_paint':False})
        Image.fromarray(candidate).save(out/f'before_{n:03}_source_boundary.png')
        rows.append((f'own source edge {n}',[('fixed source',a.rgba(old,16)),('same source boundary vote',a.rgba(candidate,16))]))
    helper.grid(rows,out/'comparison.png',6)
    write(out/'report.json',{'source_cells':records,'scope':'반투명 원화 경계를 기본50%기준에서 제외한 셀의 실제색 투표를 기록한 후보. 다른 원화색/코드 단색채움 없음. 최종 공통층 수용이나 패킹은 아직 아님.','newly_authored_image':False,'native_packed':False})
    print(json.dumps(records))

if __name__=='__main__':main()
