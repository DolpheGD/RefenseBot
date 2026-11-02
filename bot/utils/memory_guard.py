import gc
import logging
import threading
import time

from bot.config import BOT_MEMORY_CHECK_SECONDS, BOT_MEMORY_LIMIT_MB

logger = logging.getLogger("refensebot.memory")


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
    """Run a GC pass and return current RSS in MB."""
    gc.collect()
    return _get_rss_mb()


def start_memory_watchdog() -> None:
    """Watch RSS and log memory pressure. If a positive limit is configured,
    it may exit the process only after logging a clear shutdown warning.
    """
    limit_mb = BOT_MEMORY_LIMIT_MB
    if limit_mb <= 0:
        logger.info("Memory watchdog disabled (BOT_MEMORY_LIMIT_MB=%s)", limit_mb)
        return

    def worker() -> None:
        while True:
            try:
                rss_mb = _get_rss_mb()
                if rss_mb > limit_mb:
                    logger.warning(
                        "RSS %.1fMB exceeds limit %sMB. Running cleanup...",
                        rss_mb,
                        limit_mb,
                    )
                    rss_after_gc = trigger_memory_cleanup()
                    if rss_after_gc > limit_mb:
                        logger.critical(
                            "RSS still high after cleanup (%.1fMB). Logging shutdown state; process remains running unless the supervisor stops it.",
                            rss_after_gc,
                        )
                        # Keep the process alive and leave an explicit reason in the logs.
                        # A parent supervisor can still restart it if required.
                        continue
            except Exception as exc:  # pragma: no cover - watchdog should never crash the bot
                logger.exception("Unexpected memory-watchdog error: %s", exc)
            time.sleep(BOT_MEMORY_CHECK_SECONDS)

    thread = threading.Thread(target=worker, name='memory-watchdog', daemon=True)
    thread.start()
