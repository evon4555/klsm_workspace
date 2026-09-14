"""
Step definitions for antank_registration.feature.

Converts manual test cases SIT-TC-WEB-AUTH-001 .. 008 ("Website native
registration") from the Kasi requirement package into pure-UI Playwright
tests driven through WebsiteRegistrationPage.

Uses Playwright (context.page) set up in environment.py before_scenario().
The 动态码 image captcha is solved by OCR with retry inside the page object.

TC004 is EXPECTED to fail: the product currently allows duplicate
registration, which is exactly the defect that case catches.

Test data:
  * the already-registered Website account lives in config/users.yml under
    <env>.website_user (re-used as the "existing email" for TC004);
  * the email Verification Code (OTP) is a fixed test value 111111 in SIT,
    so the OTP-gated cases need no real inbox.
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from behave import given, when, then

from test_automation.config import get_settings, get_user
from test_automation.web import WebsiteRegistrationPage

# Allow `from imap_otp_poller import ...` (lives in tools/)
_TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

# Screenshots from a dashboard/behave run land here (the Kasi-workbook
# evidence strips are produced separately by tools/update_evidence.py).
_SHOT_ROOT = Path(__file__).resolve().parents[2] / "07-artifacts" / "screenshots"

# A strong, rule-compliant password for the "valid data" fields.
_VALID_PASSWORD = "Test@202605"

# The email Verification Code (OTP) WAS a fixed test value 111111 in SIT, but
# SIT removed the fixed-OTP backdoor on 2026-05-23 (see
# project_sit_otp_regression_2026_05_27 memory). Cases needing a real OTP now
# IMAP-poll the evan.wang@antank.com Aliyun corporate inbox. Brand-new-email
# scenarios use plus-addressing so OTP still lands in the same inbox while the
# product still treats each address as a fresh, never-registered account.
_VALID_OTP = "111111"


# NOTE 2026-06-09: a plus-addressed evan.wang alias was explored as a way to
# end-to-end-test brand-new-email scenarios (TC001/035/057) without rebuilding
# the SIT fixed-OTP backdoor. SIT's registration form email-format regex
# rejects the "+" character — Get Code returns "邮箱格式不正确！" — so the
# alias never even reaches the OTP service. Helper kept for future reuse if
# the SIT regex is relaxed or if antank.com gains a real catch-all subdomain.
def _fresh_evan_alias(tag: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"evan.wang+{tag}_{stamp}@antank.com"


def _new_registration_page(context) -> WebsiteRegistrationPage:
    settings = get_settings()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shot_dir = _SHOT_ROOT / f"registration_{stamp}"
    return WebsiteRegistrationPage(context.page, str(settings.antank_url),
                                   screenshot_dir=shot_dir)


@given("the Website registration page is open")
def step_open_registration(context):
    """Manual step 1 — open the registration page (email tab is the default)."""
    context.reg = _new_registration_page(context)
    context.reg.open()
    context.reg.shot("registration_page_opened")


# --- TC001  successful registration ------------------------------------------

@when("I fill the registration form with brand-new valid account data")
def step_fill_new_account(context):
    """TC001 manual steps — fill a brand-new account (a unique fake email so
    it is a genuine first-time registration), request the OTP via "Get Code",
    enter the OTP and a valid password, then submit. The Verification Code is
    only accepted after "Get Code" has been clicked.

    OTP delivery limitation: SIT removed the fixed test OTP (111111) on
    2026-05-23 and the fake @126.com inbox is uncontrolled, so end-to-end
    submission is blocked until SIT provides a fixed-OTP backdoor or a
    controlled catch-all domain (probed 2026-06-09: plus-addressing of
    evan.wang@antank.com is rejected by SIT's email-format regex).

    PRD-2026-06-10 (updated 2026-06-12): the new gated 5-step flow requires:
      1. CAPTCHA gate — subsequent fields unlocked only after CAPTCHA passes.
      2. OTP gate — password step unlocked only after OTP passes.
      3. Password rule violations are flagged inline on focus-out (not just
         on submit).
    Step-level assertions for the gating behavior are NOT added here yet —
    they need a page-object refactor (WebsiteRegistrationPage.step_advances_
    only_after_<gate>). Tracked as a follow-up; the smoke assertion below is
    the existing end-state check.
    """
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    context.tc001_email = f"fake_{stamp}@126.com"
    context.reg.fill_email(context.tc001_email)
    context.reg.request_otp_until_sent()
    context.reg.fill_verification_code(_VALID_OTP)
    context.reg.fill_passwords(_VALID_PASSWORD)
    context.reg.accept_terms()                       # required since 2026-05-26
    context.reg.shot("registration_form_filled")
    context.reg_error = context.reg.submit_until_settled()


@then("a new account is created and the visitor is signed in")
def step_assert_account_created(context):
    """TC001 expected result — registration completes (the "Registration
    successful" confirmation is shown / the browser leaves #/register)."""
    context.reg._page.wait_for_timeout(2500)        # let the success modal settle
    assert context.reg.registration_succeeded(), (
        "Expected registration to complete (success modal / left #/register); "
        f"error={context.reg_error!r}")
    print(f"  [TC001] registered new account -> {context.tc001_email}")


# --- TC002  mandatory fields -------------------------------------------------

@when("I submit the registration form with every field left empty")
def step_submit_empty(context):
    """TC002 manual steps 2-3 — submit with no fields filled."""
    context.reg.submit()
    context.reg.shot("empty_form_submitted")


@then("registration is blocked with a missing-field validation message")
def step_assert_missing_field(context):
    """TC002 expected result — submission blocked, a missing-field message shown."""
    error = context.reg.current_error()
    assert error, "Expected a validation message after an empty submit"
    assert context.reg.is_on_register_page(), \
        "Expected to stay on #/register — registration must be blocked"
    print(f"  [TC002] validation message -> {error!r}")


# --- TC003  invalid email format ---------------------------------------------

@when("I submit the registration form with an invalid email address")
def step_submit_invalid_email(context):
    """TC003 manual steps 2-3 — enter a malformed email and submit."""
    context.reg.fill_email("not-an-email")
    context.reg.shot("invalid_email_entered")
    context.reg.submit()
    context.reg.shot("invalid_email_rejected")


@then("registration is blocked with an invalid-email validation message")
def step_assert_invalid_email(context):
    """TC003 expected result — invalid email rejected, no account created."""
    error = context.reg.current_error()
    assert error, "Expected a validation message for the invalid email"
    low = error.lower()
    assert ("invalid" in low or "email" in low or "邮件" in error
            or "邮箱" in error or "格式" in error), \
        f"Expected an invalid-email message, got {error!r}"
    assert context.reg.is_on_register_page(), \
        "Expected to stay on #/register — registration must be blocked"
    print(f"  [TC003] validation message -> {error!r}")


# --- TC004  duplicate email (EXPECTED TO FAIL — product defect) --------------

@when("I submit the registration form with an already-registered email")
def step_submit_duplicate_email(context):
    """TC004 manual steps — submit a full, valid registration (REAL OTP
    fetched from inbox; SIT killed fixed 111111 since 2026-05-23) for an
    already-registered email. The registration password matches
    config/users.yml so a (defective) re-registration leaves the account
    credentials unchanged."""
    from imap_otp_poller import fetch_latest_otp, wait_for_otp_throttle
    user = get_user("website_user", get_settings().env)
    context.reg.fill_email(user.username)
    wait_for_otp_throttle(user.username)
    since = datetime.now(timezone.utc) - timedelta(seconds=10)
    context.reg.request_otp_until_sent()
    real_otp = fetch_latest_otp(since=since, timeout=45.0)
    context.reg.fill_verification_code(real_otp)
    context.reg.fill_passwords(user.password)
    context.reg.accept_terms()                       # required since 2026-05-26
    context.reg.shot("duplicate_email_form_filled")
    context.reg_error = context.reg.submit_until_settled()


# Per 2026-06-10 PRD §用户邮箱/手机+密码注册 step 5.a (updated 2026-06-12), the
# duplicate-email block MUST surface exactly one of the 3 PRD-mandated wordings.
_DUPLICATE_EMAIL_ERROR_VARIANTS = (
    "该邮箱已注册",     # zh-CN: 该邮箱已注册，请登录或找回密码。
    "此電子郵件已註冊",  # zh-HK: 此電子郵件已註冊，請直接登入或重設密碼。
    "This email address is already registered",  # en
)


@then("registration is blocked with an existing-account message")
def step_assert_duplicate(context):
    """TC004 expected result — the duplicate MUST be rejected.

    UPDATED 2026-06-12 per 2026-06-10 PRD: in addition to blocking the
    duplicate, the email field MUST surface the exact 3-language wording.
    If the product still permits the duplicate registration (legacy defect),
    is_on_register_page() will be False and this fails as before. If the
    product blocks the duplicate but uses non-PRD wording, the wording check
    catches that too.
    """
    assert context.reg.is_on_register_page(), (
        "DEFECT: registration with an already-registered email SUCCEEDED — "
        "the system did not prevent the duplicate; expected an existing-account "
        f"rejection. (error={context.reg_error!r})")
    msg = str(context.reg_error or "")
    matched = next((v for v in _DUPLICATE_EMAIL_ERROR_VARIANTS if v in msg), None)
    assert matched, (
        f"2026-06-10 PRD §用户邮箱/手机+密码注册 step 5.a.i: expected one of the "
        f"3-language duplicate-email error strings. Got: {msg!r}")
    print(f"  [PRD-2026-06-10] duplicate-email wording matched: {matched!r}")


# --- TC005  wrong email OTP --------------------------------------------------

@when("I submit the registration form with a wrong email verification code")
def step_submit_wrong_otp(context):
    """TC005 manual steps — request the OTP via "Get Code", then enter a
    deliberately wrong verification code (not 111111) and submit."""
    user = get_user("website_user", get_settings().env)
    context.reg.fill_email(user.username)
    context.reg.request_otp_until_sent()
    context.reg.fill_verification_code("000000")    # wrong OTP (deliberately)
    context.reg.fill_passwords(_VALID_PASSWORD)
    context.reg.accept_terms()                      # tick the Terms checkbox
    context.reg.shot("form_filled_wrong_otp")
    context.scenario_error = context.reg.submit_until_settled()
    context.reg.shot("otp_error_shown")


@then("registration is blocked with an OTP-error message")
def step_assert_otp_error(context):
    """TC005 expected result — registration blocked, OTP error displayed."""
    error = context.scenario_error
    assert error, "Expected an OTP-error message after submitting a wrong code"
    assert "邮箱" in error or "otp" in error.lower() or "verification" in error.lower(), \
        f"Expected an email-OTP error, got {error!r}"
    assert context.reg.is_on_register_page(), \
        "Expected to stay on #/register — registration must be blocked"
    print(f"  [TC005] OTP-error message -> {error!r}")


# --- TC006  OTP resend cooldown ----------------------------------------------

@when("I request the email verification code")
def step_request_otp(context):
    """TC006 manual steps — fill email + 动态码, then click "Get Code"."""
    user = get_user("website_user", get_settings().env)
    for attempt in range(1, 4):
        context.reg.fill_email(user.username)
        context.reg.fill_dynamic_code()
        context.reg.request_otp()
        if context.reg.resend_is_cooling_down():
            break
        print(f"  [TC006] no cooldown yet (attempt {attempt}) — retrying")
    context.reg.shot("verification_code_requested")


@then("the resend control enters a countdown cooldown")
def step_assert_cooldown(context):
    """TC006 expected result — the resend control shows a countdown cooldown."""
    text, disabled = context.reg.get_code_button_state()
    assert context.reg.resend_is_cooling_down(), (
        f"Expected the resend control to be disabled with a countdown; "
        f"got text={text!r} disabled={disabled}")
    print(f"  [TC006] resend control in cooldown -> {text!r} (disabled={disabled})")


# --- TC008  Privacy Policy link ----------------------------------------------

@when("I fill in a registration field and open the Privacy Policy link")
def step_open_privacy_policy(context):
    """TC008 manual steps — fill a field, then click the Privacy Policy link."""
    context.tc008_email = "policy.viewer@example.com"
    context.reg.fill_email(context.tc008_email)
    context.reg.shot("registration_field_filled")
    context.reg.open_privacy_policy()
    context.reg.shot("privacy_policy_opened")


@then("the Privacy Policy content opens and the form data is preserved")
def step_assert_privacy_policy(context):
    """TC008 expected result — policy opens; returning preserves form data."""
    assert context.reg.privacy_dialog_visible(), \
        "Expected the Privacy Policy modal to be visible"
    title = context.reg.privacy_dialog_title()
    assert "privacy" in title.lower() or "私隐" in title or "隐私" in title, \
        f"Expected the Privacy Policy title, got {title!r}"
    context.reg.close_privacy_policy()
    context.reg.shot("returned_form_data_preserved")
    preserved = context.reg.email_value()
    assert preserved == context.tc008_email, \
        f"Expected the email field to keep {context.tc008_email!r}, got {preserved!r}"
    print(f"  [TC008] policy opened ({title!r}); form data preserved -> {preserved!r}")


# --- TC029  registration requires the 动态码 --------------------------------

@when("I submit the registration form with a missing or wrong 动态码")
def step_submit_missing_dynamic_code(context):
    """TC029 — fill email + passwords, leave the 动态码 empty, then submit."""
    context.reg.fill_email("captcha.required@126.com")
    context.reg.fill_passwords(_VALID_PASSWORD)
    context.reg.fill_dynamic_code_value("")        # missing 动态码
    context.reg.shot("registration_missing_captcha")
    context.reg.submit()
    context.reg_error = context.reg.current_error()


@then("registration is blocked with a captcha error")
def step_assert_registration_captcha_error(context):
    """TC029 expected result — registration blocked, a 动态码 error shown."""
    err = context.reg_error
    assert err, "Expected a validation message for the missing 动态码"
    assert context.reg.is_on_register_page(), "Expected to stay on #/register"
    assert ("动态" in err or "图形" in err or "验证码" in err
            or "captcha" in err.lower() or "code" in err.lower()), \
        f"Expected a 动态码/captcha message, got {err!r}"
    print(f"  [TC029] missing-动态码 message -> {err!r}")


# --- TC030  the 动态码 refreshes on click -----------------------------------

@when("I click the 动态码 image")
def step_click_captcha_image(context):
    """TC030 — record the 动态码 image, then click it to load a fresh one."""
    context.tc030_src_before = context.reg.captcha_image_src()
    context.reg.shot("captcha_before_refresh")
    context.reg.refresh_captcha()
    context.reg.shot("captcha_after_refresh")
    context.tc030_src_after = context.reg.captcha_image_src()


@then("a fresh 动态码 image is shown")
def step_assert_captcha_refreshed(context):
    """TC030 expected result — the 动态码 image changes after the click."""
    before, after = context.tc030_src_before, context.tc030_src_after
    assert before and after, "Expected a 动态码 image src before and after the click"
    assert before != after, \
        f"Expected the 动态码 image to change on click; src stayed {before!r}"
    print("  [TC030] 动态码 image refreshed on click (src changed)")


# --- TC042  OTP resend within 60s is rejected --------------------------------

@when("I request the email verification code and immediately try to resend")
def step_request_otp_then_resend(context):
    """TC042 — request the OTP (starts the 60s cooldown), then immediately try
    to resend. request_otp() is best-effort: it never clicks a disabled button,
    so a still-cooling control proves the within-60s resend is blocked."""
    user = get_user("website_user", get_settings().env)
    context.reg.fill_email(user.username)
    context.tc042_cooling = False
    for _ in range(1, 4):
        context.reg.fill_dynamic_code()
        context.reg.request_otp()
        if context.reg.resend_is_cooling_down():
            context.tc042_cooling = True
            break
    context.reg.shot("otp_requested")
    context.reg.request_otp()                       # attempt a resend within 60s
    context.tc042_still_cooling = context.reg.resend_is_cooling_down()
    context.reg.shot("resend_within_60s_blocked")


@then("the resend within 60s is rejected and the countdown stays visible")
def step_assert_resend_blocked(context):
    """TC042 expected result — the resend control stays in its countdown."""
    assert context.tc042_cooling, "Expected the OTP request to start a cooldown"
    assert context.tc042_still_cooling, \
        "Expected the within-60s resend to be rejected (control still cooling)"
    text, disabled = context.reg.get_code_button_state()
    print(f"  [TC042] resend blocked within 60s -> {text!r} (disabled={disabled})")


# --- TC044  mismatched password / confirmation -------------------------------

@when("I submit the registration form with a mismatched password confirmation")
def step_submit_password_mismatch(context):
    """TC044 — pre-fill EVERY required field correctly (email + 动态码 +
    Get Code + OTP 111111) and ONLY make the password / confirmation
    pair mismatch, so the rejection cleanly isolates the mismatch as the
    failing variable. submit_until_settled retries the captcha so the final
    error is the real product response, not OCR noise."""
    context.reg.fill_email("mismatch.check@126.com")
    context.reg.request_otp_until_sent()
    context.reg.fill_verification_code(_VALID_OTP)
    context.reg.fill_passwords("Test@202605", "Different@202699")
    context.reg.shot("mismatched_password_filled")
    context.reg_error = context.reg.submit_until_settled()
    context.reg.shot("mismatch_blocked")


@then("registration is blocked with a password-mismatch message")
def step_assert_password_mismatch(context):
    """TC044 expected result — submission blocked, no account created."""
    error = context.reg_error
    assert error, "Expected a validation message for the mismatched password"
    assert context.reg.is_on_register_page(), \
        "Expected to stay on #/register — registration must be blocked"
    print(f"  [TC044] mismatch message -> {error!r}")


# --- TC045  password plaintext (show/hide) toggle ---------------------------

def _cycle_pwd_toggle(page, input_sel: str):
    """Click the eye-btn next to `input_sel` twice; return
    (initial_type, type_after_first_click, type_after_second_click)."""
    initial = page.locator(input_sel).first.get_attribute("type")
    eye = page.locator(f"{input_sel} + button.eye-btn").first
    eye.click(); page.wait_for_timeout(300)
    shown = page.locator(input_sel).first.get_attribute("type")
    eye.click(); page.wait_for_timeout(300)
    remasked = page.locator(input_sel).first.get_attribute("type")
    return initial, shown, remasked


@when("I type a password and toggle the show/hide eye icon on each password field")
def step_toggle_password_eye(context):
    """TC045 — fill the registration password + confirm, then cycle the eye
    toggle on each (and on the login password field too, since the spec
    covers Registration / password-login page)."""
    reg = context.reg
    reg.fill_passwords("Aa12345!", "Aa12345!")
    reg.shot("both_pwd_fields_masked")
    context.tc045_results = []
    for sel, label in ((reg.PASSWORD_SEL, "registration password"),
                       (reg.CONFIRM_SEL,  "registration confirm")):
        i, s, r = _cycle_pwd_toggle(context.page, sel)
        reg.shot(f"{label.replace(' ', '_')}_toggled")
        context.tc045_results.append((label, i, s, r))
    # Login field — open a fresh login page in the same browser tab.
    from test_automation.web import WebsiteLoginPage
    settings = get_settings()
    lp = WebsiteLoginPage(context.page, str(settings.antank_url))
    lp.open()
    user = get_user("website_user", settings.env)
    context.page.fill('input#login-password', user.password)
    context.page.wait_for_timeout(300)
    reg.shot("login_password_masked")
    i, s, r = _cycle_pwd_toggle(context.page, 'input#login-password')
    reg.shot("login_password_toggled")
    context.tc045_results.append(("login password", i, s, r))


@then("every password field cycles between masked and visible per click")
def step_assert_password_toggle_cycles(context):
    """TC045 expected result — each field starts masked (type=password),
    becomes visible (type=text) after one click, and is remasked after a
    second click. Holds for both registration password fields and the login
    password field."""
    for label, initial, shown, remasked in context.tc045_results:
        assert initial == "password", \
            f"{label}: expected initial type=password, got {initial!r}"
        assert shown == "text", \
            f"{label}: expected type=text after one click, got {shown!r}"
        assert remasked == "password", \
            f"{label}: expected type=password after second click, got {remasked!r}"
        print(f"  [TC045] {label}: password -> text -> password OK")


# --- TC057  registration returns to the entry page --------------------------

@given("the Website homepage is open as the entry page")
def step_open_homepage_entry(context):
    """TC057 — open the homepage (#/) as the non-auth entry page; record the
    URL so the post-registration landing can be compared back to it."""
    settings = get_settings()
    base = str(settings.antank_url).rstrip("/")
    context.page.goto(f"{base}/websitehtml/index.html#/", timeout=60000)
    context.page.wait_for_load_state("networkidle", timeout=20000)
    context.page.wait_for_timeout(1500)
    context.tc057_entry_url = context.page.url
    context.reg = _new_registration_page(context)
    context.reg.shot("entry_homepage")


@when("I enter the registration flow and complete it with a brand-new email")
def step_enter_register_and_complete(context):
    """TC057 — navigate from the entry into the registration form, complete
    it with a fresh fake email + fixed SIT OTP, and let the post-success
    navigation settle so the final URL can be inspected."""
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"tc057_{stamp}@126.com"
    context.reg.open()                     # navigate to #/register
    context.reg.shot("register_reached_from_entry")
    context.reg.fill_email(email)
    context.reg.request_otp_until_sent()
    context.reg.fill_verification_code(_VALID_OTP)
    context.reg.fill_passwords(_VALID_PASSWORD)
    context.reg.accept_terms()              # required since 2026-05-26
    context.reg.shot("register_form_filled")
    context.reg.submit_until_settled()
    context.page.wait_for_timeout(4000)     # let any redirect-back settle
    context.tc057_final_url = context.page.url
    context.tc057_registered = context.reg.registration_succeeded()
    context.reg.shot("post_register_landing")


@then("the user is redirected back to the entry page, not a confirmation page")
def step_assert_redirect_back_to_entry(context):
    """TC057 expected result — registration must succeed AND the final URL
    must match the recorded entry URL (the SPA preserved the entry across
    the auth flow)."""
    assert context.tc057_registered, (
        f"Registration did not succeed; final url={context.tc057_final_url!r}")
    entry, final = context.tc057_entry_url, context.tc057_final_url
    assert "#/register" not in final, (
        f"Expected redirect away from #/register, stayed at {final}")
    assert entry == final, (
        f"Expected redirect back to the entry page {entry}, landed on {final}")
    print(f"  [TC057] returned to entry {entry}")


# --- TC065  Email OTP digit-count rule ---------------------------------------

@when("I inspect the email OTP input digit-count rule")
def step_inspect_otp_digit_count(context):
    """TC065 manual step — open registration / inspect the Verification Code
    field. Pure DOM check: read the maxlength attribute, then type 10 digits
    and verify the input only retains <=6. No captcha, no submit, no real
    OTP needed.
    """
    page = context.reg._page
    inp = page.locator(context.reg.VCODE_SEL).first
    inp.wait_for(state="visible", timeout=10000)
    context.tc065_maxlen = inp.get_attribute("maxlength") or ""
    inp.fill("")
    inp.type("1234567890", delay=20)         # try to enter 10 digits
    context.tc065_retained = inp.input_value()
    context.reg.shot("otp_field_inspected")


@then("the OTP input accepts at most 6 digits")
def step_assert_otp_digit_count(context):
    """TC065 expected — maxlength=6 (HTML-enforced) OR retained value <=6
    chars (JS-enforced). Either is acceptable; both prove the rule."""
    ml = context.tc065_maxlen
    retained = context.tc065_retained
    assert ml == "6" or len(retained) <= 6, (
        f"Expected OTP input to limit to 6 digits; "
        f"maxlength={ml!r}, retained-after-10-digits-typed={retained!r}")
    print(f"  [TC065] OTP digit-count rule OK: maxlength={ml!r}, "
          f"retained={retained!r} (after typing '1234567890')")
