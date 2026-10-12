"""Convert primary HEIF photographs to full-resolution, 8-bit sRGB PNGs.

PNG compression level0 stores image data without Deflate compression.
Quantization to8bit is unavoidable for10/12bit sources. No enhancement,
resizing or lossy image encoding is applied. Source files are never changed.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import struct
import time

from PIL import Image,ImageCms
import pillow_heif

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while block:=f.read(4*1024*1024):h.update(block)
    return h.hexdigest()

def png_header(path):
    with path.open('rb') as f:
        header=f.read(33)
    if header[:8]!=b'\x89PNG\r\n\x1a\n' or header[12:16]!=b'IHDR':raise ValueError('Invalid PNG')
    w,h,bits,mode,compression,filtering,interlace=struct.unpack('>IIBBBBB',header[16:29])
    if bits!=8 or mode!=2:raise ValueError('Expected8bit RGB PNG')
    return w,h

def convert(source_path,destination_path):
    source=Path(source_path);destination=Path(destination_path);start=time.perf_counter()
    if destination.exists():raise FileExistsError('Will not overwrite '+str(destination))
    initial_hash=sha(source)
    heif=pillow_heif.open_heif(source,convert_hdr_to_8bit=True)
    info=dict(heif.info);nclx=info.get('nclx_profile') or {}
    bits=info.get('bit_depth');native_size=heif.size
    # Bit-depth reduction is not HDR tone mapping. Refuse unhandled HDR instead
    # of silently exporting incorrectly interpreted colours to training data.
    if nclx.get('transfer_characteristics') in (16,18):raise ValueError('HDR PQ/HLG requires an explicit colour-managed SDR conversion')
    image=heif.to_pillow()
    if image.mode!='RGB':raise ValueError('Expected RGB photograph, got '+image.mode)
    exif_bytes=image.info.get('exif');icc=info.get('icc_profile')
    standard=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
    color_action='sRGB source; original pixel values retained'
    if icc:
        profile=ImageCms.ImageCmsProfile(io.BytesIO(icc));name=ImageCms.getProfileName(profile).strip()
        if 'srgb' not in name.lower():
            image=ImageCms.profileToProfile(image,profile,standard,outputMode='RGB',renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC)
            icc=standard.tobytes();color_action=f'ICC colour-managed conversion from {name} to sRGB'
    elif (nclx.get('color_primaries'),nclx.get('transfer_characteristics'))==(1,13):
        icc=standard.tobytes()
    else:
        exif=image.getexif();colorspace=exif.get_ifd(34665).get(40961)
        if colorspace!=1:raise ValueError('Unknown RGB colour profile; refusing to assume sRGB')
        icc=standard.tobytes()
    decoded_pixel_hash=hashlib.sha256(image.tobytes()).hexdigest()
    temporary=destination.with_name(destination.name+'.tmp')
    if temporary.exists():raise FileExistsError(temporary)
    options=dict(format='PNG',compress_level=0,optimize=False,icc_profile=icc)
    if exif_bytes:options['exif']=exif_bytes
    if info.get('xmp'):options['xmp']=info['xmp']
    image.save(temporary,**options)
    if png_header(temporary)!=image.size:raise ValueError('PNG dimensions changed')
    with Image.open(temporary) as decoded:
        decoded.load()
        if decoded.mode!='RGB' or hashlib.sha256(decoded.tobytes()).hexdigest()!=decoded_pixel_hash:raise ValueError('PNG pixels do not match converted source')
        if decoded.info.get('icc_profile')!=icc:raise ValueError('PNG colour profile mismatch')
        if exif_bytes and decoded.info.get('exif')!=exif_bytes:raise ValueError('PNG EXIF mismatch')
    if sha(source)!=initial_hash:raise ValueError('Source changed during conversion')
    temporary.rename(destination)
    return dict(source=source.name,output=destination.name,width=image.width,height=image.height,
                decoded_native_dimensions=list(native_size),source_bit_depth=bits,png_bit_depth=8,
                png_mode='RGB',png_compression_level=0,bytes=destination.stat().st_size,
                source_sha256=initial_hash,png_sha256=sha(destination),decoded_rgb_sha256=decoded_pixel_hash,
                color_action=color_action,nclx_profile=nclx,exif_preserved=bool(exif_bytes),
                original_orientation=image.info.get('original_orientation'),pixel_roundtrip_verified=True,
                source_preserved=True,elapsed_s=time.perf_counter()-start)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--destination',required=True);p.add_argument('--report',required=True);p.add_argument('--workers',type=int,default=3);a=p.parse_args()
    source=Path(a.source).resolve();destination=Path(a.destination).resolve();report=Path(a.report)
    if not source.is_dir() or not destination.is_dir():raise FileNotFoundError('Input and output folders must exist')
    files=sorted(x for x in source.iterdir() if x.is_file() and x.suffix.lower() in {'.hif','.heif','.heic'})
    if not files:raise ValueError('No HEIF photographs found')
    outputs=[destination/(x.stem+'.png') for x in files]
    if len({str(x).lower() for x in outputs})!=len(outputs):raise ValueError('Duplicate output names')
    for output in outputs:
        if output.exists() or output.with_name(output.name+'.tmp').exists():raise FileExistsError('Refusing existing output '+str(output))
    report.parent.mkdir(parents=True,exist_ok=True);records=[];failures=[];start=time.perf_counter()
    def save_report():
        record=dict(updated_utc=datetime.now(timezone.utc).isoformat(),source=str(source),destination=str(destination),
                    requested=len(files),completed=len(records),failed=len(failures),settings=dict(mode='RGB',bit_depth=8,compression_level=0,resize=False),
                    images=sorted(records,key=lambda x:x['source']),failures=failures,elapsed_s=time.perf_counter()-start,
                    versions=dict(pillow_heif=pillow_heif.__version__,libheif=pillow_heif.libheif_info()['libheif']))
        tmp=report.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2),encoding='utf8');tmp.replace(report)
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        jobs={pool.submit(convert,str(src),str(dst)):src for src,dst in zip(files,outputs)}
        for job in as_completed(jobs):
            src=jobs[job]
            try:
                result=job.result();records.append(result)
                print(f'{len(records)+len(failures)}/{len(files)} {result["output"]}: {result["width"]}x{result["height"]},8bit RGB,verified',flush=True)
            except Exception as e:failures.append(dict(source=src.name,error=str(e)));print('FAILED '+src.name+': '+str(e),flush=True)
            save_report()
    if failures:raise RuntimeError(f'{len(failures)} conversions failed; see {report}')
    print(f'Completed {len(records)} PNGs; {sum(x["bytes"] for x in records)/1e9:.2f}GB. Every output reopened and pixel-checked.',flush=True)

if __name__=='__main__':main()
