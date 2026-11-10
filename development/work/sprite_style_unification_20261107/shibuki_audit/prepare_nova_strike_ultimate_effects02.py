"""시부키 고유 역사효과를 먼저 재현하고 새217 몸 가림만 별도 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,binary_fill_holes
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics,digest
from scripts.c01_audio_build import read_disc
from prepare_nova_strike_ultimate import P,PARENT

def reproduce(oldbody,oldfx,newbody,fill):
    remove=binary_dilation(oldbody>0,iterations=1);fx=oldfx.copy();fx[remove]=0;envelope=binary_fill_holes(oldfx>0);holes=np.zeros_like(remove)
    if fill is not None:holes=remove&envelope&(fx==0)&(newbody==0);fx[holes]=fill
    fx[newbody>0]=0
    return fx,remove,envelope,holes

def main():
    d=H/'nova_strike_ultimate_effects02';need(not d.exists(),'새효과후보');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모 변경');bodyp=H/'nova_strike_ultimate_native01/217_indices.png';body=np.array(Image.open(bodyp));need(body.shape==(384,384)and body.dtype==np.uint8 and body.max()<16,'새몸체 형식')
    pr=ROOT/'work/ultimate_costume_swap_20261105/core/prepared_special_v1/ver_buki_riko/proposal.json';policy=json.loads(pr.read_text('utf8'));histpath=ROOT/policy['baseline'];need(digest(histpath)==policy['baseline_sha256'],'역사BIN 변경');histdata=read_disc(histpath,('PL02_U.ARC',))[0]['PL02_U.ARC'];need(sha(histdata)==policy['source_arc_sha256'],'역사ARC 변경');hist=Archive(histdata)
    currentbody=a.layer(217,0)[0];need(int((currentbody>0).sum())==840,'시부키840옛몸');oldbody=hist.layer(217,5)[0];proof=[];d.mkdir();(d/'historical_PL02.ARC').write_bytes(histdata);Image.fromarray(body).save(d/'body_217_indices.png');Image.fromarray(currentbody).save(d/'historical_body_indices.png')
    for n,fill in((218,None),(220,7)):
        oldfx=hist.layer(n,5)[0];previous,remove,envelope,oldholes=reproduce(oldbody,oldfx,currentbody,fill);need(np.array_equal(previous,a.layer(n,5)[0]),f'{n} 현재역사효과 재현')
        fx,_,_,holes=reproduce(oldbody,oldfx,body,fill);recomputed=fx.copy();protected=(~remove)&(body==0)
        if n==218:
            # 현재 표시되던3점만 보존한다. 역사oldfx를 다시노출시키면
            # 기존샌들에가려진(12,13)색1이떠서새효과점으로추가된다.
            fx=previous.copy();protected&=currentbody==0
            need(int((fx>0).sum())==3 and not((fx>0)&(body>0)).any(),'현재218 실제3픽셀 보존')
        need(np.array_equal(fx[protected],oldfx[protected]),'원몸/새몸밖 효과 보존');need(not((fx>0)&(body>0)).any(),'새몸 효과 가림')
        im=a.rgba(body);im.alpha_composite(a.rgba(fx,16));diag=a.rgba(body);diag.alpha_composite(a.rgba(previous,16))
        Image.fromarray(fx).save(d/f'effect_{n}_indices.png');Image.fromarray(oldfx).save(d/f'source_effect_{n}_indices.png');im.save(d/f'actual_{n}.png')
        for name,z in(('old_body_dilation',remove),('old_effect_envelope',envelope),('new_fill_mask',holes),('protected_mask',protected)):Image.fromarray((z*255).astype(np.uint8)).save(d/f'{name}_{n}.png')
        page([('현재 옛몸/효과',a.composite(n,15)[0]),('기존효과를 새몸에 덮은 진단',diag),('새몸+새 가림효과 후보',im),('효과만',a.rgba(fx,16))],a.composite(0,0)[0],d/f'comparison_{n}.png',cols=2,scale=3 if n==220 else 5)
        proof.append({'ref':n,'historical_source_layer5_sha256':sha(oldfx.tobytes()),'historical_current_reproduction_exact':True,'old_effect_pixels':int((previous>0).sum()),'new_effect_pixels':int((fx>0).sum()),'old_removed_region':int(remove.sum()),'fill_index':fill,'old_fill_cells':int(oldholes.sum()),'new_fill_cells':int(holes.sum()),'changed_cells':int((fx!=previous).sum()),'original_effect_covers_new_body':int(((previous>0)&(body>0)).sum()),'new_effect_covers_body':0,'protected_source_cells':int(protected.sum()),'full_effect_unchanged':bool(np.array_equal(fx,previous)),'new_body_outside_effect_envelope':int(((body>0)&~envelope).sum()),'new_effect_sha256':sha(fx.tobytes()),'historical_reexposure_not_applied':[{'world':[int(x-160),int(y-160)],'historical_index':int(recomputed[y,x]),'current_index':int(fx[y,x]),'old_body_index':int(currentbody[y,x])}for y,x in zip(*np.nonzero(fx!=recomputed))]})
    oldflash=np.zeros_like(body);oldflash[binary_dilation(currentbody>0,iterations=2)]=7;oldflash[currentbody>0]=6;need(np.array_equal(oldflash,a.layer(219,5)[0]),'219 역사 실루엣 exact');flash=np.zeros_like(body);flash[binary_dilation(body>0,iterations=2)]=7;flash[body>0]=6;Image.fromarray(flash).save(d/'effect_219_indices.png')
    page([('현재219 실루엣',a.composite(219,15)[0]),('새몸219 실루엣',a.rgba(flash,16)),('현재217 몸',a.composite(217,15)[0]),('새217 몸',a.rgba(body))],a.composite(0,0)[0],d/'comparison_219.png',cols=2,scale=6)
    files=[P,bodyp,H/'nova_strike_ultimate_native01/registration.json',pr,Path(__file__),H.parent/'zero_audit/shibuki_nova_hover_relations01/report.json',H.parent/'zero_audit/shibuki_nova_hover_relations01/conclusions.json',*d.iterdir()]
    write(d/'manifest.json',{'parent_sha256':PARENT,'historical_BIN':{'path':histpath.relative_to(ROOT).as_posix(),'sha256':policy['baseline_sha256']},'historical_ARC_sha256':sha(histdata),'new_body_sha256':sha(body.tobytes()),'new_body_metrics':metrics(a.rgba(body)),'frames':proof,'flash219':{'rule':'Manhattan2 ring7/body6','historical_body_pixels':840,'new_body_pixels':int((body>0).sum()),'new_flash_pixels':int((flash>0).sum()),'historical_exact':True,'new_flash_sha256':sha(flash.tobytes())},'source_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in sorted(set(files))if p.is_file()},'scope':'강제mask15용새after몸+시부키고유효과.218의3픽셀은exact.220은역사효과/원몸팽창1/구멍메움7을새몸알파에대입한가림등록으로전체FXraw보존은아님.219는새몸Manhattan2파생.','native_packed':False,'runtime_verified':False,'root_art_pending':True});print(json.dumps({'frames':proof,'flash':int((flash>0).sum()),'manifest':sha((d/'manifest.json').read_bytes())}))
if __name__=='__main__':main()
