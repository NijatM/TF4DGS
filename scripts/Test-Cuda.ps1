# Compile and run both native and forced-PTX CUDA checks on the installed GPU.
[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'Initialize-BuildSession.ps1')
$Preflight = Join-Path $Builds 'cuda-preflight'
New-Item -ItemType Directory -Path $Preflight -Force | Out-Null
$Source = Join-Path $Preflight 'cuda_check.cu'
$Exe = Join-Path $Preflight 'cuda_check.exe'
@'
#include <cuda_runtime.h>
#include <cstdio>
static bool ok(cudaError_t status, const char* step) {
    if (status == cudaSuccess) return true;
    std::fprintf(stderr, "%s: %s\n", step, cudaGetErrorString(status));
    return false;
}
__global__ void write_value(int* value) { *value = 42; }
int main() {
    int count = 0;
    if (!ok(cudaGetDeviceCount(&count), "Device count") || count < 1) return 1;
    cudaDeviceProp properties{};
    if (!ok(cudaGetDeviceProperties(&properties, 0), "Device properties")) return 1;
    std::printf("GPU: %s; compute capability %d.%d\n", properties.name, properties.major, properties.minor);
    int* device_value = nullptr;
    if (!ok(cudaMalloc(reinterpret_cast<void**>(&device_value), sizeof(int)), "Allocate")) return 1;
    write_value<<<1, 1>>>(device_value);
    if (!ok(cudaGetLastError(), "Launch") || !ok(cudaDeviceSynchronize(), "Synchronize")) return 1;
    int value = 0;
    if (!ok(cudaMemcpy(&value, device_value, sizeof(int), cudaMemcpyDeviceToHost), "Read back")) return 1;
    if (!ok(cudaFree(device_value), "Free")) return 1;
    std::printf("Kernel result: %d\n", value);
    return value == 42 ? 0 : 1;
}
'@ | Set-Content -LiteralPath $Source -Encoding ASCII
Invoke-CheckedNative $Nvcc @('-std=c++20', '-arch=sm_86', $Source, '-o', $Exe) (Join-Path $Logs 'cuda-preflight-build.log')
Invoke-CheckedNative $Exe @() (Join-Path $Logs 'cuda-preflight-native.log')
$PreviousPtxSetting = $env:CUDA_FORCE_PTX_JIT
try {
    $env:CUDA_FORCE_PTX_JIT = '1'
    Invoke-CheckedNative $Exe @() (Join-Path $Logs 'cuda-preflight-ptx.log')
} finally {
    $env:CUDA_FORCE_PTX_JIT = $PreviousPtxSetting
}
$Record = [ordered]@{
    project = 'TF4DGS'
    validated_utc = [DateTime]::UtcNow.ToString('o')
    cuda_root = $CudaRoot
    compiler_toolset = $env:VCToolsVersion
    windows_sdk = $env:WindowsSDKVersion
    compile_passed = $true
    native_kernel_passed = $true
    forced_ptx_kernel_passed = $true
    expected_kernel_result = 42
    executable_path = $Exe
}
$Record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $ProjectRoot 'cuda-validation.json') -Encoding UTF8
Write-Output 'CUDA compile, native GPU execution and driver PTX compilation passed.'
