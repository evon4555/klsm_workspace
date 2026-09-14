# Project Context

## Project Identity

`standard product` is the baseline SaaS product workspace. It represents shared
product capabilities that customer projects can inherit and extend.

## Business Shape

The product is treated as a reusable admin and management platform. Customer
projects such as West Kowloon and Jockey Club should be evaluated as
project-specific extensions on top of this baseline unless a requirement says
otherwise.

## Scope Rules

- Product-wide behavior belongs here.
- Customer-specific behavior belongs in the relevant customer workspace.
- If a customer project reveals a reusable baseline rule, record it here only
  after the user confirms that it is product-wide.

## Context Usage Rules

Use context in this order:

1. Requirement package
2. Standard product context
3. Shared company context
4. Shared QA system

## Template Usage Rules

When generating standard-product requirement review, test-case review, or test
case workbook artifacts, first look for project-owned templates under:

`D:\Workspace\standard product\01-requirements\01-source-documents\02-templates`

If a required template exists there, it overrides same-purpose templates copied
from customer projects or generic qa-harness defaults. Historical package
artifacts are references only, not runtime templates.
