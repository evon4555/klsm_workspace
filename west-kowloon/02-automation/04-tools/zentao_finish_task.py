"""Close ZenTao task 10219:
  - consumed=16
  - status=done
  - finishedDate=now
  - a long Chinese comment summarising today's run (72 cases; Pass/Fail/NA;
    DEF-1; OTP env block; automation locations; xlsx path).

Tries POST /tasks/{id}/finish first (standard transition). Falls back to
PUT /tasks/{id} if that 404s.
"""
import os, sys, json
from datetime import datetime
import requests

TOKEN = os.environ.get("ZENTAO_API_V2_TOKEN")
if not TOKEN:
    print("ERROR: ZENTAO_API_V2_TOKEN not set"); sys.exit(1)
BASE = "https://lengliwh.chandao.net"
TASK_ID = 10219
H_JSON = {"Token": TOKEN, "Content-Type": "application/json"}

COMMENT = (
    "【自动化交付 2026-05-23】西九官网 注册/登录/忘记密码 SIT dry-run\n\n"
    "范围: SIT-TC-WEB-AUTH-001 .. 074 (TC007 / TC073 已剔除)；共 72 用例。\n\n"
    "结果统计:\n"
    "  - Pass: 30\n"
    "  - NA:   38 (其中 30 个 test design 自标 Deferred / TBD / DO-NOT-EXECUTE,\n"
    "             另外 4 个 TC051-054 是 OTP-mode 表单字段与 spec 不一致 - 实际\n"
    "             只有 3 个字段, 没有 password)\n"
    "  - Fail: 4\n"
    "      * TC004 - DEF-1 已知缺陷: 重复邮箱注册被允许, 且会重置账号密码\n"
    "      * TC034 / TC055 / TC057 - 今日 SIT 邮箱 OTP 服务环境变化:\n"
    "        固定测试码 111111 不再被接受 (服务器返回\n"
    "        '邮箱验证码错误,请重新输入!'). 昨日 (2026-05-22) 相同代码+\n"
    "        账号能通过. 自动化代码与 Behave 场景均完整, 需要产品/开发\n"
    "        确认 OTP 测试码是否被移除或服务降级.\n\n"
    "自动化资产 (D:/Workspace/west-kowloon/02-automation):\n"
    "  - 01-features/ui_e2e/antank_registration.feature\n"
    "  - 01-features/ui_e2e/antank_email_login.feature\n"
    "  - 01-features/ui_e2e/antank_forgot_password.feature\n"
    "  - 01-features/ui_e2e/antank_guest_login.feature\n"
    "  - 01-features/ui_e2e/antank_session_ui.feature\n"
    "  - 04-tools/update_evidence.py (一键刷新 xlsx + 内嵌截图)\n"
    "  - 04-tools/sync_md_results.py (xlsx → md 同步)\n\n"
    "结果工作簿 (含 71/72 行嵌入截图):\n"
    "  D:/Workspace/west-kowloon/01-requirements/02-subprojects/02-website/02-modules/\n"
    "  01-login-registration/2026-06-16/03-test-design/test-cases-registration-login.xlsx\n\n"
    "执行记录:\n"
    "  D:/Workspace/west-kowloon/01-requirements/02-subprojects/02-website/02-modules/\n"
    "  01-login-registration/2026-06-16/05-execution/test-execution-record-registration-login.md\n\n"
    "黄色 TBD 用例核查 (2026-05-23 同步):\n"
    "  - 9 个黄色项已通过 UI 实证转白: TC015 / TC022 / TC030 / TC034 /\n"
    "    TC035 / TC046 / TC047 / TC065 / TC070\n"
    "  - 8 个仍为黄色 (TC064 / TC066 / TC067 / TC068 / TC069 / TC071 /\n"
    "    TC072 / TC074), 全部需要产品/开发给配置值或策略决定\n\n"
    "QA Dashboard:\n"
    "  - 已为本批 8 个新场景在 dashboard 记录了 Run 49 / 50 / 51\n"
    "  - 5 个非 OTP 场景全部 Pass; OTP 相关 2 个 Fail 已记录原因\n\n"
    "(说明: 由于 chandao SaaS API 不允许文件上传, xlsx 未作为附件;\n"
    "完整结果工作簿请按上面路径查看, 或后续走 dashboard 同步入口.)"
)

def try_finish():
    """Standard transition: POST /tasks/{id}/finish."""
    url = f"{BASE}/api.php/v1/tasks/{TASK_ID}/finish"
    body = {
        "currentConsumed": 16,
        "consumed": 16,
        "left": 0,
        "comment": COMMENT,
        "finishedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    r = requests.post(url, headers=H_JSON, data=json.dumps(body), timeout=30)
    print(f"POST /tasks/{TASK_ID}/finish  status={r.status_code}")
    print(f"  body[0..400] = {r.text[:400]}")
    return r

def try_put():
    """Fallback: PUT /tasks/{id} with status=done + fields."""
    url = f"{BASE}/api.php/v1/tasks/{TASK_ID}"
    body = {
        "status": "done",
        "consumed": 16,
        "left": 0,
        "finishedDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "comment": COMMENT,
    }
    r = requests.put(url, headers=H_JSON, data=json.dumps(body), timeout=30)
    print(f"PUT /tasks/{TASK_ID}  status={r.status_code}")
    print(f"  body[0..400] = {r.text[:400]}")
    return r

def main():
    print("=== Attempt 1: POST /tasks/{id}/finish ===")
    r = try_finish()
    if r.status_code in (200, 201):
        try:
            j = r.json()
            ok = (j.get("status") == "success" or j.get("id") or j.get("data"))
            if ok:
                print("  -> looks OK; verify below")
                return
        except Exception:
            pass
    print("\n=== Attempt 2: PUT /tasks/{id} with status=done ===")
    r = try_put()

if __name__ == "__main__":
    main()
