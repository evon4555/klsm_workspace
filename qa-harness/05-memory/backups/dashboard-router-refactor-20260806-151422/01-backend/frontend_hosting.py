"""Serve the production Vite bundle from the FastAPI process."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def install_frontend_routes(app: FastAPI, dist_dir: Path) -> None:
    """Install static assets and SPA fallback after all API routes exist."""
    dist_dir = dist_dir.resolve()
    assets_dir = dist_dir / "assets"
    app.mount(
        "/assets",
        StaticFiles(directory=str(assets_dir), check_dir=False),
        name="frontend-assets",
    )

    @app.get("/{frontend_path:path}", include_in_schema=False)
    def serve_frontend(frontend_path: str):
        if frontend_path.startswith(("api/", "ws/")):
            raise HTTPException(status_code=404, detail="route not found")

        candidate = (dist_dir / frontend_path).resolve()
        try:
            candidate.relative_to(dist_dir)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="route not found") from exc

        if frontend_path and candidate.is_file():
            return FileResponse(candidate)

        index_file = dist_dir / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        raise HTTPException(
            status_code=404,
            detail="frontend bundle not built; run npm run build in 02-frontend",
        )
