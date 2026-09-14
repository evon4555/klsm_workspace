"""Observability and fault-injection routes."""

import asyncio

from fastapi import APIRouter


router = APIRouter()


def configure_router(*, metrics_client_instance, metrics_config_instance):
    global metrics_client, metrics_config
    metrics_client = metrics_client_instance
    metrics_config = metrics_config_instance
    return router


# ---------------------------------------------------------------------------
# Observability — Pyroscope (flame graph) + Loki (logs) + Toxiproxy (chaos)
# ---------------------------------------------------------------------------

@router.get("/api/observability/status")
async def observability_status():
    """Check connectivity to Pyroscope, Loki, and Toxiproxy."""
    pyro, loki, toxi = await asyncio.gather(
        metrics_client.check_pyroscope(),
        metrics_client.check_loki(),
        metrics_client.check_toxiproxy(),
    )
    return {
        "pyroscope": {"connected": pyro, "url": metrics_config.pyroscope_url},
        "loki": {"connected": loki, "url": metrics_config.loki_url},
        "toxiproxy": {"connected": toxi, "url": metrics_config.toxiproxy_url},
    }


@router.get("/api/observability/flamegraph")
async def get_flamegraph(query: str = "process_cpu", from_ts: str = "now-1h", until_ts: str = "now"):
    """Get flame graph data from Pyroscope (or mock data for demo)."""
    return await metrics_client.get_flame_graph(query, from_ts, until_ts)


@router.get("/api/observability/logs")
async def get_logs(query: str = '{job="fastapi-app"}', limit: int = 100):
    """Query logs from Loki (or mock data for demo)."""
    return await metrics_client.query_loki(query, limit)


@router.get("/api/observability/toxiproxy/proxies")
async def list_toxi_proxies():
    """List all Toxiproxy proxies."""
    return await metrics_client.list_proxies()


@router.post("/api/observability/toxiproxy/toxic")
async def add_toxi_toxic(proxy_name: str, toxic_type: str, latency: int = 500, jitter: int = 100):
    """Add a toxic to a proxy. For demo: returns mock confirmation when Toxiproxy is not running."""
    connected = await metrics_client.check_toxiproxy()
    if not connected:
        return {
            "status": "demo",
            "message": f"[Demo Mode] Would inject {toxic_type} toxic on proxy '{proxy_name}' with latency={latency}ms jitter={jitter}ms",
            "toxic": {
                "name": f"{proxy_name}-{toxic_type}",
                "type": toxic_type,
                "proxy": proxy_name,
                "attributes": {"latency": latency, "jitter": jitter},
            },
        }

    attrs = {"latency": latency, "jitter": jitter} if toxic_type == "latency" else {"rate": latency}
    return await metrics_client.add_toxic(proxy_name, toxic_type, attrs)


@router.post("/api/observability/toxiproxy/reset")
async def reset_toxi():
    """Reset all toxics."""
    connected = await metrics_client.check_toxiproxy()
    if not connected:
        return {"status": "demo", "message": "[Demo Mode] Would reset all toxics"}
    await metrics_client.reset_toxiproxy()
    return {"status": "ok"}


