# Test Cases - Bank-card Priority Purchase / 银行卡优先购

## [SECTION] Scope Summary

- Feature: Bank-card priority purchase with member-benefit identity binding.
- Current design set: 29 SIT cases, aligned with the latest Chinese workbook.
- English companion workbook: `en/test-cases-bank-card-priority-purchase.xlsx`.
- Description wording standard: Chinese descriptions start with `验证`; English descriptions start with `Verify`.
- Execution columns are intentionally left to the workbook; this Markdown mirrors the test-design content.

## [SECTION] Test Cases

| Test Case ID | Module/Feature | Priority | Severity | Collected from | Test Scenario | Test Case Description | Preconditions | Test Steps | Test Data | Expected Result | Test Case Owner | Environment | Execution Date | Executed By | Actual Result | Status | Comments/Remarks | Screenshots |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SIT-TC-WEB-BPP-001 | Website / Member Benefits / Identity Binding | Medium | Low | PRD §3.1 列表 / F1 | 未绑定用户访问我的权益身份 | 验证未绑定用户访问我的权益身份场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | guest1 已登录，无任何绑定 | 1. 登录 guest1@test.com<br>2. 进入个人中心 → 我的权益身份 | guest1 | 1. 页面加载成功<br>2. 显示空状态文案<br>3. 显示「+ 添加新身份」按钮 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-002 | Website / Member Benefits / Identity Binding | High | Medium | PRD §3.1 列表 / F1 | 已绑定 1 张身份的展示 | 验证已绑定 1 张身份的展示场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | user1 已绑定甲钻石，凭证剩 7 天 | 1. 登录 user1@test.com<br>2. 进入我的权益身份 | user1 | 1. 显示 1 张卡片<br>2. 含 合作方甲·钻石 + BIN 校验标签 + 「凭证 7 天后失效」 + 绑定时间 + 解绑按钮 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-003 | Website / Member Benefits / Identity Binding | Medium | Medium | PRD §3.1 列表 / F1 | 已绑定多张身份的展示 | 验证已绑定多张身份的展示场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | user2 已绑定甲钻石 + 甲白金 + 丙普通 | 1. 登录 user2@test.com<br>2. 进入我的权益身份 | user2，3 张绑定 | 1. 显示 3 张卡片<br>2. 按绑定时间倒序<br>3. 每张完整展示 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-004 | Website / Member Benefits / Identity Binding | Medium | Medium | PRD §3.1 / F1+F4 | 凭证即将过期的视觉提示 | 验证凭证即将过期的视觉提示场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | user1 的甲钻石凭证剩 2 天 | 1. 登录 user1<br>2. 进入我的权益身份 | 凭证剩 2 天 | 1. 显示「凭证 2 天后失效」<br>2. 文案颜色变化（橙/红） | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-005 | Website / Member Benefits / Identity Binding | High | High | PRD §3.1 绑定 / F2 | BIN 绑定主流程 | 验证 BIN 绑定主流程场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | 该卡未绑定 | 1. 添加新身份<br>2. 选合作方甲<br>3. 输入 4111-1111-1111-1111<br>4. 提交 | 4111-1111-1111-1111 | 1. 绑定成功 <br>2. 列表新增甲钻石<br>3. 凭证 7 天<br>4. 绑定时间为当前 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-006 | Website / Member Benefits / Identity Binding | High | Medium | U-5 / F2 | BIN 绑定要求完整卡号 | 验证 BIN 绑定要求完整卡号场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | 在 BIN 绑定表单 | 1. 选合作方甲<br>2. 输入 411111（仅 6 位）<br>3. 失焦或提交 | 411111 | 1. 提交按钮禁用 或 行内提示「请输入完整卡号」<br>2. 不发起后端校验 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-007 | Website / Member Benefits / Identity Binding | High | High | PRD §3.1 / F2 | BIN 不命中失败处理 | 验证 BIN 不命中失败处理场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | 同上 | 1. 选合作方甲<br>2. 输入 9999-9999-9999-9999<br>3. 提交 | 9999-9999-9999-9999 | 1. 显示「未匹配到 BIN」<br>2. 表单保留<br>3. 可重输入重试 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-008 | Website / Member Benefits / Identity Binding | High | High | U-4 / F2 | 跨合作方 BIN 冲突默认第一个 | 验证跨合作方 BIN 冲突默认第一个场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | 4111- 在甲和乙下均配置 | 1. 添加新身份<br>2. 选合作方甲<br>3. 输入 4111-1111-1111-1111 | 4111-1111-1111-1111 (双方命中) | 1. 仅绑甲钻石（按列表第一个）<br>2. 不弹选择对话框<br>3. 单绑定成功 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-009 | Website / Member Benefits / Identity Binding | Medium | Low | PRD §1.1.2.2 / F4 | 凭证倒计时正确 | 验证凭证倒计时正确场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | user1 凭证剩 5 天 | 1. 登录 user1<br>2. 进入我的权益身份 | 凭证 5 天 | 1. 显示「凭证 5 天后失效」<br>2. 数字按当前时间动态 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-010 | Website / Member Benefits / Identity Binding | Medium | Medium | PRD §3.1 / F4+F2 | 过期后重新绑定恢复 | 验证过期后重新绑定恢复场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | user5 凭证过期 | 1. user5 解绑过期身份<br>2. 重新添加同 BIN<br>3. 进入结算 | 同 BIN | 1. 绑定成功 + 新凭证 7 天<br>2. 后续结算正常命中 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-011 | Website / Member Benefits / Identity Binding | Medium | Medium | PRD §3.1 列表 / F5 | 解绑二次确认 | 验证解绑二次确认场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | user1 已绑甲钻石 | 1. 我的权益身份<br>2. 点击解绑 | - | 1. 弹「确认解绑？」对话框<br>2. 含取消和确认 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-012 | Website / Member Benefits / Identity Binding | High | Medium | PRD §3.1 / F5 | 解绑成功 | 验证解绑成功场景下，身份绑定状态、卡片信息和操作反馈符合业务规则 | user1 已绑甲钻石 | 1. 解绑<br>2. 确认 | - | 1. 卡片消失<br>2. 列表 -1 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-013 | Website / Member Benefits / Checkout | High | High | PRD §3.2.1 / F6 | 命中优先购权益 | 验证命中优先购权益场景下，优先购命中判定、价格模式和结算流程符合业务规则 | user1 绑甲钻石；时间在公售前 20 分（窗口内 30 分） | 1. user1 进事件页<br>2. 选票档<br>3. 立即购买 | 时间窗口内 | 1. 进优先购模式<br>2. 可正常下单 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-014 | Website / Member Benefits / Checkout | High | Medium | PRD §3.2.1 / F6 | 提前时间窗口未开 | 验证提前时间窗口未开场景下，优先购命中判定、价格模式和结算流程符合业务规则 | user1 绑甲钻石；当前在公售前 60 分（窗口外） | 1. 同上 | 窗口外 | 1. 不进优先购<br>2. 显示开票倒计时<br>4. 显示优先购倒计时 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-015 | Website / Member Benefits / Checkout | High | High | U-1 / F4+F6 | 加入购物车快照判定 | 验证加入购物车快照判定场景下，优先购命中判定、价格模式和结算流程符合业务规则 | user1 凭证剩 2 分；时间窗口内 | 1. 加车（命中优先购）<br>2. 等 5 分（凭证过期）<br>3. 进入支付 | 临过期凭证 | 1. 加车时锁定优先购权益<br>2. 凭证过期不重判<br>3. 按优先购完成支付 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-016 | Website / Member Benefits / Checkout | High | Medium | PRD §3.2.2 / F7 | 多绑定中单一命中 | 验证多绑定中单一命中场景下，优先购命中判定、价格模式和结算流程符合业务规则 | user2 绑甲钻石(窗口内) + 甲白金(窗口外) | 1. user2 购票 | 甲钻石窗口内；甲白金窗口外 | <br>1. 扣甲钻石次数 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-017 | Website / Member Benefits / Quota | High | High | U-2 / F9 | 支付成功扣减次数 | 验证支付成功扣减次数场景下，优先购次数扣减、还原和前后端同步结果符合业务规则 | 甲钻石总次数 5；user1 绑甲钻石 | 1. user1 优先购下单<br>2. 完成支付 | 初始 5 次 | 1. 支付成功后甲钻石次数 → 4<br>2. 后台计数同步 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-018 | Website / Member Benefits / Quota | High | High | U-2 / F9 | 支付失败不扣减 | 验证支付失败不扣减场景下，优先购次数扣减、还原和前后端同步结果符合业务规则 | user1 已命中甲钻石优先购并创建待支付订单 | 1. 优先购下单<br>2. 支付失败/取消 | - | 1. 次数保持 5<br>2. 订单状态失败/取消<br>3. 用户可重试 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-019 | Website / Member Benefits / Quota | High | High | U-2 / F9 | 全额退款反转计数 | 验证全额退款反转计数场景下，优先购次数扣减、还原和前后端同步结果符合业务规则 | user1 已用次数 -1（剩 4） | 1. 全额退款<br>2. 退款成功 | - | 1. 退款成功后次数恢复 5<br>2. 后台计数同步 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-020 | Website / Member Benefits / Quota | Medium | Medium | Q-7(a) / F9 | 部分退款时计数不反转 | 验证部分退款时计数不反转场景下，优先购次数扣减、还原和前后端同步结果符合业务规则 | user1 已用次数 -1（剩 4） | 1. 部分退款（多张票退 1 张）<br>2. 退款审核通过<br>3. 查看用户优先购次数 | - | 1. 部分退款成功<br>2. 该用户的甲钻石优先购次数**保持 4 不变**<br>3. 全额退款行为不受影响（参考 BPP-032）<br>4. 后台计数与前端展示同步 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-021 | Website / Member Benefits / Quota | High | Medium | PRD §3.2.2 / F9 | 连续多笔扣减 | 验证连续多笔扣减场景下，优先购次数扣减、还原和前后端同步结果符合业务规则 | 甲钻石初始 5 次 | 1. 优先购下单1+支付<br>2. 优先购下单2+支付<br>3. 优先购下单3+支付 | 3 次连续 | 1. 每次支付后扣减<br>2. 最终次数 2<br>3. 顺序正确 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-022 | Website / Member Benefits / i18n | Medium | Low | PRD §多语言 / F12 | zh-CN 渲染合作方/等级 | 验证 zh-CN 渲染合作方/等级场景下，合作方、等级和备注字段的多语言展示符合配置 | 后台录入甲合作方 zh-CN 译文 | 1. 用户语言切 zh-CN<br>2. 进入我的权益身份 | zh-CN = "合作方甲" | 1. 显示 "合作方甲 · 钻石"<br>2. 备注显示中文 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-023 | Website / Member Benefits / i18n | Medium | Low | PRD §多语言 / F12 | zh-HK 渲染 | 验证 zh-HK 渲染场景下，合作方、等级和备注字段的多语言展示符合配置 | 已录入 zh-HK 译文 | 1. 语言切 zh-HK | zh-HK = "合作方甲（繁）" | 1. 显示繁体名称<br>2. 备注繁体 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-024 | Website / Member Benefits / i18n | Medium | Low | PRD §多语言 / F12 | en 渲染 | 验证 en 渲染场景下，合作方、等级和备注字段的多语言展示符合配置 | 已录入 en 译文 | 1. 语言切 en | en = "Partner A" / "Diamond" | 1. 显示 "Partner A · Diamond"<br>2. 备注英文 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-025 | Website / Member Benefits / E2E | High | High | Q-5(a) / F9 | 银行卡优先购次数=0时，效果等同于正常购票 | 验证银行卡优先购次数为 0 时，系统降级为普通购票且不阻塞结算流程 | 次数=1 | 1. 购票（优先购一次）<br>2. 继续购票 | 甲钻石剩余次数 = 0；时间在窗口内 | 1. 成功购票<br>2. 无法成功购票  （显示正常倒计时） | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-026 | Website / Member Benefits / Checkout | High | High | F6 / E2E | 端到端银行卡优先购加入购物车 - 门票 | 验证银行卡优先购门票加入购物车、结账和支付链路符合预期 | guest1 已绑定甲钻石；门票项目在优先购窗口内 | 1. 购买门票（优先购)<br>2. 加入购物车<br>3. 结账支付<br> | 门票；甲钻石优先购权益 | 1.成功加入购物车 -门票<br>2. 成功付款 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-027 | Website / Member Benefits / Checkout | High | High | F6 / E2E | 端到端银行卡优先购加入购物车 - 座票 | 验证银行卡优先购座票加入购物车、结账和支付链路符合预期 | guest1 已绑定甲钻石；座票项目在优先购窗口内 | 1. 购买座票（优先购)<br>2. 加入购物车<br>3. 结账支付<br> | 座票；甲钻石优先购权益 | 1.成功加入购物车 -座票<br>2. 成功付款 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-028 | Website / Member Benefits / E2E | High | High | F1-F9 集成 | 端到端：绑定→优先购→支付→扣减 -> 退票 ->次数还原   （门票） | 验证银行卡优先购门票从绑定到退款后次数还原的端到端链路符合预期 | guest1 未绑定；甲钻石窗口已开；门票支持退款 | 1. 购买门票（优先购）<br>2. 退票 | 门票；4111-1111-1111-1111；初始次数 5 | 1. 绑定成功<br>2. 优先购命中<br>3. 支付成功<br>4. 计数 5 → 4<br>5. 退票成功<br>6. 计数 4 → 5 | Antank QA Team |  |  |  |  |  |  |  |
| SIT-TC-WEB-BPP-029 | Website / Member Benefits / E2E | High | High | F1-F9 集成 | 端到端：绑定→优先购→支付→扣减 -> 退票 ->次数还原   （座票） | 验证银行卡优先购座票从绑定到退款后次数还原的端到端链路符合预期 | guest1 未绑定；甲钻石窗口已开；座票支持退款 | 1. 购买座票（优先购）<br>2. 退票 | 座票；4111-1111-1111-1111；初始次数 5 | 1. 绑定成功<br>2. 优先购命中<br>3. 支付成功<br>4. 计数 5 → 4<br>5. 退票成功<br>6. 计数 4 → 5 | Antank QA Team |  |  |  |  |  |  |  |

## [SECTION] Coverage Notes

- Identity binding: BPP-001..012
- Checkout and priority-purchase decisioning: BPP-013..016, BPP-025..027
- Quota deduction/refund behavior: BPP-017..021
- Multilingual display: BPP-022..024
- End-to-end refund restoration: BPP-028..029

## [SECTION] Open Questions

None for this 29-case design set.
