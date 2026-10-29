#!/usr/bin/env python3
"""fps-debug: summarises a samply profile (Firefox processed format).
Prints, per busy thread, the share of samples by library (self) and the top
self/inclusive functions, symbolicated with the --unstable-presymbolicate
sidecar when present. Usage: prof_summary.py profile.json.gz [frames]"""
import bisect, collections, gzip, json, os, sys

path = sys.argv[1]
frames = float(sys.argv[2]) if len(sys.argv) > 2 else 0
# Optional: only the last LAST seconds of each thread (steady state).
last = float(sys.argv[3]) if len(sys.argv) > 3 else 0
op = gzip.open if path.endswith('.gz') else open
with op(path, 'rt', encoding='utf-8') as f:
    prof = json.load(f)
libs = prof.get('libs', [])
shared = prof.get('shared', {})
syms = {}
for side in (path.replace('.json.gz', '.json.syms.json'), path + '.syms.json', path.replace('.json.gz', '.syms.json')):
    if os.path.exists(side):
        try:
            sj = json.load(open(side, encoding='utf-8'))
            st = sj.get('string_table', [])
            for d in sj.get('data', []):
                tab = sorted((e['rva'], e.get('size', 0), st[e['symbol']] if isinstance(e['symbol'], int) else e['symbol']) for e in d.get('symbol_table', []))
                syms[d.get('debug_name', '').lower()] = ([t[0] for t in tab], tab)
            print(f'symbols: {side} ({len(syms)} libs)')
        except Exception as e:
            print('symbols: failed', side, e)
        break
else:
    print('symbols: no sidecar; files:', os.listdir(os.path.dirname(path) or '.'))

def col(t, k):
    v = t.get(k)
    return v if v is not None else []

def sym(libname, addr):
    s = syms.get(libname.lower())
    if not s or addr is None:
        return None
    i = bisect.bisect_right(s[0], addr) - 1
    if i < 0:
        return None
    return s[1][i][2]

threads = prof.get('threads', [])
info = []
for th in threads:
    n = th.get('samples', {}).get('length') or len(col(th.get('samples', {}), 'stack'))
    info.append((n, th))
info.sort(key=lambda x: -x[0])
interval = prof.get('meta', {}).get('interval', 1.0)
print(f"meta interval {interval} ms, {len(threads)} threads, libs {len(libs)}")
for n, th in info[:8]:
    if n == 0:
        continue
    strings = th.get('stringArray') or th.get('stringTable') or shared.get('stringArray') or []
    if isinstance(strings, dict):
        strings = strings.get('_array', [])
    smp, stk, frm, fun, res = th['samples'], th['stackTable'], th['frameTable'], th['funcTable'], th.get('resourceTable', {})
    s_stack = col(smp, 'stack'); s_w = smp.get('weight') or [1] * len(s_stack)
    s_t = col(smp, 'time'); s_cpu = smp.get('threadCPUDelta') or [None] * len(s_stack)
    if last and s_t:
        t_end = max(t for t in s_t if t is not None) - 1000.0  # drop the exit second
        keep = [i for i, t in enumerate(s_t) if t is not None and t_end - last * 1000 <= t <= t_end]
        s_stack = [s_stack[i] for i in keep]; s_w = [s_w[i] for i in keep]; s_cpu = [s_cpu[i] for i in keep]
    st_frame, st_prefix = col(stk, 'frame'), col(stk, 'prefix')
    fr_func, fr_addr = col(frm, 'func'), col(frm, 'address')
    fn_name, fn_res = col(fun, 'name'), col(fun, 'resource')
    rs_lib = col(res, 'lib')
    def libof(fi):
        r = fn_res[fi] if fi < len(fn_res) else -1
        if r is None or r < 0 or r >= len(rs_lib):
            return '?'
        li = rs_lib[r]
        return libs[li].get('debugName') or libs[li].get('name') if li is not None and 0 <= li < len(libs) else '?'
    cache = {}
    def fname(fr):
        if fr in cache:
            return cache[fr]
        fi = fr_func[fr]
        lib = libof(fi)
        nm = strings[fn_name[fi]] if fn_name[fi] < len(strings) else '?'
        if nm.startswith(('0x', 'fun_')) or nm == '?':
            s = sym(lib, fr_addr[fr] if fr < len(fr_addr) else None)
            if s:
                nm = s
        nm = nm[:110]
        cache[fr] = (lib, nm)
        return cache[fr]
    self_lib = collections.Counter(); self_fn = collections.Counter(); incl_fn = collections.Counter(); incl_lib = collections.Counter()
    tot = 0; cpu_tot = 0.0
    for s, w, cd in zip(s_stack, s_w, s_cpu):
        if s is None:
            continue
        tot += w
        cpu_tot += cd or 0
        lib, nm = fname(st_frame[s])
        self_lib[lib] += w; self_fn[(lib, nm)] += w
        seen = set(); seenl = set(); x = s; depth = 0
        while x is not None and depth < 400:
            l2, n2 = fname(st_frame[x])
            if (l2, n2) not in seen:
                seen.add((l2, n2)); incl_fn[(l2, n2)] += w
            if l2 not in seenl:
                seenl.add(l2); incl_lib[l2] += w
            x = st_prefix[x]; depth += 1
    nm = th.get('name', '?'); tid = th.get('tid', '?')
    per = f", {tot * interval / frames:.1f} ms/frame" if frames and not last else ''
    per += f", cpu delta sum {cpu_tot:.0f}" 
    print(f"\n=== thread {nm} tid {tid}: {tot} samples ({tot * interval / 1000:.1f} s){per}")
    print('  self by lib: ' + ', '.join(f"{l} {100*c/tot:.1f}%" for l, c in self_lib.most_common(10)))
    print('  incl by lib: ' + ', '.join(f"{l} {100*c/tot:.1f}%" for l, c in incl_lib.most_common(12)))
    print('  top self:')
    for (l, f_), c in self_fn.most_common(25):
        print(f"    {100*c/tot:5.1f}%  {l}!{f_}")
    print('  top inclusive (sandbox/wgpu/forja):')
    k = 0
    for (l, f_), c in incl_fn.most_common(400):
        if any(t in f_ for t in ('wgpu', 'forja', 'sandbox', 'naga', 'egui', 'ExecuteCommandLists', 'Present', 'rayon')) or l.lower().startswith(('d3d', 'dxgi')):
            print(f"    {100*c/tot:5.1f}%  {l}!{f_}"); k += 1
            if k >= 40:
                break
