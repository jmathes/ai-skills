---
name: kernel-memory-diagnosis
description: Diagnose Windows kernel memory leaks causing "Secure System" process growth. Use when asked about high memory usage, kernel pool leaks, Secure System RAM consumption, system sluggishness requiring restarts, or nonpaged/paged pool growth.
metadata:
  readme: README.md
---

Secure System = VTL1 HVCI process. Tracks kernel page integrity via SLAT/EPT. Grows proportionally to leaked pool memory (symptom, not cause). Fix pool leaks → Secure System shrinks.

## Workflow

1. Baseline: `Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory` → PoolNonpagedBytes, PoolPagedBytes. Red flags: NP>500MB, Paged>1.5GB, SecSys>1GB
2. Snapshot pool tags: `NtQuerySystemInformation(22)` — see `pool_tag_tracker.py` in this dir
3. Delta track: `python pool_tag_tracker.py 30 10` — finds monotonically growing tags (actual leakers)
4. Identify tag owners (below)
5. Audit ETW: `logman query -ets` — normal 15-25, elevated 30+, excessive 50+
6. Check non-MS drivers: `Get-CimInstance Win32_SystemDriver` filtered by CompanyName
7. Confirm HVCI: `Win32_DeviceGuard` namespace `root\Microsoft\Windows\DeviceGuard`, VBS status 2=running

## Tag owners

Vi*=GPU, Mp*=Defender/MpFilter.sys, Etw*=ETW buffers, Ale*=WFP, Con*=container/Hyper-V, Ntf*=NTFS, FM*=FilterMgr, sm*=StorageMgr, Thre=threads, File=file objects, HalD=HAL DMA, PMcp=port monitor drivers

Unknown tags: search `almsearch.dev.azure.com/microsoft` for `"<TAG> pool tag"`

## Fixes (priority order)

1. Update GPU drivers — Intel Arc/DG2 known leaks: [49178845](https://microsoft.visualstudio.com/OS/_workitems/edit/49178845), [42233897](https://microsoft.visualstudio.com/OS/_workitems/edit/42233897)
2. Update Wi-Fi/NIC drivers
3. Quit Docker Desktop when idle (Hyper-V Default Switch pool tags)
4. Defender scan exclusions for large dev dirs (if policy permits)
5. Feedback Hub report with pool tag data + ETW count + uptime
