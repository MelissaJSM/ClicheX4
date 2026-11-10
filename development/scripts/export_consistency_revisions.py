"""Read the built disc back and export only changed X display references."""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc, require
from scripts.export_x_consistency import Archive, page, sha, digest
from scripts.export_sprite_consistency_ui import canvas, sheet
from scripts.verify_shibuki_save_icon import icon, rgba
from scripts.prepare_riko_ui import entry
from scripts.ultimate_costume_swap_ui import ui_canvas

OUT=ROOT/'out/sprite_consistency_20261105'

def export(plan_path):
    plan=json.loads(plan_path.read_text('utf8'))
    char='nana' if plan['project']=='ver_rin_nana' else 'shibuki'
    parent=ROOT/plan['source_bin'];target=ROOT/plan['output']/parent.name
    build=json.loads((target.parent/'manifest.json').read_text('utf8'))
    require(digest(target)==build['modified_bin']['sha256'],'Candidate hash mismatch')
    assets,_=read_disc(target,('PL00_U.ARC','PL02_U.ARC','MOJIPAT.ARC','LOAD_U.ARC'))
    original,_=read_disc(parent,('PL00_U.ARC','PL02_U.ARC'))
    directory=OUT/'revised'/char
    require(not directory.exists(),'New revision output required')
    directory.mkdir(parents=True)
    manifest=json.loads((OUT/char/'manifest.json').read_text('utf8'))
    records={};changes=[];pairs=[];checks=0;unreconstructed=0
    for form in manifest['forms']:
        arc=Archive(assets[form['archive']])
        mask=15 if form['id'] in ('fourth','fourth_arm1','ultimate_before') else 0
        arm=form['arm_type'];idle=arc.composite(0,mask,arm)[0];items=[]
        for rec in (r for r in manifest['frames'] if r['form']==form['id']):
            n=rec['ref'];actual_mask=15 if form['id']=='ultimate_after' and 217<=n<=230 else mask
            try:new=arc.composite(n,actual_mask,arm)[0]
            except (ValueError,IndexError):
                require(rec['status']=='unreconstructed','Unexpected decode failure')
                unreconstructed+=1;continue
            require(rec['status']!='unreconstructed','Reserved reference unexpectedly changed')
            old=Image.open(ROOT/rec['path']).convert('RGBA');checks+=1
            if new.tobytes()==old.tobytes():continue
            dest=directory/form['id']/f'{n:03}.png';dest.parent.mkdir(exist_ok=True);new.save(dest)
            records[rec['id']]=dest.relative_to(ROOT).as_posix()
            changes.append({'id':rec['id'],'pixels':int(np.any(np.array(old)!=np.array(new),axis=2).sum()),'before':sha(old.tobytes()),'after':sha(new.tobytes()),'origin':[160,160]})
            items.extend([(f'{n:03} BEFORE',old),(f'{n:03} AFTER',new)])
        if items:
            p=directory/(form['id']+'_comparison.png');page(items,idle,p,cols=2,scale=3);pairs.append(p.relative_to(ROOT).as_posix())
    # Partial armor combinations are provided as compact sheets, never a
    # misleading whole-sprite PNG that omits selected layers.
    before=Archive(original['PL00_U.ARC']);after=Archive(assets['PL00_U.ARC']);partial=[]
    for n in range(237):
        if n in (105,*range(175,183)):continue
        for arm in (1,2):
            for mask in range(16):
                old=before.composite(n,mask,arm)[0];new=after.composite(n,mask,arm)[0]
                if old.tobytes()==new.tobytes():continue
                partial.append({'ref':n,'mask':mask,'arm':arm,'before':sha(old.tobytes()),'after':sha(new.tobytes())})
    menu=assets['MOJIPAT.ARC'];texture=entry(assets['LOAD_U.ARC'],0x10008)
    saves=[(f'save_fourth_{mask:02}_arm{arm}',icon(menu,texture,mask,arm)) for arm in (1,2) for mask in range(16)]
    saves += [('save_ultimate_pre',ui_canvas(menu,texture,52,30)),('save_ultimate_post',ui_canvas(menu,texture,53,31))]
    save_pairs=[]
    for label,data in saves:
        new=canvas(rgba(data));old=Image.open(OUT/char/'supplementary'/(label+'.png')).convert('RGBA');checks+=1
        if new.tobytes()==old.tobytes():continue
        p=directory/'save'/(label+'.png');p.parent.mkdir(exist_ok=True);new.save(p)
        records[label]=p.relative_to(ROOT).as_posix();save_pairs.extend([(label+' BEFORE',old),(label+' AFTER',new)])
    if save_pairs:
        p=directory/'save_comparison.png';sheet(save_pairs,p);pairs.append(p.relative_to(ROOT).as_posix())
    report={'character':char,'source_bin':target.relative_to(ROOT).as_posix(),'source_sha256':digest(target),
      'frames':records,'changes':changes,'readback_comparisons':checks,'unreconstructed_reserved':unreconstructed,
      'partial_armor_changes':partial,'partial_armor_comparisons':7296,'comparison_sheets':pairs,
      'canvas':[384,384],'origin':[160,160],'runtime_verified':False,'baseline_exports_unchanged':True}
    (directory/'mapping.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'character':char,'changed_gallery_references':len(records),'partial_changes':len(partial),'comparisons':checks}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);a=p.parse_args();export(a.plan)
