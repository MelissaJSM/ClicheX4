"""검증된 동일 길이 ARC만 새 BIN에 기록하는 제한된 복사기."""
import hashlib
from pathlib import Path

from src.psx_sector import validate_checks, replace_payload


def file_hash(path):
    with Path(path).open('rb') as stream:
        if hasattr(hashlib,'file_digest'):
            return hashlib.file_digest(stream,'sha256').hexdigest()
        digest=hashlib.sha256()
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
        return digest.hexdigest()


def write_archive_copy(source, target, record, replacement, expected_source_sha256):
    return write_archive_copies(source, target, [(record, replacement)], expected_source_sha256)


def write_archive_copies(source, target, replacements, expected_source_sha256):
    """Validate disjoint same-length files completely before creating one output."""
    source,target=Path(source).resolve(),Path(target).resolve()
    if source==target or target.exists():
        raise ValueError('Output already exists or aliases an input')
    size=source.stat().st_size
    if file_hash(source)!=expected_source_sha256:
        raise ValueError('Unsupported source BIN hash')
    changed={}; changes=[]; occupied=set()
    if not replacements:
        raise ValueError('No archive replacements')
    for record,replacement in replacements:
        if len(replacement)!=record['size'] or not replacement:
            raise ValueError('Archive size change refused')
        count=(record['size']+2047)//2048
        if size%2352 or record['lba']<0 or (record['lba']+count)*2352>size:
            raise ValueError('Invalid archive sector range')
        region=set(range(record['lba'],record['lba']+count))
        if occupied & region:
            raise ValueError('Overlapping archive sector ranges')
        occupied.update(region)
        original=bytearray(); sectors=[]
        with source.open('rb') as stream:
            stream.seek(record['lba']*2352)
            for _ in range(count):
                raw=stream.read(2352); validate_checks(raw)
                sectors.append(raw); original.extend(raw[24:2072])
        if hashlib.sha256(original[:record['size']]).hexdigest()!=record['sha256']:
            raise ValueError('Archive source hash mismatch')
        for index,raw in enumerate(sectors):
            chunk=replacement[index*2048:(index+1)*2048]
            payload=chunk+raw[24+len(chunk):2072]
            updated=replace_payload(raw,payload)
            if updated!=raw:
                lba=record['lba']+index
                changed[lba]=updated
                differences=[i for i,(a,b) in enumerate(zip(raw,updated)) if a!=b]
                if any(i<24 or 2072>i>=24+len(chunk) for i in differences):
                    raise ValueError('Change outside archive/check bytes')
                changes.append({'lba':lba,'raw_offsets':differences,
                                'data_offsets':[i-24 for i in differences if i<2072],
                                'checksum_changed_bytes':sum(i>=2072 for i in differences)})
    input_hash=hashlib.sha256(); output_hash=hashlib.sha256()
    with source.open('rb') as src,target.open('xb') as dst:
        first_sector=0
        while True:
            original_chunk=src.read(2352*256)
            if not original_chunk:break
            input_hash.update(original_chunk)
            chunk=bytearray(original_chunk)
            for lba,raw in changed.items():
                offset=(lba-first_sector)*2352
                if 0<=offset<len(chunk):chunk[offset:offset+2352]=raw
            dst.write(chunk);output_hash.update(chunk)
            first_sector+=len(chunk)//2352
    if input_hash.hexdigest()!=expected_source_sha256 or file_hash(target)!=output_hash.hexdigest():
        raise ValueError('Source changed or output readback failed')
    return {'sha256':output_hash.hexdigest(),'size':size,'verified_original_sectors':len(occupied),'changed_sectors':changes}
