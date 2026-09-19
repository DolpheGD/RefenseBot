import gc
import os
import sys
import threading
import time

from bot.config import BOT_MEMORY_CHECK_SECONDS, BOT_MEMORY_LIMIT_MB


def _get_rss_mb() -> float:
    """Best-effort RSS usage in MB. Works on Linux via /proc/self/status."""
    try:
        with open('/proc/self/status', 'r', encoding='utf-8') as fh:
            for line in fh:
                if line.startswith('VmRSS:'):
                    kb = int(line.split()[1])
                    return kb / 1024.0
        return 0.0
    except Exception:
        return 0.0


def trigger_memory_cleanup() -> float:
    """Run a GC pass and return current RSS in MB. If memory is still high,
    this function does not kill the process; the watchdog thread handles that.
    """
    gc.collect()
    return _get_rss_mb()


def start_memory_watchdog() -> None:
    """Starts a daemon thread that gracefully exits once RSS exceeds BOT_MEMORY_LIMIT_MB.

    A supervisor (systemd, docker, cron, etc.) can then restart the process cleanly.
    """
    limit_mb = BOT_MEMORY_LIMIT_MB
    if limit_mb <= 0:
        return

    def worker() -> None:
        while True:
            try:
                rss_mb = _get_rss_mb()
                if rss_mb > limit_mb:
                    print(f"[memory-watchdog] RSS {rss_mb:.1f}MB exceeds limit {limit_mb}MB. Running cleanup...")
                    rss_after_gc = trigger_memory_cleanup()
                    if rss_after_gc > limit_mb:
                        print(f"[memory-watchdog] RSS still high after cleanup ({rss_after_gc:.1f}MB). Exiting to allow supervisor restart.")
                        raise SystemExit(0)
            except SystemExit:
                raise
            except Exception as exc:  # pragma: no cover - watchdog should never crash the bot
                print(f"[memory-watchdog] unexpected error: {exc}")
            time.sleep(BOT_MEMORY_CHECK_SECONDS)

    thread = threading.Thread(target=worker, name='memory-watchdog', daemon=True)
    thread.start()
