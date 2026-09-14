"""Write the run summary into task 10219's desc field (visible at top of the
task page in 禅道)."""
import os
import sys
import json

import requests

TOKEN = os.environ.get("ZENTAO_API_V2_TOKEN")
if not TOKEN:
    print("ERROR: ZENTAO_API_V2_TOKEN not set")
    sys.exit(1)

BASE  = "https://lengliwh.chandao.net"
TASK_ID = 10219
H = {"Token": TOKEN, "Content-Type": "application/json"}

DESC = """\
<h3>自动化交付 2026-05-23 — 西九官网 注册/登录/忘记密码 SIT dry-run</h3>
<p><b>范围:</b> SIT-TC-WEB-AUTH-001..074 (剔除 TC007 / TC073), 共 72 用例。</p>
<p><b>结果:</b></p>
<ul>
  <li><b>Pass: 30</b></li>
  <li><b>NA: 38</b> (30 个 design 自标 Deferred/TBD/DO-NOT-EXECUTE;
    4 个 TC051-054 因 OTP-mode 表单与 spec 不一致, 实际 3 字段无 password;
    其余 4 个属之前批次)</li>
  <li><b>Fail: 4</b>
    <ul>
      <li><b>TC004</b> — DEF-1 已知缺陷: 重复邮箱注册被允许, 且会重置账号密码</li>
      <li><b>TC034 / TC055 / TC057</b> — 今日 SIT 邮箱 OTP <code>111111</code>
        被服务端拒绝, 返回 <code>"邮箱验证码错误,请重新输入!"</code>;
        昨日同代码同账号能通过. 自动化代码与场景完整,
        需产品/开发确认 OTP 测试码是否变更或服务降级.</li>
    </ul>
  </li>
</ul>
<p><b>黄色 TBD 用例核查:</b> 17 → 9 个根据 UI 实证转白
  (TC015 / 22 / 30 / 34 / 35 / 46 / 47 / 65 / 70); 余 8 个仍黄
  (TC064 / 66 / 67 / 68 / 69 / 71 / 72 / 74), 需产品给配置值或策略决定。</p>
<p><b>自动化资产:</b> <code>D:/Workspace/west-kowloon/02-automation</code>
  (5 个 feature 文件 + <code>04-tools/update_evidence.py</code> +
  <code>04-tools/sync_md_results.py</code>)</p>
<p><b>结果工作簿</b> (71/72 行嵌入截图):<br>
  <code>D:/Workspace/west-kowloon/01-requirements/02-subprojects/02-website/02-modules/01-login-registration/2026-06-16/03-test-design/test-cases-registration-login.xlsx</code></p>
<p><b>执行记录:</b><br>
  <code>D:/Workspace/west-kowloon/01-requirements/02-subprojects/02-website/02-modules/01-login-registration/2026-06-16/05-execution/test-execution-record-registration-login.md</code></p>
<p><b>QA Dashboard:</b> 本批 8 个新场景的执行记录在 Run 49 / 50 / 51 (5 个非 OTP 全 Pass; 2 个 OTP fail 已记录原因).</p>
<p><i>说明: chandao SaaS API 不允许文件上传, 故 xlsx 未作附件; 请按上面本地路径查看, 或后续通过 dashboard 同步入口。</i></p>
"""

r = requests.put(f"{BASE}/api.php/v1/tasks/{TASK_ID}",
                 headers=H, data=json.dumps({"desc": DESC}), timeout=30)
print(f"PUT /tasks/{TASK_ID}  status={r.status_code}  body={r.text[:200]}")
