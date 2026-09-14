from fastapi import FastAPI
from fastapi.testclient import TestClient

from frontend_hosting import install_frontend_routes


def test_vite_dist_is_served_with_spa_fallback(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>dashboard</html>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")

    app = FastAPI()

    @app.get("/api/example")
    def api_example():
        return {"ok": True}

    install_frontend_routes(app, dist)
    client = TestClient(app)

    assert client.get("/").status_code == 200
    assert "dashboard" in client.get("/package-health").text
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/api/example").json() == {"ok": True}
    assert client.get("/api/missing").status_code == 404
