"""
Metrics Client — unified interface to query Prometheus and Grafana.

Each integration is independent and fails gracefully when the service is unavailable.
When a service is not reachable, the client returns mock/demo data so the dashboard
still works for demonstration purposes.

Usage:
    client = MetricsClient(config)
    metrics = await client.get_prometheus_metrics("k6_http_req_duration", "1h")
    panels = client.get_grafana_panel_urls(dashboard_uid, panel_ids)
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

try:
    # `httpx` is only used here for the dashboard backend to query observability
    # services. It is separate from Playwright APIRequestContext used in tests.
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class MetricsConfig:
    """Configuration for external metrics services."""

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        grafana_url: str = "http://localhost:3000",
        grafana_api_key: str = "",
        grafana_dashboard_uid: str = "",
        pyroscope_url: str = "http://localhost:4040",
        loki_url: str = "http://localhost:3100",
        toxiproxy_url: str = "http://localhost:8474",
    ):
        self.prometheus_url = prometheus_url.rstrip("/")
        self.grafana_url = grafana_url.rstrip("/")
        self.grafana_api_key = grafana_api_key
        self.grafana_dashboard_uid = grafana_dashboard_uid
        self.pyroscope_url = pyroscope_url.rstrip("/")
        self.loki_url = loki_url.rstrip("/")
        self.toxiproxy_url = toxiproxy_url.rstrip("/")


class MetricsClient:
    """Dashboard backend client for Prometheus, Grafana, and related services."""

    # Timeout for health checks (seconds) -- kept short so the dashboard loads fast
    _HEALTH_TIMEOUT = 1.0
    # Timeout for data queries (seconds)
    _QUERY_TIMEOUT = 1.5
    # How long to cache a health-check result (seconds)
    _HEALTH_CACHE_TTL = 60
    # TCP pre-check timeout -- on Windows, connection refused doesn't return
    # quickly, so we use a short socket probe first to avoid blocking httpx
    _TCP_PROBE_TIMEOUT = 0.15

    def __init__(self, config: MetricsConfig):
        self.config = config
        # Cache: service_name -> (timestamp, bool)
        self._health_cache: dict[str, tuple[float, bool]] = {}

    @staticmethod
    def _make_client(timeout: float) -> "httpx.AsyncClient":
        """Create an httpx client with dual-stack loopback support.

        Historical: when Prometheus/Loki ran in WSL2 Docker, their published
        ports came back via IPv6 [::1] and httpx's default IPv4-first probe
        would hang on Windows. Since 2026-05-27 those services are Windows
        native and listen on 0.0.0.0, so IPv4 works directly — but the
        dual-stack transport stays as defense-in-depth (no harm, costs
        nothing).
        """
        transport = httpx.AsyncHTTPTransport(local_address="::0")
        return httpx.AsyncClient(timeout=timeout, transport=transport)

    def _get_cached_health(self, service: str) -> bool | None:
        """Return cached health status if still fresh, else None."""
        if service in self._health_cache:
            ts, result = self._health_cache[service]
            if time.time() - ts < self._HEALTH_CACHE_TTL:
                return result
        return None

    def _set_cached_health(self, service: str, connected: bool) -> bool:
        self._health_cache[service] = (time.time(), connected)
        return connected

    @staticmethod
    def _tcp_port_open(url: str, timeout: float = 0.15) -> bool:
        """Fast TCP probe: return True only if the port accepts connections.

        On Windows, connecting to a non-listening localhost port never gets a
        quick RST -- it always burns the full timeout. Using a very short
        timeout (150ms) lets us fail fast while still catching real services.

        Tries both IPv4 and IPv6 for defense-in-depth — the Windows-native
        observability services bind to 0.0.0.0 so either family resolves.
        """
        import socket
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        # Try IPv6 first, then IPv4 — covers either binding choice
        families = [(socket.AF_INET6, "::1"), (socket.AF_INET, "127.0.0.1")]
        if host not in ("localhost", "127.0.0.1", "::1"):
            # External host — just try IPv4
            families = [(socket.AF_INET, host)]

        for family, addr in families:
            s = socket.socket(family, socket.SOCK_STREAM)
            s.settimeout(timeout)
            try:
                s.connect((addr, port))
                s.close()
                return True
            except (OSError, socket.timeout):
                s.close()
        return False

    # -----------------------------------------------------------------------
    # Prometheus
    # -----------------------------------------------------------------------

    async def query_prometheus(
        self,
        query: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        step: str = "60s",
    ) -> dict:
        """Query Prometheus range API. Falls back to mock data if unavailable."""
        if not HAS_HTTPX or not self._tcp_port_open(self.config.prometheus_url, self._TCP_PROBE_TIMEOUT):
            return self._mock_prometheus_range(query)

        try:
            now = datetime.utcnow()
            if not end:
                end = now.isoformat() + "Z"
            if not start:
                start = (now - timedelta(hours=1)).isoformat() + "Z"

            params = {
                "query": query,
                "start": start,
                "end": end,
                "step": step,
            }

            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.get(
                    f"{self.config.prometheus_url}/api/v1/query_range",
                    params=params,
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        return self._mock_prometheus_range(query)

    async def query_prometheus_instant(self, query: str) -> dict:
        """Instant Prometheus query. Falls back to mock data."""
        if not HAS_HTTPX or not self._tcp_port_open(self.config.prometheus_url, self._TCP_PROBE_TIMEOUT):
            return self._mock_prometheus_instant(query)

        try:
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.get(
                    f"{self.config.prometheus_url}/api/v1/query",
                    params={"query": query},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        return self._mock_prometheus_instant(query)

    async def check_prometheus(self) -> bool:
        """Check if Prometheus is reachable (cached, with fast TCP pre-check)."""
        cached = self._get_cached_health("prometheus")
        if cached is not None:
            return cached
        if not HAS_HTTPX or not self._tcp_port_open(self.config.prometheus_url, self._TCP_PROBE_TIMEOUT):
            return self._set_cached_health("prometheus", False)
        try:
            async with self._make_client(self._HEALTH_TIMEOUT) as client:
                resp = await client.get(f"{self.config.prometheus_url}/-/healthy")
                return self._set_cached_health("prometheus", resp.status_code == 200)
        except Exception:
            return self._set_cached_health("prometheus", False)

    # -----------------------------------------------------------------------
    # Grafana
    # -----------------------------------------------------------------------

    def get_grafana_panel_url(
        self,
        dashboard_uid: str = "",
        panel_id: int = 1,
        from_time: str = "now-15m",
        to_time: str = "now",
        theme: str = "light",
        refresh: str = "5s",
    ) -> str:
        """Generate a Grafana solo panel iframe URL.

        Defaults tuned for performance tests:
        - `from=now-15m` instead of now-1h so a 60-second test isn't diluted.
        - `refresh=5s` so the iframe pulls fresh data while a test is running
          (without this the iframe loads once and stays frozen forever).
        """
        uid = dashboard_uid or self.config.grafana_dashboard_uid
        if not uid:
            return ""

        params = {
            "orgId": 1,
            "panelId": panel_id,
            "from": from_time,
            "to": to_time,
            "theme": theme,
            "refresh": refresh,
        }
        return f"{self.config.grafana_url}/d-solo/{uid}/?{urlencode(params)}"

    def get_grafana_dashboard_url(
        self,
        dashboard_uid: str = "",
        from_time: str = "now-15m",
        to_time: str = "now",
        refresh: str = "5s",
    ) -> str:
        """Generate a full Grafana dashboard URL (for iframe).
        Same defaults as the solo-panel URL above.
        """
        uid = dashboard_uid or self.config.grafana_dashboard_uid
        if not uid:
            return ""

        params = {"from": from_time, "to": to_time, "kiosk": "", "refresh": refresh}
        return f"{self.config.grafana_url}/d/{uid}/?{urlencode(params)}"

    async def check_grafana(self) -> bool:
        """Check if Grafana is reachable (cached, with fast TCP pre-check)."""
        cached = self._get_cached_health("grafana")
        if cached is not None:
            return cached
        if not HAS_HTTPX or not self._tcp_port_open(self.config.grafana_url, self._TCP_PROBE_TIMEOUT):
            return self._set_cached_health("grafana", False)
        try:
            headers = {}
            if self.config.grafana_api_key:
                headers["Authorization"] = f"Bearer {self.config.grafana_api_key}"
            async with self._make_client(self._HEALTH_TIMEOUT) as client:
                resp = await client.get(f"{self.config.grafana_url}/api/health", headers=headers)
                return self._set_cached_health("grafana", resp.status_code == 200)
        except Exception:
            return self._set_cached_health("grafana", False)

    async def list_grafana_dashboards(self) -> list:
        """List available Grafana dashboards."""
        if not HAS_HTTPX:
            return []
        try:
            headers = {}
            if self.config.grafana_api_key:
                headers["Authorization"] = f"Bearer {self.config.grafana_api_key}"
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.get(f"{self.config.grafana_url}/api/search", headers=headers)
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return []

    # -----------------------------------------------------------------------
    # Mock data generators (for demo when services are unavailable)
    # -----------------------------------------------------------------------

    @staticmethod
    def _mock_prometheus_range(query: str) -> dict:
        """Generate realistic mock Prometheus range query results."""
        now = time.time()
        values = []
        for i in range(60):
            ts = now - (59 - i) * 60
            if "duration" in query or "latency" in query or "resp_time" in query:
                val = random.uniform(80, 350) + random.gauss(0, 30)
            elif "error" in query or "fail" in query:
                val = random.uniform(0.001, 0.05)
            elif "rps" in query or "rate" in query or "throughput" in query:
                val = random.uniform(50, 200) + random.gauss(0, 20)
            else:
                val = random.uniform(10, 100)
            values.append([ts, f"{max(0, val):.4f}"])

        return {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [{
                    "metric": {"__name__": query.split("(")[0] if "(" in query else query},
                    "values": values,
                }],
            },
        }

    @staticmethod
    def _mock_prometheus_instant(query: str) -> dict:
        if "duration" in query or "latency" in query:
            val = random.uniform(120, 280)
        elif "error" in query or "fail" in query:
            val = random.uniform(0.01, 0.04)
        elif "rps" in query or "rate" in query:
            val = random.uniform(80, 180)
        else:
            val = random.uniform(10, 100)

        return {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [{
                    "metric": {},
                    "value": [time.time(), f"{val:.4f}"],
                }],
            },
        }

    # -----------------------------------------------------------------------
    # Pyroscope — continuous profiling / flame graphs
    # -----------------------------------------------------------------------

    async def check_pyroscope(self) -> bool:
        cached = self._get_cached_health("pyroscope")
        if cached is not None:
            return cached
        if not HAS_HTTPX or not self._tcp_port_open(self.config.pyroscope_url, self._TCP_PROBE_TIMEOUT):
            return self._set_cached_health("pyroscope", False)
        try:
            async with self._make_client(self._HEALTH_TIMEOUT) as client:
                resp = await client.get(f"{self.config.pyroscope_url}/ready")
                return self._set_cached_health("pyroscope", resp.status_code == 200)
        except Exception:
            return self._set_cached_health("pyroscope", False)

    async def get_flame_graph(self, query: str = "process_cpu", from_ts: str = "now-1h", until_ts: str = "now") -> dict:
        """Query Pyroscope for flame graph data. Falls back to mock."""
        if not HAS_HTTPX or not self._tcp_port_open(self.config.pyroscope_url, self._TCP_PROBE_TIMEOUT):
            return generate_mock_flamegraph()
        try:
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.get(
                    f"{self.config.pyroscope_url}/pyroscope/render",
                    params={"query": query, "from": from_ts, "until": until_ts, "format": "json"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return generate_mock_flamegraph()

    async def get_pyroscope_apps(self) -> list:
        if not HAS_HTTPX or not self._tcp_port_open(self.config.pyroscope_url, self._TCP_PROBE_TIMEOUT):
            return []
        try:
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.get(f"{self.config.pyroscope_url}/pyroscope/label-values", params={"label": "service_name"})
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return []

    # -----------------------------------------------------------------------
    # Loki — log aggregation
    # -----------------------------------------------------------------------

    async def check_loki(self) -> bool:
        cached = self._get_cached_health("loki")
        if cached is not None:
            return cached
        if not HAS_HTTPX or not self._tcp_port_open(self.config.loki_url, self._TCP_PROBE_TIMEOUT):
            return self._set_cached_health("loki", False)
        try:
            async with self._make_client(self._HEALTH_TIMEOUT) as client:
                resp = await client.get(f"{self.config.loki_url}/ready")
                return self._set_cached_health("loki", resp.status_code == 200)
        except Exception:
            return self._set_cached_health("loki", False)

    async def query_loki(self, query: str = '{job="test-app"}', limit: int = 100) -> dict:
        """Query Loki for logs. Falls back to mock data."""
        if not HAS_HTTPX or not self._tcp_port_open(self.config.loki_url, self._TCP_PROBE_TIMEOUT):
            return generate_mock_logs()
        try:
            now = int(time.time() * 1_000_000_000)
            one_hour_ago = now - 3600 * 1_000_000_000
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.get(
                    f"{self.config.loki_url}/loki/api/v1/query_range",
                    params={
                        "query": query,
                        "start": str(one_hour_ago),
                        "end": str(now),
                        "limit": limit,
                        "direction": "backward",
                    },
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return generate_mock_logs()

    async def get_loki_labels(self) -> list:
        if not HAS_HTTPX or not self._tcp_port_open(self.config.loki_url, self._TCP_PROBE_TIMEOUT):
            return []
        try:
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.get(f"{self.config.loki_url}/loki/api/v1/labels")
                if resp.status_code == 200:
                    return resp.json().get("data", [])
        except Exception:
            pass
        return []

    # -----------------------------------------------------------------------
    # Toxiproxy — chaos / network fault injection
    # -----------------------------------------------------------------------

    async def check_toxiproxy(self) -> bool:
        cached = self._get_cached_health("toxiproxy")
        if cached is not None:
            return cached
        if not HAS_HTTPX or not self._tcp_port_open(self.config.toxiproxy_url, self._TCP_PROBE_TIMEOUT):
            return self._set_cached_health("toxiproxy", False)
        try:
            async with self._make_client(self._HEALTH_TIMEOUT) as client:
                resp = await client.get(f"{self.config.toxiproxy_url}/version")
                return self._set_cached_health("toxiproxy", resp.status_code == 200)
        except Exception:
            return self._set_cached_health("toxiproxy", False)

    async def list_proxies(self) -> dict:
        if not HAS_HTTPX:
            return {}
        try:
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.get(f"{self.config.toxiproxy_url}/proxies")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return {}

    async def create_proxy(self, name: str, listen: str, upstream: str) -> dict:
        if not HAS_HTTPX:
            return {"error": "httpx not installed"}
        try:
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.post(
                    f"{self.config.toxiproxy_url}/proxies",
                    json={"name": name, "listen": listen, "upstream": upstream, "enabled": True},
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def add_toxic(self, proxy_name: str, toxic_type: str, attributes: dict, stream: str = "downstream", toxicity: float = 1.0) -> dict:
        if not HAS_HTTPX:
            return {"error": "httpx not installed"}
        try:
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.post(
                    f"{self.config.toxiproxy_url}/proxies/{proxy_name}/toxics",
                    json={
                        "name": f"{proxy_name}-{toxic_type}",
                        "type": toxic_type,
                        "stream": stream,
                        "toxicity": toxicity,
                        "attributes": attributes,
                    },
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def remove_toxic(self, proxy_name: str, toxic_name: str) -> bool:
        if not HAS_HTTPX:
            return False
        try:
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.delete(f"{self.config.toxiproxy_url}/proxies/{proxy_name}/toxics/{toxic_name}")
                return resp.status_code == 204
        except Exception:
            return False

    async def reset_toxiproxy(self) -> bool:
        if not HAS_HTTPX:
            return False
        try:
            async with self._make_client(self._QUERY_TIMEOUT) as client:
                resp = await client.post(f"{self.config.toxiproxy_url}/reset")
                return resp.status_code == 204
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Mock data generators for demo mode
# ---------------------------------------------------------------------------

def generate_mock_flamegraph() -> dict:
    """Generate realistic mock flame graph data (Pyroscope flamebearer format).

    Simulates a FastAPI app under load with recognizable call stacks.
    """
    # Function names that would appear in a real Python web app
    names = [
        "total",
        "uvicorn.main:serve",
        "starlette.routing:Router.handle",
        "fastapi.routing:APIRouter.handle",
        "app.api.tickets:list_tickets",
        "app.api.tickets:create_ticket",
        "app.api.programs:list_programs",
        "app.api.auth:login",
        "sqlalchemy.engine:execute",
        "sqlalchemy.orm.query:Query.all",
        "psycopg2._psycopg:execute",
        "app.services.ticket_service:get_tickets",
        "app.services.ticket_service:validate_ticket",
        "app.services.program_service:get_programs",
        "json.encoder:JSONEncoder.encode",
        "pydantic.main:BaseModel.model_validate",
        "httpx._client:AsyncClient.request",
        "app.middleware.auth:verify_token",
        "jwt.api_jwt:decode",
        "hashlib:pbkdf2_hmac",
        "app.services.cache:get_cached",
        "redis.client:Redis.get",
        "redis.connection:Connection.send_command",
        "app.utils.pagination:paginate",
        "time.sleep",  # simulating I/O wait
    ]

    # Build a realistic call tree with hotspots
    # Level format: [x_offset, total, self, name_index, ...]
    total = 10000

    levels = [
        # Level 0: root
        [0, total, 0, 0],
        # Level 1: uvicorn
        [0, total, 50, 1],
        # Level 2: starlette
        [0, total - 50, 30, 2],
        # Level 3: fastapi router
        [0, total - 80, 20, 3],
        # Level 4: API endpoints (the main branches)
        [0, 3500, 50, 4,  3500, 1800, 30, 5,  5300, 2800, 40, 6,  8100, 1500, 20, 7],
        # Level 5: service layer + auth
        [0, 2200, 80, 11,  2200, 1200, 40, 12,  3500, 1700, 60, 13,  5300, 2500, 70, 14,
         8100, 800, 30, 17,  8900, 600, 20, 18],
        # Level 6: DB / cache / serialization (the hotspots!)
        [0, 1800, 100, 8,  1800, 400, 200, 20,  2200, 800, 300, 15,
         3500, 1500, 80, 8,  5300, 1800, 120, 9,  7100, 600, 400, 14,
         8100, 500, 200, 19,  8600, 300, 300, 25],
        # Level 7: low-level DB calls (the real bottleneck)
        [0, 1600, 1200, 10,  1600, 200, 200, 23,
         3500, 1300, 1000, 10,  4800, 200, 200, 23,
         5300, 1600, 1400, 10,  6900, 200, 200, 24,
         8100, 300, 300, 21],
        # Level 8: psycopg2 execute (deepest DB call)
        [0, 400, 400, 10,  3500, 300, 300, 10,  5300, 200, 200, 10],
    ]

    return {
        "flamebearer": {
            "names": names,
            "levels": levels,
            "numTicks": total,
            "maxSelf": 1400,
        },
        "metadata": {
            "format": "single",
            "spyName": "pyspy",
            "sampleRate": 100,
            "units": "samples",
            "name": "process_cpu{service_name=\"fastapi-app\"}",
        },
        "timeline": {
            "startTime": int(time.time()) - 3600,
            "samples": [random.randint(80, 150) for _ in range(60)],
            "durationDelta": 60,
        },
    }


def generate_mock_logs() -> dict:
    """Generate realistic mock log entries that would come from Loki."""
    now = time.time()
    levels = ["info", "info", "info", "info", "warn", "error", "debug"]
    endpoints = ["/api/v1/programs", "/api/v1/tickets", "/api/v1/login", "/api/v1/users/me"]
    status_codes = [200, 200, 200, 200, 200, 201, 400, 401, 500, 503]

    log_templates = {
        "info": [
            'method=GET path={ep} status=200 duration={dur}ms ip=192.168.1.{ip}',
            'method=POST path={ep} status=201 duration={dur}ms ip=10.0.0.{ip}',
            'User login successful user_id={uid} ip=192.168.1.{ip}',
            'Database query executed query="SELECT * FROM tickets WHERE ..." duration={dur}ms rows={rows}',
            'Cache hit key="tickets:page:{page}" ttl=300s',
            'Background job completed job=cleanup_expired_sessions duration={dur}ms',
            'Health check passed service=api uptime=43200s',
        ],
        "warn": [
            'Slow query detected query="SELECT * FROM programs JOIN ..." duration={dur}ms threshold=500ms',
            'Connection pool nearing capacity active=18/20 waiting=3',
            'Rate limit approaching client=192.168.1.{ip} requests=95/100 window=60s',
            'Retry attempt 2/3 for external API call url=https://payment.example.com/verify',
            'Cache miss rate elevated miss_rate=0.35 threshold=0.20 key_pattern="tickets:*"',
            'Memory usage high rss=1.8GB limit=2.0GB gc_count=47',
        ],
        "error": [
            'Database connection failed host=db.internal:5432 error="connection refused" retry_in=5s',
            'Request failed method=POST path=/api/v1/tickets status=500 error="IntegrityError: duplicate key"',
            'Redis timeout command=GET key="session:abc123" timeout=3000ms',
            'Authentication failed user="admin" reason="invalid_token" ip=203.0.113.{ip}',
            'Unhandled exception in /api/v1/programs: TypeError: NoneType has no attribute "id"',
            'Circuit breaker OPEN for service=payment-gateway failures=5/5 cooldown=30s',
            'SSL certificate verification failed host=api.external.com error="certificate has expired"',
        ],
        "debug": [
            'SQL query: SELECT t.id, t.title FROM tickets t WHERE t.status = "open" LIMIT 20',
            'Request headers: Authorization=Bearer eyJ...truncated Content-Type=application/json',
            'Response serialization completed model=TicketListResponse items={rows} duration={dur}ms',
        ],
    }

    entries = []
    for i in range(80):
        ts_offset = random.uniform(0, 3600)
        ts = now - ts_offset
        level = random.choice(levels)
        templates = log_templates.get(level, log_templates["info"])
        template = random.choice(templates)

        msg = template.format(
            ep=random.choice(endpoints),
            dur=random.randint(1, 2000) if level == "error" else random.randint(5, 500),
            ip=random.randint(1, 254),
            uid=random.randint(1000, 9999),
            rows=random.randint(0, 500),
            page=random.randint(1, 20),
        )

        entries.append({
            "timestamp": f"{int(ts * 1_000_000_000)}",
            "level": level,
            "message": msg,
            "service": "fastapi-app",
            "env": random.choice(["local", "sit", "uat"]),
        })

    entries.sort(key=lambda e: e["timestamp"], reverse=True)

    return {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {"job": "fastapi-app", "env": "sit", "level": lv},
                    "values": [
                        [e["timestamp"], e["message"]]
                        for e in entries if e["level"] == lv
                    ],
                }
                for lv in ["error", "warn", "info", "debug"]
                if any(e["level"] == lv for e in entries)
            ],
        },
    }


def generate_mock_perf_report() -> dict:
    """Generate a complete mock performance test report for demo purposes.

    This simulates what a real Locust/k6 test run would produce,
    with realistic endpoint-level metrics.
    """
    endpoints = [
        {"method": "POST", "name": "/api/v1/login", "weight": 10},
        {"method": "GET", "name": "/api/v1/programs", "weight": 30},
        {"method": "POST", "name": "/api/v1/programs", "weight": 10},
        {"method": "GET", "name": "/api/v1/tickets", "weight": 25},
        {"method": "POST", "name": "/api/v1/tickets", "weight": 15},
        {"method": "GET", "name": "/api/v1/users/me", "weight": 10},
    ]

    total_requests = 0
    total_failures = 0
    endpoint_results = []
    duration_s = random.randint(180, 600)
    users = random.choice([50, 100, 200, 500])

    for ep in endpoints:
        count = int(users * duration_s / 10 * ep["weight"] / 100)
        failures = int(count * random.uniform(0.005, 0.04))
        avg_rt = random.uniform(50, 400)
        min_rt = avg_rt * random.uniform(0.2, 0.5)
        max_rt = avg_rt * random.uniform(2, 8)
        p50 = avg_rt * random.uniform(0.8, 1.0)
        p90 = avg_rt * random.uniform(1.3, 2.0)
        p95 = avg_rt * random.uniform(1.5, 2.5)
        p99 = avg_rt * random.uniform(2.0, 4.0)

        total_requests += count
        total_failures += failures

        endpoint_results.append({
            "method": ep["method"],
            "endpoint": ep["name"],
            "requests": count,
            "failures": failures,
            "avg_response_time": round(avg_rt, 1),
            "min_response_time": round(min_rt, 1),
            "max_response_time": round(max_rt, 1),
            "p50": round(p50, 1),
            "p90": round(p90, 1),
            "p95": round(p95, 1),
            "p99": round(p99, 1),
            "rps": round(count / duration_s, 1),
            "error_rate": round(failures / count * 100, 2) if count > 0 else 0,
        })

    # Generate time-series data for charts (1-second intervals, sampled every 5s)
    points = duration_s // 5
    rps_series = []
    rt_series = []
    error_series = []
    users_series = []

    for i in range(points):
        t = i * 5
        # Simulate ramp-up then steady state
        ramp_factor = min(1.0, t / (duration_s * 0.15))
        current_users = int(users * ramp_factor)

        rps_val = (total_requests / duration_s) * ramp_factor + random.gauss(0, 5)
        rt_val = 150 + random.gauss(0, 30) + (20 if ramp_factor > 0.8 else 0)
        err_val = random.uniform(0, 3) * ramp_factor

        rps_series.append({"time": t, "value": round(max(0, rps_val), 1)})
        rt_series.append({"time": t, "value": round(max(10, rt_val), 1)})
        error_series.append({"time": t, "value": round(max(0, err_val), 2)})
        users_series.append({"time": t, "value": current_users})

    overall_avg_rt = sum(e["avg_response_time"] * e["requests"] for e in endpoint_results) / total_requests if total_requests else 0
    error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    return {
        "summary": {
            "total_requests": total_requests,
            "total_failures": total_failures,
            "error_rate": round(error_rate, 2),
            "avg_response_time": round(overall_avg_rt, 1),
            "rps": round(total_requests / duration_s, 1),
            "duration_s": duration_s,
            "virtual_users": users,
            "start_time": (datetime.utcnow() - timedelta(seconds=duration_s)).isoformat(),
            "end_time": datetime.utcnow().isoformat(),
        },
        "endpoints": endpoint_results,
        "timeseries": {
            "rps": rps_series,
            "response_time": rt_series,
            "error_rate": error_series,
            "users": users_series,
        },
    }
