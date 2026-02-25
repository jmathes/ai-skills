---
name: kernel-memory-diagnosis
description: Diagnose Windows kernel memory leaks causing "Secure System" process growth. Use when asked about high memory usage, kernel pool leaks, Secure System RAM consumption, system sluggishness requiring restarts, or nonpaged/paged pool growth.
---

# Kernel Memory Leak Diagnosis

Diagnose and identify the root causes of Windows kernel memory leaks, particularly when the "Secure System" process grows over time. This skill provides a systematic diagnostic workflow using pool tag analysis, driver identification, and ETW session auditing.

## Background

"Secure System" is the VTL 1 (Virtual Trust Level 1) secure kernel process that hosts HVCI (Hypervisor-protected Code Integrity). It maintains tracking records for kernel memory pages. When drivers leak pool memory (allocate and never free), HVCI's tracking state for those pages persists, causing Secure System's working set to balloon proportionally. **Secure System growth is a symptom of kernel pool leaks, not the cause.**

## Diagnostic Workflow

### Step 1: Baseline System State

Collect uptime, RAM usage, and kernel pool counters:

```powershell
# Uptime and RAM
$os = Get-CimInstance Win32_OperatingSystem
$uptime = (Get-Date) - $os.LastBootUpTime
Write-Host "Uptime: $($uptime.Days)d $($uptime.Hours)h"
Write-Host "Total RAM: $([math]::Round($os.TotalVisibleMemorySize/1MB, 1)) GB"
Write-Host "Free RAM: $([math]::Round($os.FreePhysicalMemory/1MB, 1)) GB"

# Kernel pool counters
$perf = Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
Write-Host "Pool Nonpaged: $([math]::Round($perf.PoolNonpagedBytes/1MB, 1)) MB"
Write-Host "Pool Paged: $([math]::Round($perf.PoolPagedBytes/1MB, 1)) MB"
Write-Host "Committed: $([math]::Round($perf.CommittedBytes/1GB, 2)) GB"

# Secure System size
$ss = Get-Process -Name 'Secure System' -ErrorAction SilentlyContinue
Write-Host "Secure System WS: $([math]::Round($ss.WorkingSet64/1MB, 0)) MB"
```

**Red flags:**
- Nonpaged pool > 500 MB
- Paged pool > 1.5 GB
- Secure System > 1 GB
- Committed bytes significantly exceeding physical RAM

### Step 2: Pool Tag Snapshot

Use Python to read kernel pool tags via `NtQuerySystemInformation`. This identifies which kernel components are consuming memory:

```python
# Save as pool_tag_snapshot.py and run with: python pool_tag_snapshot.py
import ctypes, struct

def get_pool_tags():
    ntdll = ctypes.WinDLL('ntdll')
    buf_size = 2 * 1024 * 1024
    buf = ctypes.create_string_buffer(buf_size)
    ret_len = ctypes.c_ulong(0)
    status = ntdll.NtQuerySystemInformation(22, buf, buf_size, ctypes.byref(ret_len))
    if status != 0:
        print(f'Failed: 0x{status & 0xFFFFFFFF:08X}')
        return

    data = buf.raw[:ret_len.value]
    count = struct.unpack_from('<I', data, 0)[0]
    entries = []
    offset = 8
    for _ in range(count):
        if offset + 40 > len(data): break
        tag = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[offset:offset+4])
        pa, pf = struct.unpack_from('<II', data, offset + 4)
        pu = struct.unpack_from('<Q', data, offset + 16)[0]
        npa, npf = struct.unpack_from('<II', data, offset + 24)
        npu = struct.unpack_from('<Q', data, offset + 32)[0]
        total = pu + npu
        if total > 1024 * 1024:
            entries.append((tag, pu, npu, pa - pf, npa - npf))
        offset += 40

    entries.sort(key=lambda x: x[1] + x[2], reverse=True)
    print(f'  Tag   Paged_MB   NP_MB     P_Outs     NP_Outs')
    print('-' * 52)
    for tag, pu, npu, po, npo in entries:
        print(f'  {tag:4s} {pu / (1024**2):>8.1f} {npu / (1024**2):>8.1f} {po:>10,} {npo:>10,}')

get_pool_tags()
```

### Step 3: Pool Tag Delta Tracking

A snapshot shows what's **big**, but not what's **growing**. Use `pool_tag_tracker.py` (included in this skill's directory) to sample pool tags over time and identify monotonically increasing tags — the actual leakers:

```
python pool_tag_tracker.py 30 10
```

This samples every 30 seconds for 10 iterations (5 minutes total) and reports which tags are actively growing, with estimated daily leak rates.

### Step 4: Identify Tag Owners

Cross-reference the top pool tags with known owners:

| Tag prefix | Owner |
|------------|-------|
| `Vi*` (Vi54, Vi12, Vi01, Vi03, etc.) | Intel/AMD/NVIDIA GPU driver (video) |
| `Mp*` (Mpus, MPCp, MPfn, MPpX, MPsc) | Windows Defender (MpFilter.sys) |
| `Etw*` (EtwB, EtwR, EtwD) | ETW tracing session buffers |
| `Ale*` (AleS, AleE) | WFP Application Layer Enforcement (network filtering) |
| `Con*` (ConT, Cont) | Container / Hyper-V networking |
| `Ntf*` (NtfF, Ntff) | NTFS file system |
| `FM*` (FMfn, FMsl) | Filter Manager (minifilter drivers) |
| `sm*` (smNp, smCB, smBt) | Storage Manager |
| `Thre` | Thread objects |
| `File` | File objects |
| `HalD` | HAL DMA allocations |
| `PMcp` | Check running drivers with `pm` or `port` in name |

For unrecognized tags, search the Microsoft internal ADO `OS` project:
```
almsearch.dev.azure.com/microsoft — searchText: "<TAG> pool tag"
```

### Step 5: Audit ETW Sessions

Excessive ETW tracing is a common source of nonpaged pool bloat in enterprise environments:

```powershell
logman query -ets 2>&1
```

**Normal:** 15–25 sessions. **Elevated:** 30+. **Excessive:** 50+.

Common enterprise ETW overhead sources:
- MDE/Sense trace loggers
- Endpoint DLP
- Global Secure Access Client
- Diagtrack (telemetry)
- Intel driver auto-loggers

### Step 6: Check Drivers and Crash History

```powershell
# Non-Microsoft kernel drivers (leak suspects)
Get-CimInstance Win32_SystemDriver | Where-Object { $_.State -eq 'Running' } |
    ForEach-Object {
        $path = $_.PathName -replace '\\SystemRoot','C:\Windows' -replace '\\??\\','' -replace '"',''
        if (Test-Path $path -EA SilentlyContinue) {
            $vi = (Get-Item $path).VersionInfo
            if ($vi.CompanyName -and $vi.CompanyName -notmatch 'Microsoft') {
                [PSCustomObject]@{ Name=$_.Name; Company=$vi.CompanyName; Path=$path }
            }
        }
    } | Format-Table -AutoSize

# Recent BSODs
Get-WinEvent -FilterHashtable @{LogName='System'; Id=1001; ProviderName='Microsoft-Windows-WER-SystemErrorReporting'} -MaxEvents 5 -EA SilentlyContinue |
    Select-Object TimeCreated, @{N='Msg';E={$_.Message.Substring(0, [Math]::Min(300, $_.Message.Length))}} | Format-List
```

### Step 7: VBS/HVCI Status

Confirm whether HVCI is the mechanism amplifying pool leaks:

```powershell
$dg = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace 'root\Microsoft\Windows\DeviceGuard'
Write-Host "VBS Status: $($dg.VirtualizationBasedSecurityStatus)"  # 2 = Running
Write-Host "Services Running: $($dg.SecurityServicesRunning -join ', ')"  # 1=CredGuard, 2=HVCI
```

## Common Fixes (Priority Order)

1. **Update GPU drivers** — Intel Arc (DG2) has known kernel pool leak bugs (ADO [49178845](https://microsoft.visualstudio.com/OS/_workitems/edit/49178845), [42233897](https://microsoft.visualstudio.com/OS/_workitems/edit/42233897)). Use Intel Driver & Support Assistant or download directly from Intel.
2. **Update Wi-Fi/NIC drivers** — disconnect/reconnect cycles can leak incrementally.
3. **Quit Docker Desktop when idle** — keeps Hyper-V Default Switch and container pool tags alive.
4. **Review Defender scan exclusions** — large dev directories cause high `Mpus` allocations. *Only if organizational policy permits.*
5. **File a Feedback Hub report** — include pool tag data, ETW count, Secure System size, and uptime.

## Key Concept: Why Secure System Grows

HVCI (running in VTL 1) enforces W^X (Write XOR Execute) on kernel pages via SLAT/EPT entries. It maintains tracking metadata for every kernel page's integrity state. When a driver leaks pool memory and never frees it, VTL 1 never receives the "page freed" notification, so its metadata for those pages persists indefinitely. The Secure System working set is proportional to total accumulated kernel pool usage — fix the pool leaks and Secure System shrinks.
