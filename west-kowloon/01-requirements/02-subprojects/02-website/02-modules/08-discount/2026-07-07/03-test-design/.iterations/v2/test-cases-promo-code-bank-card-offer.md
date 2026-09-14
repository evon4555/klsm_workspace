# Test Cases - Promo Code / Bank-card Offer Promotion

## [SECTION] Revision History

| Date | Author | Change | Status |
|---|---|---|---|
| 2026-07-07 | QA1 (AI) | Initial 20 SIT cases from signed requirement consolidation. | Done |
| 2026-07-07 | QA1 (AI) | Template correction: aligned Markdown with project TestCase_Template.xlsx by adding the Label column and regenerated the xlsx from a cloned template. Case scope and IDs unchanged. | Done |

## [SECTION] Scope Summary

- Feature: Bank-card offer/coupon promotion through promo code entry before CyberSource Checkout.
- Current design set: 20 SIT cases, aligned with the signed consolidation document.
- Signed scope: `../02-analysis/requirement-consolidation-promo-code-bank-card-offer.md`.
- Isolation rule: old `2026-06-25` bank-card priority-purchase cases are not modified by this package.
- Markdown mirrors the project TestCase_Template.xlsx columns; execution-result fields remain blank at design time.

## [SECTION] Test Cases

| Label | Test Case ID | Module/Feature | Priority | Severity | Collected from | Test Scenario | Test Case Description | Preconditions | Test Steps | Test Data | Expected Result | Test Case Owner | Environment | Execution Date | Executed By | Actual Result | Status | Comments/Remarks | Screenshots |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SIT | SIT-TC-WEB-BCO-001 | Website / Discount / Promo Code Bank-card Offer | High | Medium | Signed scope F7 / Q-8 | 订单确认页显示优惠码入口 | 验证用户选择票务商品后，在 Checkout 前可以看到优惠码录入入口并准备应用银行优惠券活动 | 票务项目已配置银行优惠券活动；CyberSource MID 测试数据已准备；用户已进入单场次票订单确认页 | 1. 选择支持优惠码的票务项目<br>2. 进入订单确认页<br>3. 检查 Checkout 按钮前的优惠码区域 | ticket_event_bank_offer_001 | 1. 显示一个优惠码/促销码输入入口<br>2. 入口位于 Checkout 前，用户可在付款前选择或输入优惠码<br>3. 未输入优惠码时订单仍可继续原价 Checkout | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-002 | Website / Discount / Promo Code Bank-card Offer | High | High | PRD chapter 1 context + Q-3/Q-8 | 有效优惠码被识别并计算折扣 | 验证有效 promo code 在订单确认页被识别后，系统在 Checkout 前展示并计算对应银行优惠 | 促销活动已关联有效 promo code 与 CyberSource MID；该票务订单满足活动条件 | 1. 在优惠码输入框输入有效 promo code<br>2. 点击确认/应用<br>3. 观察优惠明细和订单应付金额 | PROMO-MID-OK | 1. 优惠码校验成功<br>2. 优惠明细中显示对应银行优惠券活动<br>3. 订单应付金额按优惠后金额刷新<br>4. 该优惠处于当前订单待使用状态 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-003 | Website / Discount / Promo Code Bank-card Offer | High | Medium | PRD chapter 1 context / F8 | 无效优惠码统一失败提示 | 验证格式错误或不存在的优惠码不会影响订单金额，并按统一文案提示不可用 | 用户在订单确认页；订单未应用任何优惠码 | 1. 输入无效 promo code<br>2. 点击确认/应用<br>3. 观察输入框提示和订单金额 | BADCODE123 | 1. 显示「当前优惠码不可用」或等价统一失败提示<br>2. 订单金额不变化<br>3. 不会进入 CyberSource 支付校验<br>4. 用户可清空并重新输入 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-004 | Website / Discount / Promo Code Bank-card Offer | High | Medium | PRD chapter 1 context / F8 | 优惠码有效但当前订单不可用 | 验证 promo code 本身存在但不适用于当前票务订单时，不应用优惠且统一提示不可用 | 存在绑定其他活动/票务项目的有效 promo code；当前订单不满足该活动条件 | 1. 进入不适用该 promo code 的订单确认页<br>2. 输入该 promo code 并确认<br>3. 观察优惠状态和金额 | PROMO-OTHER-EVENT | 1. 显示「当前优惠码不可用」或等价统一失败提示<br>2. 不展示该银行优惠券活动为可用优惠<br>3. 订单应付金额保持不变 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-005 | Website / Discount / Promo Code Bank-card Offer | Medium | Medium | PRD chapter 1 context / Q-3 | 删除优惠码后可重新输入其他优惠码 | 验证用户删除已应用的 promo code 后，优惠金额刷新，并可继续输入另一个 promo code | 订单已成功应用一个有效 promo code | 1. 点击删除/移除当前优惠码<br>2. 观察订单金额<br>3. 输入另一个有效 promo code 并确认 | PROMO-MID-OK -> PROMO-MID-OK-2 | 1. 删除后原优惠不再生效，订单金额恢复或重新计算<br>2. 输入新 promo code 后仅新优惠码生效<br>3. 同一订单不会同时保留两个 promo code 优惠 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-006 | Website / Discount / Promo Code Bank-card Offer | Medium | Medium | PRD chapter 1 context | 同一订单最多一个优惠码优惠 | 验证同一笔订单不会同时应用多个 promo code 优惠 | 存在两个均可用于当前票务订单的 promo code | 1. 应用第一个 promo code<br>2. 尝试直接应用第二个 promo code<br>3. 观察优惠明细和应付金额 | PROMO-A, PROMO-B | 1. 系统不允许两个 promo code 同时处于生效状态<br>2. 如允许替换，则旧优惠被移除后新优惠生效<br>3. 优惠明细和应付金额只反映一个 promo code | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-007 | Website / Discount / CyberSource Checkout | High | High | Signed scope F7 / Q-6/Q-7/Q-8 | 带优惠金额发起 CyberSource Checkout | 验证用户应用 promo code 后点击 Checkout，系统以优惠后金额进入 CyberSource 支付流程 | 订单已应用有效 promo code；CyberSource 成功支付测试卡和 MID 已准备 | 1. 应用有效 promo code<br>2. 确认优惠后应付金额<br>3. 点击 Checkout<br>4. 进入 CyberSource 支付页或支付流程 | PROMO-MID-OK + CS-SUCCESS-CARD | 1. 跳转/发起 CyberSource Checkout 成功<br>2. 支付金额为优惠后金额<br>3. 支付请求或测试日志中使用预期商户/MID 测试配置<br>4. 网站不做额外 BIN/发卡行枚举校验 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-008 | Website / Discount / CyberSource Checkout | High | High | Signed scope F7 / Q-6/Q-7 | CyberSource 支付成功后订单成功 | 验证 MID/卡/支付网关测试配置匹配时，CyberSource 返回成功后订单按优惠后金额完成支付 | 有效 promo code 已应用；使用匹配 MID 的 CyberSource 成功测试卡 | 1. 点击 Checkout 进入 CyberSource<br>2. 使用成功测试卡完成支付<br>3. 返回网站<br>4. 查看订单状态和金额 | CS-SUCCESS-CARD / matched MID | 1. CyberSource 返回成功<br>2. 网站订单状态为已支付/支付成功<br>3. 订单支付金额等于优惠后金额<br>4. 订单详情保留 promo code/优惠活动记录 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-009 | Website / Discount / CyberSource Checkout | High | High | Signed scope F8 / Q-6/Q-7 | MID/卡/支付网关不匹配导致支付失败 | 验证 MID 与卡或支付网关配置不匹配时，系统以 CyberSource 支付失败结果为准，不误判为成功 | 有效 promo code 已应用；准备不匹配 MID 或失败测试卡 | 1. 点击 Checkout 进入 CyberSource<br>2. 使用不匹配或失败测试卡支付<br>3. 返回网站<br>4. 查看订单状态 | CS-MID-MISMATCH-CARD / unmatched MID | 1. CyberSource 返回失败或非成功结果<br>2. 网站订单不进入已支付状态<br>3. 不生成成功支付票券<br>4. 用户可重新支付或返回修改优惠码 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-010 | Website / Discount / CyberSource Checkout | Medium | High | Signed scope F8 / Q-6 | CyberSource 取消或超时返回 | 验证用户在 CyberSource 中取消支付或支付超时时，网站不会把订单标记为支付成功 | 订单已应用有效 promo code 并已发起 Checkout | 1. 进入 CyberSource 支付流程<br>2. 取消支付或触发超时<br>3. 返回网站或等待回调<br>4. 查看订单状态 | CS-CANCEL or timeout simulation | 1. 订单保持待支付/支付失败/取消状态之一<br>2. 不发放票券<br>3. 优惠码记录不会产生成功支付效果<br>4. 用户仍可重新进入支付流程 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-011 | Website / Discount / Test Data Dependency | Medium | Medium | Q-2 / F8 | 支付网关测试数据未准备时不执行正向结论 | 验证当 CyberSource MID/网关测试数据缺失时，本包用例不应得出网站功能失败以外的业务结论 | 测试环境缺失对应 MID 或 CyberSource 网关映射 | 1. 应用有效 promo code<br>2. 点击 Checkout<br>3. 观察支付发起或返回结果 | missing MID / gateway mapping | 1. 测试记录标明为测试数据/环境阻塞或支付失败路径<br>2. 不把第三方配置缺失误判为网站优惠码识别失败<br>3. 订单不会被误置为支付成功 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-012 | Website / Discount / Payment Path | Medium | Medium | Q-7 | 非 CyberSource 支付路径不纳入本轮正向覆盖 | 验证本轮银行优惠券活动只按 CyberSource 路径覆盖，其他支付方式不作为正向成功条件 | 测试环境存在非 CyberSource 支付方式，或产品配置隐藏其他方式 | 1. 应用有效 promo code<br>2. 检查可选支付方式<br>3. 如可选择非 CyberSource，尝试进入该支付路径 | non-CyberSource payment method | 1. 正向成功用例只以 CyberSource 为准<br>2. 非 CyberSource 不作为银行优惠券活动成功路径<br>3. 如系统隐藏其他支付方式，则记录为符合本轮范围 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-013 | Website / Discount / Ticket Scope | Medium | Medium | PRD background | 仅票务订单可使用本促销 | 验证该银行优惠券活动仅支持票务促销，不适用于非票务商品订单 | 存在非票务商品或非票务订单入口；同一 promo code 已配置为票务促销 | 1. 进入非票务商品/订单确认页<br>2. 输入票务 promo code<br>3. 观察校验结果和金额 | PROMO-MID-OK on non-ticket order | 1. 非票务订单不应用该优惠<br>2. 金额保持不变<br>3. 提示当前优惠码不可用或不展示该入口，按实际 UI 记录 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-014 | Website / Discount / Coexistence Smoke | Medium | Medium | Q-5(c) / F9 | 后端配置允许叠加时的轻量同享检查 | 验证当后端配置允许 bank-card offer 与另一种优惠同享时，网站可按配置展示并计算优惠，不展开全组合矩阵 | 后端测试数据配置 bank-card offer 可与一个指定普通/会员优惠同享 | 1. 使订单先命中另一种优惠<br>2. 输入 bank-card offer promo code<br>3. 观察优惠明细和应付金额 | PROMO-STACK-YES | 1. 两个优惠可同时展示/计算，符合后端配置<br>2. 金额计算正确<br>3. 测试仅覆盖一个 smoke 组合，不枚举全部组合 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-015 | Website / Discount / Coexistence Smoke | Medium | Medium | Q-5(c) / F9 | 后端配置不允许叠加时的轻量互斥检查 | 验证当后端配置不允许 bank-card offer 与另一种优惠同享时，网站不会同时应用两个优惠 | 后端测试数据配置 bank-card offer 不可与一个指定优惠同享 | 1. 使订单先命中另一种优惠<br>2. 输入 bank-card offer promo code<br>3. 观察优惠选择状态和金额 | PROMO-STACK-NO | 1. 不会同时应用两个互斥优惠<br>2. 用户可看到不可同享提示或不可选状态，按实际 UI 记录<br>3. 金额只反映最终生效优惠 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-016 | Website / Discount / Regression Smoke | Medium | Medium | Q-1/Q-4 | 不输入 promo code 时购票支付不受影响 | 验证新优惠码入口存在时，不输入 promo code 的普通购票 Checkout 流程不被阻塞 | 票务项目支持银行优惠券活动；用户不输入任何 promo code | 1. 进入订单确认页<br>2. 不输入 promo code<br>3. 点击 Checkout<br>4. 完成普通 CyberSource 支付或进入支付流程 | no promo code | 1. 用户可继续 Checkout<br>2. 订单按未优惠金额支付<br>3. 不影响普通购票主流程 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-017 | Website / Discount / BPP Isolation Smoke | Medium | Medium | Q-1/Q-4/U-7 | 旧银行优先购流程不因本包被改写 | 验证在不使用本包 promo code 的情况下，既有银行优先购基础流程仍由旧包覆盖，本包只做轻量隔离检查 | 存在已配置的 2026-06-25 BPP 测试用户和优先购活动；本订单不输入 bank-card offer promo code | 1. 使用 BPP 用户进入优先购场景<br>2. 不输入本包 promo code<br>3. 继续原优先购购票流程 | existing BPP user + no BCO promo code | 1. 旧 BPP 主流程不被本包入口阻塞<br>2. 不修改旧 BPP 用例断言<br>3. 如发现差异，另按旧包 CHANGE 规则处理 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-018 | Website / Discount / Amount Integrity | High | High | Q-8 / F7 | 优惠后金额与支付金额一致 | 验证网站优惠计算金额、Checkout 金额、支付成功订单金额三者一致 | 有效 promo code 已应用并完成 CyberSource 成功支付 | 1. 记录优惠前金额、优惠金额、优惠后应付金额<br>2. 点击 Checkout 并完成支付<br>3. 查看支付返回和订单详情金额 | PROMO-MID-OK + CS-SUCCESS-CARD | 1. Checkout 金额等于订单确认页优惠后金额<br>2. 支付成功订单金额一致<br>3. 不存在原价支付但页面显示优惠的情况 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-019 | Website / Discount / Retry Path | Medium | Medium | F8 / Q-6 | 支付失败后可重试或修改优惠码 | 验证 CyberSource 支付失败返回后，用户仍可重新支付或回到订单确认页修改 promo code | 订单已应用 promo code，并使用失败测试卡完成一次失败支付 | 1. 触发一次 CyberSource 支付失败<br>2. 返回订单或失败页<br>3. 尝试重新支付或修改 promo code | CS-FAIL-CARD | 1. 订单保持未支付/失败状态<br>2. 用户可重新发起支付或返回修改优惠码<br>3. 不会重复生成成功订单或票券 | Antank QA Team |  |  |  |  |  |  |  |
| SIT | SIT-TC-WEB-BCO-020 | Website / Discount / Traceability | Medium | Medium | F7/F8 / Q-6 | 订单详情保留优惠码与支付结果可追溯信息 | 验证支付完成后订单详情或后台可追溯 promo code、优惠金额和 CyberSource 返回结果 | 订单使用 promo code 并完成一次成功或失败支付 | 1. 完成一笔成功支付或失败支付<br>2. 打开订单详情或可用后台查询页<br>3. 核对优惠码、优惠金额、支付结果记录 | PROMO-MID-OK + success/fail return code | 1. 记录 promo code/活动标识<br>2. 记录优惠金额或未生效原因<br>3. 记录 CyberSource 成功/失败返回结果<br>4. 便于后续缺陷定位和证据提交 | Antank QA Team |  |  |  |  |  |  |  |

## [SECTION] Coverage Notes

- Promo-code entry and recognition: BCO-001..006
- CyberSource Checkout success/failure: BCO-007..012, BCO-018..019
- Ticket-only and coexistence smoke: BCO-013..015
- Regression/isolation: BCO-016..017
- Traceability/evidence: BCO-020

## [SECTION] Open Questions

None for this signed 20-case design set. Figma-specific visual cases can be added later if the UI source becomes available.
