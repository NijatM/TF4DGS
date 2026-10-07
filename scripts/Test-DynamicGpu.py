"""Exercise the isolated gsplat Windows CUDA wheel with actual gradients."""
import argparse
import json
from pathlib import Path
import time

import torch
import gsplat
from gsplat import rasterization


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError('GPU validation output already exists')
    assert torch.cuda.is_available(), 'CUDA runtime unavailable'
    device='cuda'
    means=torch.tensor([[.05,0.,2.]],device=device,requires_grad=True)
    colors=torch.tensor([[.2,.5,.8]],device=device,requires_grad=True)
    quats=torch.tensor([[1.,0.,0.,0.]],device=device)
    scales=torch.full((1,3),.1,device=device)
    opacity=torch.tensor([.8],device=device)
    views=torch.eye(4,device=device).unsqueeze(0)
    intrinsics=torch.tensor([[[60.,0.,32.],[0.,60.,32.],[0.,0.,1.]]],device=device)
    start=time.perf_counter()
    rgb,alpha,meta=rasterization(means,quats,scales,opacity,colors,views,intrinsics,64,64,packed=False)
    weights=torch.arange(64,device=device).reshape(1,1,64,1)/64
    (rgb*weights).sum().backward()
    torch.cuda.synchronize()
    assert rgb.shape==(1,64,64,3) and alpha.max()>0
    assert means.grad is not None and torch.isfinite(means.grad).all() and means.grad.norm()>0
    assert colors.grad is not None and torch.isfinite(colors.grad).all() and colors.grad.norm()>0
    result={'status':'passed','torch':torch.__version__,'torch_cuda':torch.version.cuda,
            'gsplat':gsplat.__version__,'device':torch.cuda.get_device_name(0),
            'forward_backward_seconds':time.perf_counter()-start,
            'position_gradient_norm':float(means.grad.norm()),'color_gradient_norm':float(colors.grad.norm()),
            'cuda_peak_allocated_bytes':torch.cuda.max_memory_allocated(),
            'note':'Real one-Gaussian CUDA render/backward; not a reconstruction-quality benchmark.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
