from main import app


def test_domain_routes_are_registered_once_from_router_modules():
    http_routes = [route for route in app.routes if hasattr(route, "methods")]
    dashboard_routes = [
        route
        for route in http_routes
        if route.path not in {
            "/openapi.json",
            "/docs",
            "/docs/oauth2-redirect",
            "/redoc",
            "/{frontend_path:path}",
        }
    ]

    route_keys = [
        (method, route.path)
        for route in dashboard_routes
        for method in route.methods
    ]
    assert len(dashboard_routes) == 54
    assert len(route_keys) == len(set(route_keys))

    expected_modules = {
        "/api/perf/status": "routers.performance",
        "/api/observability/status": "routers.observability",
        "/api/api-monitor/endpoints": "routers.api_monitor",
        "/api/zentao/dashboard": "routers.zentao",
        "/api/quality-system/packages": "routers.package_health",
    }
    by_path = {route.path: route for route in dashboard_routes}
    for path, module_name in expected_modules.items():
        assert by_path[path].endpoint.__module__ == module_name
