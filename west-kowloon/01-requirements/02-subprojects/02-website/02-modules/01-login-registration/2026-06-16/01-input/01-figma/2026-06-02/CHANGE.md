# Change 2026-06-02

**Why:**       第三方登录功能 UI/流程明细化 — 新增"Link Your Account"账号绑定中间页。OAuth 认证成功后,如果该第三方账号是首次接入,引导用户用 Email 或 Phone 完成绑定;系统根据该 Email/Phone 是否已注册分两条分支处理。
**Source:**    https://wtvrhpmlkj.feishu.cn/docx/YWQddc6p0opPOAxkY4ucKrxgnVh#share-LpOzdTZjdom9STxrhQicaK0UntT  §3.2.2 第三方平台授权登录(2026-05-26 完善绑定流程)
**Approver:**  Sivya
**Effective:** 2026-06-30

**Scope:**
  - Modify (7):  AUTH-017, AUTH-018, AUTH-059, AUTH-060, AUTH-061, AUTH-062, AUTH-063
  - Add (10):    AUTH-078 ... AUTH-087
  - Deprecate (0): —

**Sources delta this change:**
  - figma/2026-06-02/ — 6 张联名登录页面 截图
  - prd/2026-06-02/国际版标准官网 - 在线购票.md  §3.2.2 (PRD 章节加 "2026-05-26 完善绑定流程" 子节)
  - prd/2026-06-02/联名登录流程图.png
  - prd/2026-06-02/本次修改-联名登录.png
  - mindmap/2026-06-02/ — 待补 (mindmap 未更新)

**Open questions (from PRD §3.2.2):**
  1. OTP 验证未通过是否有尝试次数 / 时间上限? 超限是退回未登录还是允许继续重试?  (PRD 标注 "待确认")
  2. 第三方平台列表是 5 个(Google/Facebook/TikTok/X/WeChat,来自 figma) 还是包含 WhatsApp(PRD 例举)? 以哪一份为准?
  3. 第三方返回的 email/phone 默认填入 Link 页时,如果用户修改成另一个,后端走"新账号"还是"已注册账号"分支取决于哪个值?
