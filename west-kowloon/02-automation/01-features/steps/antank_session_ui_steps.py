"""
Step definitions for antank_session_ui.feature.

Converts manual test cases SIT-TC-WEB-AUTH-013 (logout / back-button
protection), 027 (mobile-viewport layout) and 028 (multilingual labels)
into pure-UI Playwright tests.
"""

from behave import given, when, then

from test_automation.config import get_settings, get_user
from test_automation.web import WebsiteLoginPage


# --- TC013  logout clears authenticated access -------------------------------

@given("a registered user is logged in")
def step_logged_in(context):
    """TC013 manual step 1 — log a registered user in."""
    settings = get_settings()
    user = get_user("website_user", settings.env)
    context.login_page = WebsiteLoginPage(context.page, str(settings.antank_url))
    context.login_page.open()
    context.login_page.login(user.username, user.password)
    assert context.login_page.is_logged_in(), "Expected the user to be logged in"


@when("the user logs out and reopens a registered-only page")
def step_logout_and_revisit(context):
    """TC013 manual steps 3-4 — log out, then reopen the registered-only
    personal centre (#/my/profile)."""
    base = str(get_settings().antank_url).rstrip("/")
    context.logout_ok = context.login_page.logout()
    context.page.goto(f"{base}/websitehtml/index.html#/my/profile", timeout=60000)
    context.page.wait_for_timeout(3000)


@then("the registered-only page is not accessible")
def step_assert_registered_blocked(context):
    """TC013 expected result — after logout the personal centre is not shown
    (the route redirects away from #/my/profile)."""
    url = context.page.url
    assert "#/my/profile" not in url, \
        f"Expected the personal centre to be blocked after logout (url={url})"
    print(f"  [TC013] logout cleared access (logout_ok={context.logout_ok}, url={url})")


# --- TC027  mobile-viewport authentication layout ----------------------------

@given("the browser uses a mobile viewport")
def step_mobile_viewport(context):
    """TC027 — switch the page to a typical mobile viewport."""
    context.page.set_viewport_size({"width": 390, "height": 844})


@when("I open the login and registration screens")
def step_open_auth_mobile(context):
    """TC027 — open login + registration on the mobile viewport and measure
    field visibility and horizontal overflow."""
    base = str(get_settings().antank_url).rstrip("/")
    context.mobile_results = {}
    for name, route, field in [("login", "#/login", "#login-email"),
                               ("register", "#/register",
                                'input[placeholder="Email"]')]:
        context.page.goto(f"{base}/websitehtml/index.html{route}", timeout=60000)
        context.page.wait_for_load_state("networkidle", timeout=30000)
        context.page.wait_for_timeout(1500)
        context.mobile_results[name] = {
            "field_visible": context.page.locator(field).first.is_visible(),
            "submit_visible": context.page.locator(".submit-btn").first.is_visible(),
            "overflow_px": context.page.evaluate(
                "() => document.documentElement.scrollWidth"
                " - document.documentElement.clientWidth"),
        }


@then("the auth form fields and submit controls are visible and usable")
def step_assert_mobile_usable(context):
    """TC027 expected result — no critical clipping; fields/controls usable."""
    for name, r in context.mobile_results.items():
        assert r["field_visible"], f"{name}: auth field not visible on mobile viewport"
        assert r["submit_visible"], f"{name}: submit control not visible on mobile viewport"
        assert r["overflow_px"] <= 6, \
            f"{name}: {r['overflow_px']}px horizontal overflow on mobile viewport"
    print(f"  [TC027] mobile viewport usable -> {context.mobile_results}")


# --- TC028  multilingual auth labels -----------------------------------------

@given("the Website login page is open for a language check")
def step_open_login_i18n(context):
    """TC028 — open the login page so its language can be switched."""
    base = str(get_settings().antank_url).rstrip("/")
    context.page.goto(f"{base}/websitehtml/index.html#/login", timeout=60000)
    context.page.wait_for_load_state("networkidle", timeout=30000)
    context.page.wait_for_timeout(1500)


@when("I switch the interface language")
def step_switch_language(context):
    """TC028 — open the language switcher and pick a non-current language."""
    context.label_before = context.page.locator(".submit-btn").first.inner_text().strip()
    trigger = context.page.locator(".auth-lang__trigger")
    assert trigger.count(), "Expected a language switcher on the auth page"
    trigger.first.click()
    context.page.wait_for_timeout(800)
    opts = context.page.locator("[role=option], .auth-lang__option, li")
    clicked = False
    for i in range(opts.count()):
        opt = opts.nth(i)
        text = (opt.inner_text() or "").strip()
        if opt.is_visible() and text and text.upper() != "EN":
            opt.click()
            clicked = True
            break
    assert clicked, "Expected a non-English language option in the switcher"
    context.page.wait_for_timeout(1500)
    context.label_after = context.page.locator(".submit-btn").first.inner_text().strip()


@then("the auth page labels change to the selected language")
def step_assert_language_changed(context):
    """TC028 expected result — auth labels follow the selected language."""
    assert context.label_before != context.label_after, (
        "Expected the submit-button label to change with the language; "
        f"it stayed {context.label_before!r}")
    print(f"  [TC028] label changed: {context.label_before!r} -> {context.label_after!r}")
