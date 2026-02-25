"""
Pool tag delta tracker — samples kernel pool tags periodically and shows which are growing.
The one(s) growing monotonically = the leak.
"""
import ctypes
import struct
import time
import sys

def get_pool_tags():
    ntdll = ctypes.WinDLL('ntdll')
    buf_size = 2 * 1024 * 1024
    buf = ctypes.create_string_buffer(buf_size)
    ret_len = ctypes.c_ulong(0)
    status = ntdll.NtQuerySystemInformation(22, buf, buf_size, ctypes.byref(ret_len))
    if status != 0:
        return {}

    data = buf.raw[:ret_len.value]
    count = struct.unpack_from('<I', data, 0)[0]
    tags = {}
    offset = 8
    for _ in range(count):
        if offset + 40 > len(data):
            break
        tag = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[offset:offset+4])
        pa, pf = struct.unpack_from('<II', data, offset + 4)
        pu = struct.unpack_from('<Q', data, offset + 16)[0]
        npa, npf = struct.unpack_from('<II', data, offset + 24)
        npu = struct.unpack_from('<Q', data, offset + 32)[0]
        tags[tag] = {'paged': pu, 'nonpaged': npu, 'p_out': pa - pf, 'np_out': npa - npf}
        offset += 40
    return tags

def main():
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    samples = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    min_delta_kb = 100  # only show tags that grew by at least this much

    print(f"Sampling pool tags every {interval}s for {samples} samples ({interval * samples}s total)")
    print(f"Will show tags that grow by >= {min_delta_kb} KB between first and last sample")
    print()

    baseline = get_pool_tags()
    print(f"[0s] Baseline captured: {len(baseline)} tags")

    history = []
    for i in range(1, samples + 1):
        time.sleep(interval)
        current = get_pool_tags()
        elapsed = i * interval

        # Compare to baseline
        growers = []
        for tag, cur in current.items():
            base = baseline.get(tag, {'paged': 0, 'nonpaged': 0, 'p_out': 0, 'np_out': 0})
            d_paged = cur['paged'] - base['paged']
            d_np = cur['nonpaged'] - base['nonpaged']
            d_total = d_paged + d_np
            if d_total > min_delta_kb * 1024:
                growers.append((tag, d_paged, d_np, d_total, cur['paged'] + cur['nonpaged']))

        growers.sort(key=lambda x: x[3], reverse=True)

        print(f"\n[{elapsed}s] Tags growing since baseline:")
        if not growers:
            print("  (none exceeding threshold)")
        else:
            print(f"  {'Tag':>6}  {'Delta_KB':>10}  {'D_Paged_KB':>12}  {'D_NP_KB':>10}  {'Total_MB':>10}")
            print(f"  {'-'*54}")
            for tag, dp, dnp, dt, total in growers[:15]:
                print(f"  {tag:>6}  {dt/1024:>10.1f}  {dp/1024:>12.1f}  {dnp/1024:>10.1f}  {total/(1024**2):>10.1f}")

        history.append((elapsed, growers))

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY — Monotonic growers (leak suspects)")
    print("=" * 60)
    final = get_pool_tags()
    suspects = []
    for tag, cur in final.items():
        base = baseline.get(tag, {'paged': 0, 'nonpaged': 0})
        d_total = (cur['paged'] + cur['nonpaged']) - (base['paged'] + base['nonpaged'])
        if d_total > min_delta_kb * 1024:
            rate_kb_per_min = (d_total / 1024) / (samples * interval / 60)
            suspects.append((tag, d_total, rate_kb_per_min, cur['paged'] + cur['nonpaged']))

    suspects.sort(key=lambda x: x[1], reverse=True)
    if not suspects:
        print("No tags grew significantly during the monitoring period.")
        print("Try a longer monitoring period or use the system more actively.")
    else:
        print(f"  {'Tag':>6}  {'Growth_KB':>10}  {'Rate_KB/min':>12}  {'Current_MB':>12}  {'Est_MB/day':>12}")
        print(f"  {'-'*62}")
        for tag, dt, rate, total in suspects:
            est_day = rate * 60 * 24 / 1024
            print(f"  {tag:>6}  {dt/1024:>10.1f}  {rate:>12.1f}  {total/(1024**2):>12.1f}  {est_day:>12.1f}")

if __name__ == '__main__':
    main()
