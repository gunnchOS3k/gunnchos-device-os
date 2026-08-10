#!/usr/bin/env python3
"""Debug/profiling template — CPU/mem markers for local sessions."""
import time, resource, json

def profile(fn):
    start = time.time()
    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    result = fn()
    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "result": result,
        "elapsed_s": time.time() - start,
        "user_cpu_s": ru1.ru_utime - ru0.ru_utime,
        "max_rss_kb": ru1.ru_maxrss,
    }
