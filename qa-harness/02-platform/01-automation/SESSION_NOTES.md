# Session Notes & Decisions

Things future-Claude or future-you should know about why the project looks
the way it does. Append-only style: don't rewrite history, just add new
entries on top.

---

## 2026-05-27 — Migrate observability to Windows native; retire WSL2 Docker

### What changed

1. **Prometheus moved from WSL Docker to Windows native.** Installed at
   `D:\prometheus\prometheus-2.51.0.windows-amd64\` (same version as the
   previous `prom/prometheus:v2.51.0` image). Data dir `D:\prometheus\data\`.
   Started via `infra\start-prometheus.bat`.
2. **Loki moved from WSL Docker to Windows native.** Installed at
   `D:\loki\loki-windows-amd64.exe` (Loki 2.9.6, matches the previous
   `grafana/loki:2.9.6` image). Data dir `D:\loki\data\`. Config at
   `infra/loki/loki-config.yaml`. Started via `infra\start-loki.bat`.
3. **Locust scrape target reverted** from `host.docker.internal:9646` back
   to `localhost:9646` in `prometheus.yml` — no WSL indirection needed now.
4. **Deleted** `infra/docker-compose.yml`, `infra/refresh-wsl-host-ip.sh`,
   `infra/.env` (the WINDOWS_HOST_IP file). WSL2 is no longer required.

### Why

Goal stated by user 2026-05-27: "all services on Windows or Mac, no Ubuntu".
The observability stack was the only piece still living in WSL Docker. With
both Prometheus and Loki shipping Windows binaries from the same release
artifacts that produced the Docker images, the migration was 1-day mechanical
work and removed an entire category of operational pain — no more iptables
quirks, no more host-IP refresh after WSL restart, no more `WINDOWS_HOST_IP`
juggling. Single OS = single mental model for the whole team.

### Things to redo if environment is rebuilt

- **If Prometheus install is wiped**: re-download
  `https://github.com/prometheus/prometheus/releases/download/v2.51.0/prometheus-2.51.0.windows-amd64.zip`,
  extract to `D:\prometheus\`, run `infra\start-prometheus.bat`.
- **If Loki install is wiped**: re-download
  `https://github.com/grafana/loki/releases/download/v2.9.6/loki-windows-amd64.exe.zip`,
  extract to `D:\loki\`, run `infra\start-loki.bat`.

### Things NOT to try again

- Putting Prometheus or Loki back in Docker. The whole point was to drop
  the WSL2 + Docker dependency. If a future need for containerization
  arises (e.g. a Linux server deployment), do it on the SERVER, not on
  dev machines.

---

## 2026-05-16 — Grafana moved out of Docker; SkyWalking removed; iptables → legacy

### What changed

1. **SkyWalking fully removed.** OAP + UI containers stopped/deleted,
   backend `metrics_client.py` SkyWalking section deleted, `/api/perf/services`
   no longer returns a `skywalking` field, frontend Performance Test page
   no longer has a SkyWalking tab, all docs cleaned.
2. **`fastapi-app` Prometheus scrape job deleted** from
   `infra/prometheus/prometheus.yml`. The FastAPI backend never exposed
   `/metrics`, so the target was permanently DOWN.
3. **Locust scrape target switched** from hard-coded `172.19.80.1:9646` to
   `host.docker.internal:9646`. Compose injects this via `extra_hosts:
   host.docker.internal:${WINDOWS_HOST_IP:-172.19.80.1}` — `.env` holds the
   actual IP, refreshable via `infra/refresh-wsl-host-ip.sh`.
4. **iptables backend switched from `nft` to `legacy`** on the WSL2 host:
   ```bash
   sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
   sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
   sudo systemctl restart docker
   ```
5. **Grafana moved from Docker container to Windows-native install** at
   `D:\grafana\grafana-v10.4.1`. Started via `infra\start-grafana.bat`.
   Config: `infra/grafana/grafana.windows.ini`. Datasources point at
   `http://localhost:9090` and `http://localhost:3100` (Docker-published
   ports reachable from Windows).
6. **`docker-compose.yml` no longer defines Grafana** or `grafana-data`
   volume.

### Why

**The root issue:** on this WSL2 Ubuntu 24.04 + native Docker Engine setup,
container-to-container TCP forwarding is broken. ICMP/DNS work between
containers, but TCP times out — and the hairpin path
(container → Windows mapped port → another container) is broken too. This
is most likely an iptables/nft rule-write issue in Docker's bridge driver.

**What didn't fix it:**
- `docker compose down && up -d` (network fully rebuilt)
- `docker compose up -d --force-recreate`
- Switching to iptables-legacy + `systemctl restart docker`
- Grafana with `network_mode: host` — works for the proxy query but WSL2
  does not forward host-network bound ports back to Windows, so the
  browser cannot reach it on `localhost:3000`

**What did fix the Grafana symptom:** running Grafana natively on Windows.
From Windows it reaches Prometheus and Loki on `localhost:9090` / `:3100`
via the Docker port mappings, which work fine. No container network
involvement.

**SkyWalking removal motivation:** SkyWalking is APM — it needs an agent
on the *system under test* to capture traces. Our SUT is a remote service
(`anticket.lengliwh.com`) we can't instrument, and Locust is just the load
generator (instrumenting it would be tracing the wrong side). All our
useful metrics (RPS, p95, error rate, active users) come from Locust's
prometheus_client exporter. SkyWalking was empty space — the dashboard tab
literally only said "connected" with no charts.

### Things to redo if environment is rebuilt

- **If WSL is reinstalled**: redo iptables-legacy switch (commands above)
  before bringing up Docker.
- **If Docker is reinstalled inside WSL**: same — iptables backend
  resets to system default.
- **If Grafana install is wiped**: re-download
  `https://dl.grafana.com/oss/release/grafana-10.4.1.windows-amd64.zip`,
  extract to `D:\grafana\`, double-click `infra\start-grafana.bat`. Provisioning
  picks up datasources and the locust-perf dashboard automatically.
- **If WSL is restarted (gateway IP may have changed)**: run
  `wsl bash -c "cd /mnt/d/qa-harness/automation && bash infra/refresh-wsl-host-ip.sh"`.

### Things NOT to try again (already proven dead-end)

- Putting Grafana back in `docker-compose.yml` and pointing at
  `http://prometheus:9090`.
- Using `extra_hosts: host.docker.internal:host-gateway` to reach Windows
  from a container (gives docker bridge IP `172.17.0.1`, not Windows).
- Hardcoding `172.19.80.1` anywhere — this is the current WSL2 gateway IP,
  it changes on WSL restart. Always go via `host.docker.internal` (injected
  by compose) or `${WINDOWS_HOST_IP}` (read from `.env`).
