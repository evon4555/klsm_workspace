# Website Mindmap Extract

---

## [SECTION] About

Structured extract of the West Kowloon Website mindmap maintained in Feishu. See `mindmap-source.md` for the live source link and snapshot files.

This file is **incremental**: branches are filled in as their sub-trees are captured. Branches marked `[NOT YET CAPTURED]` have not been extracted in detail; consumers must not assume the absence of detail here means absence of requirement.

Extraction status as of 2026-05-15:

- Level 1 (root → first-level branches): complete
- Sub-trees: not yet captured

---

## [SECTION] Root

- Root node: **西九官网** (West Kowloon Official Website)
- Source format: Feishu mind map / document
- Note on counts: numbers in parentheses below are descendant-node counts shown on the mindmap, useful as a size signal per branch.

---

## [SECTION] First-Level Branches

| # | Branch (CN) | Branch (EN, working translation) | Descendant Count | Highlight | Notes |
|---|---|---|---|---|---|
| 1 | 注册/登录（只支持邮箱） | Registration / Login | ~12X | — | **Per project rule (mindmap authoritative), ignore the "只支持邮箱" qualifier.** Actual sub-tree includes: email registration with password, two login modes (password + verification-code), guest login, 5 third-party providers (Google/Facebook/X/Tiktok/wechat), forgot password (mindmap-only, marked "PRD上没有写"). Mobile registration/login are yellow placeholders — in scope, not yet detailed. See sub-tree below. |
| 2 | 个人中心 | Personal Centre | 121 | — | Registered-user account area. Largest among user-facing account branches. |
| 3 | 首页 | Home Page | 52 | — | |
| 4 | 页眉 | Header | 18 | — | |
| 5 | 页脚 | Footer | 3 | — | |
| 6 | 项目详情页 | Project / Event Detail Page | 384 | — | **Largest branch.** Likely covers event description, scheduling, seat selection, pricing tiers, etc. |
| 7 | 会员 | Membership | 87 | — | Distinct from 个人中心. Likely benefits / tiers / privileges. |
| 8 | 核销 | Redemption / Check-in | 7 | — | Small. Possibly e-ticket-side flow on web. |
| 9 | Ecommerce | Ecommerce | — | Yellow highlight | Not expanded. Status to confirm: TBD / out of scope / split elsewhere. |
| 10 | 购物车 | Shopping Cart | — | Yellow highlight | Not expanded. Same status question as above. |
| 11 | 抽签 | Lottery / Ballot | — | Yellow highlight | Not expanded. Same status question. |
| 12 | 无障碍方式 | Accessibility | — | Yellow highlight | Not expanded. Same status question. |
| 13 | 活动 | Events / Campaigns | 81 | — | |
| 14 | 跨场次套票 | Cross-Show Bundle | 16 | — | Multi-performance package. |
| 15 | 门票联票 | Ticket Combo / Joint Ticket | 28 | — | Multi-venue or multi-product combo ticket. |
| 16 | Cookie | Cookie | 5 | — | |

---

## [SECTION] Yellow-Highlight Status Question

Four branches (`Ecommerce`, `购物车`, `抽签`, `无障碍方式`) are yellow-highlighted with no descendant count visible. This pattern typically indicates one of:

1. Newly added placeholder, not yet detailed.
2. Out of current release scope.
3. Detail maintained in a separate document.

**Owner action required**: confirm the meaning of yellow highlight in this mindmap's convention before this extract is treated as authoritative for scope decisions.

---

## [SECTION] Sub-Tree Detail

### [FIELD] 1. 注册/登录

**Captured 2026-05-15** from four screenshots in `..\..\02-modules\01-login-registration\2026-06-16\01-input\02-mindmap\`:
- `注册.png` — registration sub-tree
- `登录1.png` — 密码登录 + 验证码登录
- `登录2.png` — 游客登录 + 第三方登录 + 手机登录(placeholder)
- `忘记密码.png` — forgot password (mindmap-only, not in PRD)

**Scope resolution:** Ignore the level-1 qualifier "（只支持邮箱）". Per user direction, the mindmap content (sub-tree) is the truth; that label is to be disregarded.

#### 注册 (Registration)

**进入注册途径**
- 登录页面下方注册 link

**注册信息内容**
- **邮箱地址**
  - 邮箱验证
  - 如邮箱已注册, 提示已注册信息 (多语言)
- **密码 / 密码确认**
  - 密码规则
  - 是否有明码显示密码内容
  - 两次密码输入不同 → 提示失败
- **动态码** (image captcha)
  - 动态码有效期
  - 输错后自动刷新
  - 点图片自动刷新
  - 动态码必须匹配图片
- **验证码** (email OTP)
  - 60 秒防重复提交
  - 重发: 重发验证码不重复; 重发后上一个验证码失效
  - 与邮箱验证码一致
  - 验证码规则 (几位数字)
  - 验证码邮件:
    - 多语言情况不同邮件
    - 格式 / 内容 / 发件人 / 标题
    - 邮件中有 link 可以点击 link 完成注册
      - 点击 link 成功注册 → 返回跳转到原进入登录注册页面前的页面
      - 点击 link 注册失败 → 返回注册页面
      - Link 失效时间
  - 验证码有效期
- 以上所有错误情况的错误提示语, 多语言
- 以上内容页面提示信息 (比如邮箱, 密码), 多语言
- 注册成功 → 返回跳转到原进入登录注册页面前的页面
- **手机注册** `[YELLOW — placeholder, in scope but not yet detailed]`

#### 登录 (Login)

##### 密码登录
- 正确邮箱 + 密码 + 动态码 可登录
- **动态码** (image captcha)
  - 动态码有效期
  - 输错后自动刷新?
  - 点图片自动刷新
  - 动态码必须匹配图片
- 登录过期时间? → 过期自动退出  *(open question in mindmap)*
- 主动退出
- 任何一项 (邮箱 / 密码 / 动态码) 错误, 提示信息 (多语言)
- 任何两项错误, 提示信息 (多语言)
- 所有信息都错误 (多语言)

##### 验证码登录
- 正确邮箱 + 密码 + 动态码 + 验证码 可登录  *(source literally lists 4 fields including password; verify with product whether password is required in this mode)*
- **动态码** (same captcha rules as password login)
- **验证码** (email OTP, same structure as registration)
- 主动退出
- 登录过期时间? → 过期自动退出  *(open question in mindmap)*
- 任何一项 / 两项 / 三项 / 所有信息错误 → 多语言提示

##### 游客登录
- 机器人验证
  - 验证失败跳转什么页面?  *(open question in mindmap)*
  - 返回跳转到原进入登录注册页面前的页面
- 登录过期时间? (按最后一次操作计算还是从登录开始计算)  *(open question in mindmap)* → 过期自动退出 → 清空游客数据
- 主动退出 → 清空游客数据

##### 第三方登录
Explicit provider list (5):
- Google
- Facebook
- X
- Tiktok
- wechat

Rules / open questions:
- 这些登录方式后, 是不是在分享的时候就能直接跳转到对应的网站并且登录?  *(open question)*
- 第一次登录页还是要注册邮箱, 以后再次登录就能直接进  *(rule: first-time still requires email registration; subsequent logins direct)*

##### 手机登录
`[YELLOW — placeholder, in scope but not yet detailed]`

##### 共用规则 (across all login modes)
- 以上所有错误情况的错误提示语, 多语言
- 以上内容页面提示信息 (比如邮箱, 密码), 多语言

#### 忘记密码 (PRD 上没写, 仅脑图)

**Mindmap author annotation:** `忘记密码 (PRD上没有写)` — explicitly flagged as a flow that exists in mindmap but not in PRD. Per project rule, **this is in scope**.

- **输入邮箱**
  - 邮箱已注册 → 发送零时密码?  *(open question)* → 登录有引导修改密码?  *(open question)*
  - 邮箱未注册 → 提示错误信息
- **验证码** (email OTP, same structure as registration)
- **动态码** (same captcha rules)

### [FIELD] 2. 个人中心

[NOT YET CAPTURED]

Priority: high. Dry-run regression cases (guest-restricted access to personal centre, wallet, orders, coupons, membership, favourites) depend on knowing the actual page entries here.

### [FIELD] 3. 首页

[NOT YET CAPTURED]

### [FIELD] 4. 页眉

[NOT YET CAPTURED]

### [FIELD] 5. 页脚

[NOT YET CAPTURED]

### [FIELD] 6. 项目详情页

[NOT YET CAPTURED]

Note: largest branch (384 descendants). Likely a future high-priority requirement package on its own.

### [FIELD] 7. 会员

[NOT YET CAPTURED]

### [FIELD] 8. 核销

[NOT YET CAPTURED]

### [FIELD] 9. Ecommerce

[NOT YET CAPTURED] — status unclear (see Yellow-Highlight Status Question above).

### [FIELD] 10. 购物车

[NOT YET CAPTURED] — status unclear.

### [FIELD] 11. 抽签

[NOT YET CAPTURED] — status unclear.

### [FIELD] 12. 无障碍方式

[NOT YET CAPTURED] — status unclear.

### [FIELD] 13. 活动

[NOT YET CAPTURED]

### [FIELD] 14. 跨场次套票

[NOT YET CAPTURED]

### [FIELD] 15. 门票联票

[NOT YET CAPTURED]

### [FIELD] 16. Cookie

[NOT YET CAPTURED]

---

## [SECTION] Cross-References

### [FIELD] Source Authority (Resolved 2026-05-15)

For this project, **mindmap is authoritative; PRD is reference / background**. The earlier mindmap-vs-PRD conflict on the "只支持邮箱" label was resolved: ignore the label; mindmap sub-tree content is the truth. PRDs remain useful as supporting context but do not override mindmap. See memory `project-west-kowloon-source-authority`.

### [FIELD] Gap Analysis Pointer

Detailed gap analysis between the captured mindmap content and the existing dry-run outputs is now maintained in the login/registration module package:

- `..\..\02-modules\01-login-registration\2026-06-16\02-analysis\requirement-risk-review-registration-login.md`
- `..\..\02-modules\01-login-registration\2026-06-16\02-analysis\test-strategy-registration-login.md`

Major gap themes already visible from level-2 capture:

- **Image captcha (动态码)** is in every flow (registration, both login modes, forgot password). Existing dry-run mentions captcha only briefly for guest. Real coverage gap.
- **Two distinct login modes** (password vs verification-code) — existing test cases conflate them.
- **Email verification link** (clickable link in email, alternative to entering code) — not in current test cases.
- **Forgot password flow** is in scope (mindmap-only, PRD silent) — current cases SIT-TC-WEB-AUTH-015/016 cover this but were conditional on "Figma scope confirmation"; mindmap confirms.
- **Specific 5 third-party providers**: Google / Facebook / X / Tiktok / wechat — existing risk review listed broader set as open question; mindmap closes it.
- **Error message permutations** (1 wrong / 2 wrong / 3 wrong / all wrong) — beyond current case granularity.
- **Multilingual** is cross-cutting, not just a single case.

PRD-only findings that earlier appeared as "gaps" but are **not necessarily in scope** (because mindmap is authoritative and may have deliberately excluded them):

- Auto-registration on first verification-code login (PRD §3.2.1) — mindmap registration sub-tree does not describe this. **Confirm with user.**
- 5-minute-remaining popup countdown for guest (PRD §3.2.3) — mindmap guest sub-tree does not describe this. **Confirm with user.**
- WestK SSO three jump scenarios (PRD §3.2.4 待讨论) — mindmap has no SSO branch in registration/login sub-tree at all. **Confirm with user.**

---

## [SECTION] Update History

| Date | Author | Change |
|---|---|---|
| 2026-05-15 | AI extract | Initial level-1 capture from cropped screenshot. Sub-trees pending. |
| 2026-05-15 | AI extract | Cross-checked level-1 against PRDs in `..\02-prd\`. Found mindmap-PRD conflict on registration/login scope. Replaced earlier "test cases invalid" claim with conflict-aware note. Added gap list of PRD-described features missing from current dry-run outputs. |
| 2026-05-15 | AI extract | Captured full registration/login sub-tree from 4 PNGs (注册 / 登录1 / 登录2 / 忘记密码). User resolved authority: mindmap > PRD; ignore "只支持邮箱" label. Updated branch-1 detail and cross-references accordingly. Surfaced three PRD-only items as "confirm with user" rather than as gaps. |
