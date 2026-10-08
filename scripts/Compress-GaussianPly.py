"""Vectorized PlayCanvas compressed PLY packing with measured round-trip error.

Format reference: playcanvas/splat-transform (MIT), revision
b6424a5b3b929695fbaafe738a995adb1240d675, compressed-chunk.ts/read-ply.ts.
Full float32 source exports remain the archive; this is a quantized viewer copy.
"""
from pathlib import Path
import math
import numpy as np

CHUNK_PROPERTIES = ['min_x','min_y','min_z','max_x','max_y','max_z',
    'min_scale_x','min_scale_y','min_scale_z','max_scale_x','max_scale_y','max_scale_z',
    'min_r','min_g','min_b','max_r','max_g','max_b']
VERTEX_PROPERTIES = ['packed_position','packed_rotation','packed_scale','packed_color']
SH_C0 = .28209479177387814


def read_standard(path):
    with Path(path).open('rb') as stream:
        header=[]
        while True:
            line=stream.readline().decode('ascii').strip();header.append(line)
            assert len(header)<100
            if line=='end_header':break
        assert header[1]=='format binary_little_endian 1.0'
        assert len([s for s in header if s.startswith('property float ')])==17
        count=int(next(s.split()[-1] for s in header if s.startswith('element vertex ')))
        rows=np.frombuffer(stream.read(),dtype='<f4').reshape(-1,17).copy()
    assert len(rows)==count and np.isfinite(rows).all()
    return rows


def morton_order(xyz):
    span=np.maximum(np.ptp(xyz,axis=0),1e-8)
    grid=np.clip((xyz-xyz.min(0))/span*1023,0,1023).astype(np.uint32)
    code=np.zeros(len(xyz),np.uint32)
    for bit in range(10):
        for axis in range(3):code|=((grid[:,axis]>>bit)&1)<<(3*bit+axis)
    return np.argsort(code,kind='stable')


def quantize(value,bits):
    return np.clip(np.floor(value*((1<<bits)-1)+.5),0,(1<<bits)-1).astype(np.uint32)


def pack_xyz(value):
    return (quantize(value[...,0],11)<<21)|(quantize(value[...,1],10)<<11)|quantize(value[...,2],11)


def normalize(value,low,high):
    span=high-low
    return np.where(span>1e-8,(value-low)/np.maximum(span,1e-8),0)


def read_compressed(path):
    with Path(path).open('rb') as stream:
        header=[]
        while True:
            line=stream.readline().decode('ascii').strip();header.append(line)
            assert len(header)<100
            if line=='end_header':break
        count=int(next(s.split()[-1] for s in header if s.startswith('element vertex ')))
        chunks=int(next(s.split()[-1] for s in header if s.startswith('element chunk ')))
        bounds=np.frombuffer(stream.read(chunks*18*4),'<f4').reshape(chunks,18)
        packed=np.frombuffer(stream.read(),'<u4').reshape(count,4)
    assert len(bounds)==math.ceil(count/256)
    b=bounds[np.arange(count)//256]
    def xyz(word,lo,hi):
        t=np.column_stack(((word>>21)/2047.,((word>>11)&1023)/1023.,(word&2047)/2047.))
        return b[:,lo:lo+3]+t*(b[:,hi:hi+3]-b[:,lo:lo+3])
    means=xyz(packed[:,0],0,3);log_scale=xyz(packed[:,2],6,9)
    rgb_bits=packed[:,3]
    t=np.column_stack((rgb_bits>>24,(rgb_bits>>16)&255,(rgb_bits>>8)&255))/255.
    colors=b[:,12:15]+t*(b[:,15:18]-b[:,12:15])
    alpha=(rgb_bits&255)/255.
    rotation=packed[:,1];largest=rotation>>30
    rest=(np.column_stack(((rotation>>20)&1023,(rotation>>10)&1023,rotation&1023))/1023.-.5)*math.sqrt(2)
    keep=np.arange(4)[None,:]!=largest[:,None]
    q=np.empty((count,4));q[keep]=rest.ravel()
    q[np.arange(count),largest]=np.sqrt(np.maximum(0,1-np.sum(rest**2,axis=1)))
    return dict(means=means.astype(np.float32),scales=np.exp(log_scale).astype(np.float32),
        colors=colors.astype(np.float32),opacity=alpha.astype(np.float32),quats=q.astype(np.float32))


def compress(source,target):
    rows=read_standard(source);order=morton_order(rows[:,:3]);rows=rows[order]
    count=len(rows);chunks=math.ceil(count/256)
    padded=np.concatenate((rows,np.repeat(rows[-1:],chunks*256-count,axis=0)))
    block=padded.reshape(chunks,256,17)
    rgb=block[:,:,6:9]*SH_C0+.5;scale=np.clip(block[:,:,10:13],-20,20)
    bounds=np.concatenate((block[:,:,:3].min(1),block[:,:,:3].max(1),
        scale.min(1),scale.max(1),rgb.min(1),rgb.max(1)),axis=1).astype('<f4')
    pos=pack_xyz(normalize(block[:,:,:3],bounds[:,None,:3],bounds[:,None,3:6])).ravel()[:count]
    scales=pack_xyz(normalize(scale,bounds[:,None,6:9],bounds[:,None,9:12])).ravel()[:count]
    crgb=quantize(normalize(rgb,bounds[:,None,12:15],bounds[:,None,15:18]),8).reshape(-1,3)[:count]
    alpha=1/(1+np.exp(-rows[:,9]))
    color=(crgb[:,0]<<24)|(crgb[:,1]<<16)|(crgb[:,2]<<8)|quantize(alpha,8)
    q=rows[:,13:17]/np.linalg.norm(rows[:,13:17],axis=1,keepdims=True)
    largest=np.argmax(np.abs(q),axis=1).astype(np.uint32)
    q*=np.where(q[np.arange(count),largest]>=0,1,-1)[:,None]
    keep=np.arange(4)[None,:]!=largest[:,None]
    rest=quantize(q[keep].reshape(count,3)/math.sqrt(2)+.5,10)
    rotation=(largest<<30)|(rest[:,0]<<20)|(rest[:,1]<<10)|rest[:,2]
    packed=np.column_stack((pos,rotation,scales,color)).astype('<u4')
    header=['ply','format binary_little_endian 1.0',
        'comment TF4DGS quantized viewer copy; full float32 archive retained',f'element chunk {chunks}',
        *[f'property float {p}' for p in CHUNK_PROPERTIES],f'element vertex {count}',
        *[f'property uint {p}' for p in VERTEX_PROPERTIES],'end_header']
    with Path(target).open('xb') as stream:
        stream.write(('\n'.join(header)+'\n').encode('ascii'));bounds.tofile(stream);packed.tofile(stream)
    decoded=read_compressed(target)
    assert all(np.isfinite(v).all() for v in decoded.values())
    xyz_error=np.linalg.norm(decoded['means']-rows[:,:3],axis=1)
    color_error=np.abs(decoded['colors']-(rows[:,6:9]*SH_C0+.5))
    result=dict(gaussians=count,maximum_position_error_mm=float(xyz_error.max()*1000),
        mean_position_error_mm=float(xyz_error.mean()*1000),maximum_rgb_channel_error=float(color_error.max()),
        maximum_opacity_error=float(np.max(np.abs(decoded['opacity']-alpha))),
        maximum_scale_relative_error=float(np.max(np.abs(decoded['scales']/np.exp(rows[:,10:13])-1))),
        maximum_rotation_error_degrees=float(np.max(2*np.arccos(np.clip(np.abs(np.sum(q*decoded['quats'],axis=1)),0,1)))*180/np.pi),
        bytes=Path(target).stat().st_size,source_bytes=Path(source).stat().st_size,
        gaussian_count_preserved=True,quantized=True)
    assert result['maximum_position_error_mm']<.5
    assert result['maximum_rgb_channel_error']<.0021 and result['maximum_opacity_error']<.0021
    return result
