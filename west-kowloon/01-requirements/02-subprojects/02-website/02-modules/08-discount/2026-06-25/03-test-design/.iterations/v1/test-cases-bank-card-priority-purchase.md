# Test Cases — 银行卡优先购 (Bank-card Priority Purchase)

## [SECTION] Scope Summary

- Feature: 合作方会员身份（BIN/API 绑定）+ 银行卡优先购 + mid 冲突 (F1-F12, 共 12 条能力)
- Source authority: PRD 工作底本 (本故事无脑图)
- Risk level: **High** (营收相邻；影响结算流程；mid 绑定时机与 PRD 描述不一致)
- Assumptions:
  - SIT environment, mock BIN 库 + mock 合作方（Q-3 = c，不依赖真实卡）
  - Q-5 = (b) **mid 在支付方式选择时绑定到订单**（与 PRD §3.2 末段描述不一致，测试经理 2026-06-26 确认会配置好后端）
  - U-1 = 加入购物车后快照判定（不在支付前重判）
  - U-2 = 支付成功扣减次数；全额退款反转
  - U-4 = BIN 跨合作方冲突时默认取列表第一个
  - U-5 = BIN 绑定要求完整卡号
- Mock 数据基线:
  - 合作方甲 (BIN)：钻石 (BIN 411111/542210，次数 5，提前 30 分)、白金 (BIN 622202，次数 3，提前 15 分)
  - 合作方乙 (BIN)：业主 (BIN 411111，次数 10，提前 45 分) — 与甲钻石的 BIN 冲突
  - 合作方丙 (API)：普通 (次数 2，提前 10 分，需填邮箱+工号)
  - 测试卡：4111-1111-1111-1111 / 5422-2222-2222-2222 / 6222-0202-0000-0001 / 9999-9999-9999-9999
  - 测试事件：测试演出，公售 2026-08-01 10:00
  - 测试用户：guest1 (无绑定) / user1 (甲钻石) / user2 (甲钻石+白金) / user3 (BIN 冲突) / user4 (API 丙) / user5 (凭证过期)
- 黄色标记: ~~已全部消化~~ — Q-7(a) 部分退款不反转、Q-8(a) 翻译 fallback zh-CN、BPP-037 重分类为联调验证（Q-5(b) 已签）。详见 consolidation v2 修订历史 2026-06-27
- 不在本范围: 白名单/OAuth (Q-1=a)、会员专享项目/商品/促销活动 (Q-2=a)、§1.1/1.2/2.1 后台 (标准产品后台测试组)

## [SECTION] Test Cases

| Test Case ID | Module/Feature | Priority | Severity | Collected from | Test Scenario | Test Case Description | Preconditions | Test Steps | Test Data | Expected Result | Test Case Owner | Environment | Execution Date | Executed By | Actual Result | Status | Comments/Remarks | Screenshots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SIT-TC-WEB-BPP-001 | Website / Member Benefits / Identity Binding | Medium | Low | PRD §3.1 列表 / F1 | 未绑定用户访问我的权益身份 | 验证空状态展示 | guest1 已登录，无任何绑定 | 1. 登录 guest1@test.com<br>2. 进入个人中心 → 我的权益身份 | guest1 | 1. 页面加载成功<br>2. 显示空状态文案<br>3. 显示「+ 添加新身份」按钮 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-002 | Website / Member Benefits / Identity Binding | High | Medium | PRD §3.1 列表 / F1 | 已绑定 1 张身份的展示 | 验证单卡片信息完整 | user1 已绑定甲钻石，凭证剩 7 天 | 1. 登录 user1@test.com<br>2. 进入我的权益身份 | user1 | 1. 显示 1 张卡片<br>2. 含 合作方甲·钻石 + BIN 校验标签 + 「凭证 7 天后失效」 + 绑定时间 + 解绑按钮 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-003 | Website / Member Benefits / Identity Binding | Medium | Medium | PRD §3.1 列表 / F1 | 已绑定多张身份的展示 | 验证多卡片展示 + 排序 | user2 已绑定甲钻石 + 甲白金 + 丙普通 | 1. 登录 user2@test.com<br>2. 进入我的权益身份 | user2，3 张绑定 | 1. 显示 3 张卡片<br>2. 按绑定时间倒序<br>3. 每张完整展示 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-004 | Website / Member Benefits / Identity Binding | Medium | Medium | PRD §3.1 / F1+F4 | 凭证即将过期的视觉提示 | 验证临期警告 | user1 的甲钻石凭证剩 2 天 | 1. 登录 user1<br>2. 进入我的权益身份 | 凭证剩 2 天 | 1. 显示「凭证 2 天后失效」<br>2. 文案颜色变化（橙/红） | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-005 | Website / Member Benefits / Identity Binding | High | High | PRD §3.1 绑定 / F2 | BIN 绑定主流程 | 输入合法卡号 → 命中 → 绑定成功 | guest1 未绑定 | 1. 添加新身份<br>2. 选合作方甲<br>3. 输入 4111-1111-1111-1111<br>4. 提交 | 4111-1111-1111-1111 | 1. 绑定成功 toast<br>2. 列表新增甲钻石<br>3. 凭证 7 天<br>4. 绑定时间为当前 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-006 | Website / Member Benefits / Identity Binding | High | Medium | U-5 / F2 | BIN 绑定要求完整卡号 | 不完整卡号被前端拦截 | 在 BIN 绑定表单 | 1. 选合作方甲<br>2. 输入 411111（仅 6 位）<br>3. 失焦或提交 | 411111 | 1. 提交按钮禁用 或 行内提示「请输入完整卡号」<br>2. 不发起后端校验 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-007 | Website / Member Benefits / Identity Binding | High | High | PRD §3.1 / F2 | BIN 不命中失败处理 | 合法卡号但 BIN 不在库 → 失败提示 + 重试 | 同上 | 1. 选合作方甲<br>2. 输入 9999-9999-9999-9999<br>3. 提交 | 9999-9999-9999-9999 | 1. 显示「未匹配到 BIN」<br>2. 表单保留<br>3. 可重输入重试 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-008 | Website / Member Benefits / Identity Binding | High | High | U-4 / F2 | 跨合作方 BIN 冲突默认第一个 | BIN 同时命中甲钻石和乙业主 → 取列表第一个 | 4111- 在甲钻石和乙业主下均配置 | 1. 添加新身份<br>2. 选合作方甲<br>3. 输入 4111-1111-1111-1111 | 4111-1111-1111-1111 (双方命中) | 1. 仅绑甲钻石（按列表第一个）<br>2. 不弹选择对话框<br>3. 单绑定成功 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-009 | Website / Member Benefits / Identity Binding | Low | Low | PRD §3.1 / F2 | BIN 绑定取消 | 用户取消未保存 | 在 BIN 绑定表单 | 1. 填卡号<br>2. 点取消 | - | 1. 关闭表单<br>2. 列表不变<br>3. 数据未保存 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-010 | Website / Member Benefits / Identity Binding | High | High | PRD §3.1 绑定 / F3 | API 绑定主流程 | API 校验通过 → 绑定成功 | guest1 未绑定 | 1. 添加新身份<br>2. 选合作方丙<br>3. 表单显示 邮箱+工号<br>4. 填 user@partnerc.com + EMP001<br>5. 提交 | API 返回 valid | 1. 绑定成功<br>2. 列表新增丙普通<br>3. 凭证按合作方配置 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-011 | Website / Member Benefits / Identity Binding | High | High | PRD §3.1 / F3 | API 校验失败 | API 返回不通过 → 失败提示 + 重试 | 同上 | 1. 选合作方丙<br>2. 填 invalid@partnerc.com + EMP999<br>3. 提交 | API 返回 invalid | 1. 显示失败提示<br>2. 表单保留<br>3. 可修改重试 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-012 | Website / Member Benefits / Identity Binding | Medium | Medium | PRD §3.1 / F3 | API 表单必填校验 | 漏填字段被前端拦截 | API 表单加载 | 1. 仅填邮箱<br>2. 工号留空<br>3. 提交 | 邮箱有值，工号空 | 1. 提交按钮禁用 或 行内提示「请填写工号」<br>2. 不调用 API | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-013 | Website / Member Benefits / Identity Binding | Medium | Low | PRD §1.1.2.2 / F4 | 凭证倒计时正确 | 验证倒计时数字按当前时间动态计算 | user1 凭证剩 5 天 | 1. 登录 user1<br>2. 进入我的权益身份 | 凭证 5 天 | 1. 显示「凭证 5 天后失效」<br>2. 数字按当前时间动态 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-014 | Website / Member Benefits / Checkout | High | High | PRD §3.2 / F4+F6 | 过期凭证在结算被忽略 | 过期身份不参与权益判定 | user5 甲钻石凭证已过期 | 1. 登录 user5<br>2. 时间在公售前 25 分（窗口内）<br>3. 加入购物车 | user5 凭证过期 | 1. 不进入优先购<br>2. 显示普通价<br>3. 不打断 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-015 | Website / Member Benefits / Identity Binding | Medium | Medium | PRD §3.1 / F4+F2 | 过期后重新绑定恢复 | 删除过期 + 重绑 → 权益恢复 | user5 凭证过期 | 1. user5 解绑过期身份<br>2. 重新添加同 BIN<br>3. 进入结算 | 同 BIN | 1. 绑定成功 + 新凭证 7 天<br>2. 后续结算正常命中 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-016 | Website / Member Benefits / Identity Binding | Medium | Medium | PRD §3.1 列表 / F5 | 解绑二次确认 | 防误操作 | user1 已绑甲钻石 | 1. 我的权益身份<br>2. 点击解绑 | - | 1. 弹「确认解绑？」对话框<br>2. 含取消和确认 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-017 | Website / Member Benefits / Identity Binding | High | Medium | PRD §3.1 / F5 | 解绑成功 | 确认后卡片移除 + UI 同步 | user1 已绑甲钻石 | 1. 解绑<br>2. 确认 | - | 1. 卡片消失<br>2. 成功 toast<br>3. 列表 -1 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-018 | Website / Member Benefits / Checkout | High | High | PRD §3.2 / F5+F6 | 解绑后不参与权益判定 | 解绑身份在结算时被忽略 | user1 已解绑甲钻石 | 1. user1 加入购物车 | - | 1. 不进入优先购<br>2. 普通价 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-019 | Website / Member Benefits / Checkout | High | High | PRD §3.2.1 / F6 | 命中优先购权益 | 绑定 + 窗口开 → 进入优先购模式 | user1 绑甲钻石；时间在公售前 20 分（窗口内 30 分） | 1. user1 进事件页<br>2. 选票档<br>3. 立即购买 | 时间窗口内 | 1. 进优先购模式<br>2. 显示「使用 甲钻石 优先购权益」<br>3. 可正常下单 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-020 | Website / Member Benefits / Checkout | High | Medium | PRD §3.2.1 / F6 | 提前时间窗口未开 | 有绑定但时间未到 → 普通价 | user1 绑甲钻石；当前在公售前 60 分（窗口外） | 1. 同上 | 窗口外 | 1. 不进优先购<br>2. 普通价<br>3. 不打断<br>4. 弱提示「公售前 30 分启用优先购」 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-021 | Website / Member Benefits / Checkout | High | Medium | PRD §3.2.1 / F6+F8 | 用户无任何绑定 | 普通价路径 | guest1 未绑定 | 1. guest1 购票 | - | 1. 普通价<br>2. 不打断<br>3. 弱提示「绑定身份可享优先购」 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-022 | Website / Member Benefits / Checkout | High | High | PRD §3.2.1 / F8 | 不命中场景不打断结算 | 全流程零阻塞 | 无绑定用户 | 1. 完整购票到支付 | - | 1. 0 弹窗中断<br>2. 弱提示不挡按钮<br>3. 支付正常完成 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-023 | Website / Member Benefits / Checkout | High | High | U-1 / F4+F6 | 加入购物车快照判定 | 加车后凭证过期不重判 | user1 凭证剩 2 分；时间窗口内 | 1. 加车（命中优先购）<br>2. 等 5 分（凭证过期）<br>3. 进入支付 | 临过期凭证 | 1. 加车时锁定优先购权益<br>2. 凭证过期不重判<br>3. 按优先购完成支付 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-024 | Website / Member Benefits / Checkout | High | High | Q-6 / F7 | 多命中取总价最低 | 多绑定同时命中 → 按最低总价 | user2 绑甲钻石(8 折)+甲白金(9 折)；均在窗口 | 1. user2 购票 | 原价 100；钻石 80；白金 90 | 1. 自动选甲钻石（80 最低）<br>2. 显示「使用 甲钻石」<br>3. 扣甲钻石次数 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-025 | Website / Member Benefits / Checkout | High | High | PRD §3.2.2 / F7 | 内部会员 + 合作方混合取最优 | VIP + 甲钻石 → 取更低 | user2 是 VIP(7 折) + 甲钻石(8 折) | 1. user2 购票 | VIP 70；甲钻石 80 | 1. 取 VIP（70 最低）<br>2. 不消耗甲钻石次数 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-026 | Website / Member Benefits / Checkout | Medium | Medium | PRD §3.2.2 / F7 | 多绑定全部不命中 | 时间不在任何窗口 → 普通价 | user2 多绑定；时间均窗口外 | 1. user2 购票 | - | 1. 普通价<br>2. 不消耗任何次数 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-027 | Website / Member Benefits / Checkout | High | Medium | PRD §3.2.2 / F7 | 多绑定中单一命中 | 仅 1 个在窗口 → 用该单一 | user2 绑甲钻石(窗口内) + 甲白金(窗口外) | 1. user2 购票 | 甲钻石 80；白金不可用 | 1. 用甲钻石<br>2. 价 80<br>3. 扣甲钻石次数 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-028 | Website / Member Benefits / Checkout | Medium | Low | PRD §3.2.1 / F8 | 弱提示样式不挡操作 | 弱提示展示形态 | 未绑定用户在有合作方优先购的事件页 | 1. 进事件详情 | - | 1. 顶部/侧边弱提示（toast/banner/小图标）<br>2. 不弹窗<br>3. 不挡购票按钮 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-029 | Website / Member Benefits / Checkout | High | Medium | PRD §3.2.1 / F8 | 弱提示全流程不阻塞 | 端到端不被打断 | 同上 | 1. 购票→订单→支付→成功 | - | 1. 每步弱提示存在但不阻塞<br>2. 成功页正常显示 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-030 | Website / Member Benefits / Quota | High | High | U-2 / F9 | 支付成功扣减次数 | 计数 -1 | 甲钻石总次数 5；user1 绑甲钻石 | 1. user1 优先购下单<br>2. 完成支付 | 初始 5 次 | 1. 支付成功后甲钻石次数 → 4<br>2. 后台计数同步 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-031 | Website / Member Benefits / Quota | High | High | U-2 / F9 | 支付失败不扣减 | 仅支付成功才扣 | 同上 | 1. 优先购下单<br>2. 支付失败/取消 | - | 1. 次数保持 5<br>2. 订单状态失败/取消<br>3. 用户可重试 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-032 | Website / Member Benefits / Quota | High | High | U-2 / F9 | 全额退款反转计数 | 退款 → 计数 +1 | user1 已用次数 -1（剩 4） | 1. 全额退款<br>2. 退款成功 | - | 1. 退款成功后次数恢复 5<br>2. 后台计数同步 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-033 | Website / Member Benefits / Quota | Medium | Medium | Q-7(a) / F9 | 部分退款时计数不反转 | 验证部分退款后优先购次数保持不变（权益已消费） | user1 已用次数 -1（剩 4） | 1. 部分退款（多张票退 1 张）<br>2. 退款审核通过<br>3. 查看用户优先购次数 | - | 1. 部分退款成功<br>2. 该用户的甲钻石优先购次数**保持 4 不变**<br>3. 全额退款行为不受影响（参考 BPP-032）<br>4. 后台计数与前端展示同步 | Antank QA Team |  |  |  |  |  | Q-7(a) 决策 2026-06-27：部分退款不反转 |  |
| SIT-TC-WEB-BPP-034 | Website / Member Benefits / Quota | High | Medium | PRD §3.2.2 / F9 | 连续多笔扣减 | 顺序累计正确 | 甲钻石初始 5 次 | 1. 优先购下单1+支付<br>2. 优先购下单2+支付<br>3. 优先购下单3+支付 | 3 次连续 | 1. 每次支付后扣减<br>2. 最终次数 2<br>3. 顺序正确 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-035 | Website / Member Benefits / Promotion Conflict | High | High | Q-5(b) / F10 | mid 一致时银行卡促销可叠加 | 优先购 mid=甲，促销 mid=甲 → 可选 | user1 优先购下单（甲钻石）；促销 X 配置 mid=甲 | 1. 优先购下单<br>2. 选支付方式（**此时 mid 绑定到订单** — Q-5(b)）<br>3. 进入促销选择器 | 优先购 mid=甲；促销 X mid=甲 | 1. 促销 X 可选<br>2. 选中后应用 promotion + 优先购权益叠加<br>3. 总价正确 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-036 | Website / Member Benefits / Promotion Conflict | Medium | Medium | PRD §3.2 / F10 | 多个 mid 一致促销 | 都可选 | 配置 2 个 mid=甲 的促销 | 1. 同上<br>2. 在选择器查看 | 促销 X, Y 均 mid=甲 | 1. 两个都可选<br>2. 按业务规则应用 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-037 | Website / Member Benefits / Promotion Conflict | High | High | Q-5(b) / F10 | mid 绑定时机联调验证 | 验证后端 mid 在「支付方式选择后」绑定到订单（按 Q-5(b)） | 完整优先购订单流程 | 1. 优先购下单成功<br>2. 进入订单确认页，查订单数据是否含 mid<br>3. 选择支付方式<br>4. 重新查订单数据<br>5. 进入促销选择器 | - | 1. 订单确认页：订单数据**不含** mid<br>2. 选支付方式后：订单数据**含** mid<br>3. 促销选择器读取该 mid 做匹配比较<br>4. 实际行为与 Q-5(b) 答复一致 | Antank QA Team |  |  |  |  |  | 联调验证用例：Q-5(b) 已签字 2026-06-26 v1，本用例确认后端实现位置 |  |
| SIT-TC-WEB-BPP-038 | Website / Member Benefits / Promotion Conflict | High | High | U-6 / F11 | mid 不一致促销禁用 | 优先购 mid=甲，促销 Z mid=乙 → 不可选 | user1 优先购下单（mid=甲）；促销 Z mid=乙 | 1. 优先购下单<br>2. 选支付方式<br>3. 进促销选择器 | 优先购 mid=甲；促销 Z mid=乙 | 1. 促销 Z 不可选（按 U-6 不验证 UI 文案）<br>2. 不阻塞其他可选促销 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-039 | Website / Member Benefits / Promotion Conflict | Medium | Medium | PRD §3.2 / F11 | 多 mid 不一致 | 多个非匹配 mid 均不可选 | 配置 mid=乙、mid=丙 多个促销 | 1. 同上 | 优先购 mid=甲；多个其他 mid 促销 | 1. 所有非 mid=甲 不可选<br>2. mid=甲 的可选 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-040 | Website / Member Benefits / i18n | Medium | Low | PRD §多语言 / F12 | zh-CN 渲染合作方/等级 | 基础多语言 | 后台录入甲合作方 zh-CN 译文 | 1. 用户语言切 zh-CN<br>2. 进入我的权益身份 | zh-CN = "合作方甲" | 1. 显示 "合作方甲 · 钻石"<br>2. 备注显示中文 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-041 | Website / Member Benefits / i18n | Medium | Low | PRD §多语言 / F12 | zh-HK 渲染 | 繁体显示 | 已录入 zh-HK 译文 | 1. 语言切 zh-HK | zh-HK = "合作方甲（繁）" | 1. 显示繁体名称<br>2. 备注繁体 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-042 | Website / Member Benefits / i18n | Medium | Low | PRD §多语言 / F12 | en 渲染 | 英文显示 | 已录入 en 译文 | 1. 语言切 en | en = "Partner A" / "Diamond" | 1. 显示 "Partner A · Diamond"<br>2. 备注英文 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-043 | Website / Member Benefits / i18n | Medium | Medium | Q-8(a) / F12 | 翻译缺失时 fallback 到 zh-CN | 验证合作方字段在目标语言译文缺失时回退到 zh-CN（平台主语言） | 合作方甲仅录 zh-CN 译文 | 1. 用户语言切到 en（或 zh-HK）<br>2. 进入我的权益身份<br>3. 检查卡片中合作方名称 / 等级 / 备注的展示 | 仅 zh-CN 译文 | 1. 卡片展示的合作方名称 fallback 到 zh-CN（如「合作方甲」）<br>2. 等级名称 fallback 到 zh-CN（如「钻石」）<br>3. 备注 fallback 到 zh-CN<br>4. 不显示英文 key 名 / 空白 / 报错 | Antank QA Team |  |  |  |  |  | Q-8(a) 决策 2026-06-27：fallback 到 zh-CN |  |
| SIT-TC-WEB-BPP-044 | Website / Member Benefits / E2E | High | High | F1-F9 集成 | 端到端：绑定→优先购→支付→扣减 | 完整链路 | guest1 未绑定；甲钻石窗口开 | 1. guest1 绑 BIN（命中甲钻石）<br>2. 进测试演出 → 优先购下单<br>3. 选支付方式<br>4. 完成支付<br>5. 查我的权益身份 | 完整链路 | 1. 绑定成功（凭证 7 天）<br>2. 优先购命中（价 80）<br>3. 支付成功<br>4. 计数 5 → 4<br>5. 我的权益身份显示该绑定 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-045 | Website / Member Benefits / E2E | High | High | F9 集成 E2E | 端到端：退款反转 | 全额退款后计数恢复 | 续 BPP-044，user 已支付，次数 4 | 1. 申请全额退款<br>2. 退款审核通过 | - | 1. 退款成功<br>2. 计数恢复 5<br>3. 订单状态退款<br>4. 我的权益身份不变 | Antank QA Team |  |  |  |  |  |  |  |

## [SECTION] 用例分组索引

- **F1 我的权益身份 列表** (BPP-001..004): 4 条 — 空状态 / 单卡 / 多卡 / 临期警告
- **F2 BIN 绑定** (BPP-005..009): 5 条 — 主流程 / 完整卡号校验(U-5) / 不命中 / 跨合作方冲突(U-4) / 取消
- **F3 API 绑定** (BPP-010..012): 3 条 — 主流程 / 失败 / 必填校验
- **F4 凭证过期** (BPP-013..015): 3 条 — 倒计时 / 过期忽略 / 重绑恢复
- **F5 解绑** (BPP-016..018): 3 条 — 二次确认 / 成功 / 解绑后不命中
- **F6 结算单权益判定** (BPP-019..023): 5 条 — 命中 / 窗口未开 / 无绑定 / 不打断 / 加车快照(U-1)
- **F7 多绑定取最优** (BPP-024..027): 4 条 — 总价最低(Q-6) / 内部+合作方混合 / 全部不命中 / 单命中
- **F8 非阻断** (BPP-028..029): 2 条 — 弱提示样式 / 全流程不打断
- **F9 计数扣减** (BPP-030..034): 5 条 — 支付成功扣 / 支付失败不扣 / 退款反转(U-2) / 部分退款不反转(Q-7) / 连续多笔
- **F10 mid 一致** (BPP-035..037): 3 条 — 单 mid 叠加(Q-5b) / 多 mid 一致 / mid 绑定时机联调验证(Q-5b)
- **F11 mid 不一致** (BPP-038..039): 2 条 — 禁用(U-6 不验证 UI 文案) / 多 mid 不一致
- **F12 多语言** (BPP-040..043): 4 条 — zh-CN / zh-HK / en / 翻译缺失 fallback zh-CN(Q-8)
- **E2E 综合** (BPP-044..045): 2 条 — 端到端正向 / 端到端退款

**总计：45 条**
- 优先级分布：High 26 / Medium 16 / Low 3
- 黄色待定：**0 条**（v2 后 Q-7/Q-8 决策已消化；BPP-037 重分类为联调验证）
