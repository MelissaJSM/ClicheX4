"""Export current player UI sprites and HUD, without unrelated original game sheets."""
from export_assets import *
from src.psx_ui_atlas import local_composition

def main():
    p=argparse.ArgumentParser();p.add_argument('--br',type=Path,required=True);p.add_argument('--rn',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    release=json.loads((ROOT/'release-manifest.json').read_text('utf8'));rows=[]
    for mode,path,xc,zc in [('ver_buki_riko',a.br,'shibuki','riko'),('ver_rin_nana',a.rn,'nana','rin')]:
        if digest(path)!=release['ps1'][mode]['sha256']:raise ValueError('Wrong final BIN')
        raw=disc(path,['PL00_U.ARC','PL01_U.ARC','COL00_0X.ARC','COL00_0Z.ARC','ST0E_U1.ARC','COL0E_U1.ARC','LOAD_U.ARC','MOJIPAT.ARC'])
        def add(char,group,name,im,meta):
            dest=a.out/'characters'/char/'ui'/group/(name+'.png');picture(dest,im);rows.append({'character':char,'file':dest.relative_to(a.out).as_posix(),'sha256':digest(dest),**meta})
        for char,arcname,palname in [(xc,'PL00_U.ARC','COL00_0X.ARC'),(zc,'PL01_U.ARC','COL00_0Z.ARC')]:
            arc=raw[arcname];words=struct.unpack_from('<16H',entry(raw[palname],5),17*32)
            for n in range(69,78):
                cp=local_composition(composition_frame(entry(arc,3),1,n));im,bb=render_static_rgba(entry(arc,0x10206),cp,{0:words})
                add(char,'hud',f'{n:03}',im,{'bank':1,'ref':n,'bounds':bb,'note':'Modified HUD with original meter geometry; CAPCOM rights also apply.'})
        tex=entry(raw['ST0E_U1.ARC'],0x10102);parts=entry(raw['ST0E_U1.ARC'],10);starts=entry(raw['ST0E_U1.ARC'],12);pal=entry(raw['COL0E_U1.ARC'],5)
        for char,bank,row in [(zc,0,0),(xc,2,16)]:
            start=struct.unpack_from('<I',starts,bank*4)[0]
            for n in range(aliased_composition(parts,bank,0)['bank_frame_count']):
                comp=aliased_composition(parts,bank,n);colors={q['clut']:struct.unpack_from('<16H',pal,(row+q['clut'])*32)for q in comp['parts']}
                im,bb=render_static_rgba(tex[start:],comp,colors);add(char,'selection_sprite',f'{n:03}',world(im,bb),{'bank':bank,'ref':n,'origin':[80,80]})
        menu=raw['MOJIPAT.ARC'];tex=entry(raw['LOAD_U.ARC'],0x10008);po=struct.unpack_from('<I',menu,4)[0]
        def saved(spec):
            canvas=Image.new('RGBA',(160,160))
            for n,row in spec:
                cp=aliased_composition(menu,2,n)
                for q in cp['parts']:
                    words=struct.unpack_from('<16H',menu,po+(row+q['clut'])*32)
                    im,bb=render_static_rgba(tex,local_composition({**cp,'parts':[q]}),{0:words});canvas.alpha_composite(im,(80+bb[0],80+bb[1]))
            return canvas
        for arm in [1,2]:
            for mask in range(16):
                specs=[(44,8)]+[(n,10 if bit==4 and arm==2 else 8)for bit,n in[(1,45),(2,46),(4,47),(8,48)]if mask&bit]
                add(xc,'save_sprite',f'fourth_{mask:02}_arm{arm}',saved(specs),{'mask':mask,'arm_type':arm,'origin':[80,80]})
        for char,label,n,row in[(xc,'ultimate_before',52,30),(xc,'ultimate_after',53,31),(zc,'normal',43,8),(zc,'black',43,27)]:add(char,'save_sprite',label,saved([(n,row)]),{'origin':[80,80],'ref':n,'palette_row':row})
    save(a.out/'ui-manifest.json',{'sources':release['ps1'],'images':rows,'runtime_capture':False});print('UI images',len(rows),flush=True)
if __name__=='__main__':main()
