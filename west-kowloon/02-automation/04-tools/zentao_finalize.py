"""Finalize task 10219:
  1. Write the run summary into the action log via POST /actions
  2. Close the task (close transition) with closedReason=done
"""
import os, sys, json
from datetime import datetime
import requests

TOKEN = os.environ.get("ZENTAO_API_V2_TOKEN")
if not TOKEN:
    print("ERROR: ZENTAO_API_V2_TOKEN not set")
    sys.exit(1)

BASE  = "https://lengliwh.chandao.net"
H_JSON = {"Token": TOKEN, "Content-Type": "application/json"}
TASK_ID = 10219

COMMENT = (
    "【自动化交付 2026-05-23】西九官网 注册/登录/忘记密码 SIT dry-run\n\n"
    "范围: SIT-TC-WEB-AUTH-001..074 (剔除 TC007 / TC073)；共 72 用例。\n\n"
    "结果统计:\n"
    "  - Pass: 30\n"
    "  - NA:   38 (30 个 design 自标 Deferred/TBD/DO-NOT-EXECUTE；\n"
    "             4 个 TC051-054 因 OTP-mode 表单与 spec 不一致, 实际\n"
    "             3 字段无 password)\n"
    "  - Fail: 4\n"
    "      * TC004 - DEF-1 已知缺陷: 重复邮箱注册被允许, 且重置账号密码\n"
    "      * TC034/55/57 - 今日 SIT 邮箱 OTP 111111 被服务端拒绝\n"
    "        ('邮箱验证码错误,请重新输入!'); 昨日同代码同账号能通过.\n"
    "        自动化代码与场景完整, 需产品/开发确认 OTP 测试码是否变更.\n\n"
    "黄色 TBD 用例核查: 17 个 → 9 个根据 UI 实证转白\n"
    "  (TC015/22/30/34/35/46/47/65/70), 余 8 个仍待产品给配置/策略.\n\n"
    "自动化资产: D:/Workspace/west-kowloon/02-automation (5 个 feature 文件 + 04-tools/update_evidence.py).\n"
    "结果工作簿 (71/72 行嵌入截图):\n"
    "  D:/Workspace/west-kowloon/01-requirements/02-subprojects/02-website/02-modules/\n"
    "  01-login-registration/2026-06-16/03-test-design/test-cases-registration-login.xlsx\n\n"
    "QA Dashboard 已记录本批 8 个新场景的 Run 49/50/51.\n\n"
    "(注: chandao SaaS API 不允许文件上传, 故 xlsx 未作附件; 请按上面路径查看.)"
)


def try_action_log():
    """Try writing the comment as an action log entry on the task."""
    candidates = [
        ("POST /api.php/v1/actions",
         f"{BASE}/api.php/v1/actions",
         {"objectType": "task", "objectID": TASK_ID, "action": "commented",
          "comment": COMMENT}),
        ("POST /api.php/v1/tasks/{id}/actions",
         f"{BASE}/api.php/v1/tasks/{TASK_ID}/actions",
         {"action": "commented", "comment": COMMENT}),
        ("POST /api.php/v1/tasks/{id}/comments",
         f"{BASE}/api.php/v1/tasks/{TASK_ID}/comments",
         {"comment": COMMENT}),
    ]
    for label, url, body in candidates:
        print(f"\n--- {label} ---")
        try:
            r = requests.post(url, headers=H_JSON, data=json.dumps(body), timeout=20)
            print(f"  status={r.status_code}  body={r.text[:300]}")
            if r.status_code in (200, 201) and 'error' not in r.text.lower():
                return True
        except Exception as e:
            print(f"  EXC: {e}")
    return False


def try_close():
    """Close transition: POST /tasks/{id}/close with closedReason=done."""
    url = f"{BASE}/api.php/v1/tasks/{TASK_ID}/close"
    body = {"closedReason": "done", "comment": "已完成,见前置注释。"}
    r = requests.post(url, headers=H_JSON, data=json.dumps(body), timeout=20)
    print(f"\n=== POST /tasks/{TASK_ID}/close ===")
    print(f"  status={r.status_code}  body={r.text[:300]}")
    return r.status_code in (200, 201)


if __name__ == "__main__":
    print("=== STEP 1: write comment to action log ===")
    try_action_log()
    print("\n=== STEP 2: close transition (closedReason=done) ===")
    try_close()
