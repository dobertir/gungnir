"""
sync/run_sync_and_rebuild.py
-----------------------------
Entry point for the Railway Cron service.
Runs the monthly data sync then rebuilds embeddings sequentially.

Railway Cron config:
  Start Command : python sync/run_sync_and_rebuild.py
  Cron Schedule : 0 3 1 * *   (1st of every month at 03:00 UTC)
"""

import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("corfo.cron")

# Prefer public URL when running outside Railway's internal network
os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get("DATABASE_PUBLIC_URL", "") or os.environ.get("DATABASE_URL", ""),
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync.datainnovacion_sync import run_sync  # noqa: E402


def main():
    log.info("=== Cron job iniciado ===")
    t0 = time.perf_counter()

    # ── Step 1: sync data ────────────────────────────────────────────────────
    log.info("Paso 1/2: sincronizando datos desde datainnovacion.cl ...")
    result = run_sync()
    if result.get("status") != "ok":
        log.error("Sync falló: %s", result.get("error_message"))
        sys.exit(1)
    log.info(
        "Sync completado — %d filas obtenidas, %d upserted",
        result.get("rows_fetched", 0),
        result.get("rows_upserted", 0),
    )

    # ── Step 2: rebuild embeddings ───────────────────────────────────────────
    log.info("Paso 2/2: reconstruyendo embeddings ...")
    try:
        import build_embeddings
        build_embeddings.main()
    except Exception as e:
        log.error("Rebuild de embeddings falló (no crítico): %s", e)

    elapsed = time.perf_counter() - t0
    log.info("=== Cron job completado en %.0fs ===", elapsed)


if __name__ == "__main__":
    main()
