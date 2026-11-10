from pathlib import Path
D=Path(__file__).parent;P=D.parent/'hyouretsuzan_v1'
s=(P/'inspect_runtime.py').read_text().replace('20261025T103853924418Z','20261025T120648682390Z').replace("'ice_identification'","'rise_alignment'").replace('p[0xb9]&2','p[0xb9]&8').replace('(97,98)','(101,102)').replace('obj[1]==0x21','obj[1]==0x23')
s=s.replace("'animation':obj[0x17]","'x':struct.unpack_from('<i',obj,8)[0]/65536,'y':struct.unpack_from('<i',obj,12)[0]/65536,'animation':obj[0x17]")
(D/'inspect_runtime.py').write_text(s,'utf8')
