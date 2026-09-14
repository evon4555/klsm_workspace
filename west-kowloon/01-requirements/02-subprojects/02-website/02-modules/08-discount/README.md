# Discount and Member Benefits

Scope:

- partner-member identity system (合作方会员管理) with BIN / API verification
- BIN library management (BIN 库)
- priority-purchase configuration (优先购配置) referencing partner-member levels
- customer-facing "我的权益身份" identity binding in 个人中心
- checkout-time benefit auto-decision and bank-card priority-purchase vs bank-card discount conflict

Source baseline: 会员系统 v2.1 PRD (story-702, created 2026-05-28, rev 1.1
2026-06-11).

New module-specific changes should go directly under dated folders in this
module, for example `2026-06-25`.

Open: the folder slug is `08-discount`, but the active 2026-06-25 source covers
member-benefit infrastructure beyond plain discount (partner-member, BIN, and
priority-purchase). Rename pending product/user decision — see the
`2026-06-25/package.md` open questions.
