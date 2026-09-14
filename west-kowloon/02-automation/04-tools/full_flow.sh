#!/bin/bash
# ---------------------------------------------------------------------------
# full_flow.sh — End-to-end smoke script for the Antank ticketing system.
#
# This script exercises the complete program creation flow via raw curl calls:
#   Step 1: Create a new program (项目)       → extracts PROGRAM_ID
#   Step 2: Add a ticket type (票价)          → extracts TICKET_ID
#   Step 3: Save the sales rules (销售规则)   → confirms success
#
# Usage:
#   export COOKIES='fctkid=...; Authorization=...; ukeyage=...'
#   bash full_flow.sh
#
# Prerequisites:
#   - A valid session cookie in the COOKIES environment variable.
#     Obtain it by logging in via the browser (DevTools → Application → Cookies)
#     and paste the three values: fctkid, Authorization, ukeyage.
#
# Note: This script is a quick manual smoke-test helper.
#       For automated regression, use the Behave feature:
#         behave 01-features/antank_email_login.feature
# ---------------------------------------------------------------------------

# Session cookies — replace with your own after logging in.
: "${COOKIES:?Set COOKIES with the current browser session cookie before running full_flow.sh}"

# Timestamp used as a unique suffix so test data names do not collide across runs.
TS=$(date +%Y%m%d%H%M%S)

# =========================================
# 步骤1: 新建项目 (Create new program)
# =========================================
echo "步骤1: 新建项目..."
STEP1=$(curl -s -X POST "https://anticket.lengliwh.com/theatre/home/program/op/save.xhtml" \
  -H "accept: application/json, text/plain, */*" \
  -H "accept-language: zh-CN,zh;q=0.9" \
  -H "lang: zh-CN" \
  -H "origin: https://anticket.lengliwh.com" \
  -H "referer: https://anticket.lengliwh.com/menpiao/index.html" \
  -H "routerpath: menpiao:/menpiao/programs" \
  -H "sec-fetch-dest: empty" \
  -H "sec-fetch-mode: cors" \
  -H "sec-fetch-site: same-origin" \
  -H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Content-Type: application/x-www-form-urlencoded;charset=UTF-8" \
  -b "$COOKIES" \
  --data-urlencode "defaultLang=en" \
  --data-urlencode "supportLang=en" \
  --data-urlencode "cnName=test no seat project${TS}" \
  --data-urlencode "briefName=${TS}" \
  --data-urlencode "stadiumId=69844" \
  --data-urlencode "venueId=1708" \
  --data-urlencode "durationType=period" \
  --data-urlencode "startTime=2026-03-18 00:00:00" \
  --data-urlencode "endTime=2026-03-18 23:59:59" \
  --data-urlencode "minPrice=0" \
  --data-urlencode "maxPrice=1" \
  --data-urlencode "showMode=calendar" \
  --data-urlencode "category=" \
  --data-urlencode "smallCategory=" \
  --data-urlencode "saleType=sale" \
  --data-urlencode "tag=" \
  --data-urlencode "approvalNum=" \
  --data-urlencode "multiGroupCheck=N" \
  --data-urlencode "allowInvoice=N" \
  --data-urlencode "pushInvoice=N" \
  --data-urlencode "programCode=" \
  --data-urlencode "available=Y" \
  --data-urlencode "supportSeat=N" \
  --data-urlencode "consumerInvoiceTime=paid" \
  --data-urlencode "bizScenario=program" \
  --data-urlencode "certLevel=" \
  --data-urlencode "blackLimit=Y" \
  --data-urlencode "productType=")

# Parse the program ID from the JSON response, e.g. {"program":{"id":12345,...}}
PROGRAM_ID=$(echo "$STEP1" | grep -o '"program":{[^}]*"id":[0-9]*' | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
if [ -z "$PROGRAM_ID" ]; then
  echo "FAILED step1: $STEP1"
  exit 1
fi
echo "OK | programId=$PROGRAM_ID | cnName=test no seat project${TS}"

# =========================================
# 步骤2: 新增票价 (Add ticket type / price)
# =========================================
echo ""
echo "步骤2: 新增票价..."
STEP2=$(curl -s -X POST "https://anticket.lengliwh.com/theatre/home/tickettype/op/save.xhtml" \
  -H "accept: application/json, text/plain, */*" \
  -H "accept-language: zh-CN,zh;q=0.9" \
  -H "lang: zh-CN" \
  -H "origin: https://anticket.lengliwh.com" \
  -H "referer: https://anticket.lengliwh.com/menpiao/index.html" \
  -H "routerpath: menpiao:/menpiao/programs" \
  -H "sec-fetch-dest: empty" \
  -H "sec-fetch-mode: cors" \
  -H "sec-fetch-site: same-origin" \
  -H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Content-Type: application/x-www-form-urlencoded;charset=UTF-8" \
  -b "$COOKIES" \
  --data-urlencode "cnName=test ticket type ${TS}" \
  --data-urlencode "briefName=" \
  --data-urlencode "status=N" \
  --data-urlencode "ticketType=normal" \
  --data-urlencode "layoutId=" \
  --data-urlencode "price=0.01" \
  --data-urlencode "settlePrice=" \
  --data-urlencode "channelPrice=" \
  --data-urlencode "opentime=" \
  --data-urlencode "closetime=" \
  --data-urlencode "discountType=normal" \
  --data-urlencode "priceLimitId=" \
  --data-urlencode "ticketTierId=7" \
  --data-urlencode "code=${TS}" \
  --data-urlencode "category=visitor" \
  --data-urlencode "supportRefund=Y" \
  --data-urlencode "sortNum=0" \
  --data-urlencode "remark=" \
  --data-urlencode "description=" \
  --data-urlencode "unionFlag=" \
  --data-urlencode "checkpreset=0" \
  --data-urlencode "checkexpand=0" \
  --data-urlencode "supportDay=workday,holiday,weekend" \
  --data-urlencode "entrynum=1" \
  --data-urlencode "givePoint=0" \
  --data-urlencode "supportExchange=N" \
  --data-urlencode "unitnum=1" \
  --data-urlencode "checkStartTime=00:00:00" \
  --data-urlencode "checkEndTime=23:59:59" \
  --data-urlencode "multiDay=N" \
  --data-urlencode "minBuyNum=0" \
  --data-urlencode "recheckNum=0" \
  --data-urlencode "dayRange=" \
  --data-urlencode "supportMachine=N" \
  --data-urlencode "checkConfirm=N" \
  --data-urlencode "confirmMsg=" \
  --data-urlencode "otherinfo=" \
  --data-urlencode "showTicketVerifications=[]" \
  --data-urlencode "depositPlanId=" \
  --data-urlencode "refundPlanId=" \
  --data-urlencode "firstCategory=" \
  --data-urlencode "secondCategory=" \
  --data-urlencode "firstCategoryId=" \
  --data-urlencode "secondCategoryId=" \
  --data-urlencode "pictures=" \
  --data-urlencode "dynamicValue=" \
  --data-urlencode "combinationPackageReq=" \
  --data-urlencode "combinationPackage=N" \
  --data-urlencode "programId=${PROGRAM_ID}")   # link this ticket type to the program created in step 1

# Parse the ticket type ID from the JSON response, e.g. {"id":67890,...}
TICKET_ID=$(echo "$STEP2" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ -z "$TICKET_ID" ]; then
  echo "FAILED step2: $STEP2"
  exit 1
fi
echo "OK | ticketTypeId=$TICKET_ID | cnName=test ticket type ${TS} | price=0.01"

# =========================================
# 步骤3: 保存销售规则 (Save sales rules)
# =========================================
echo ""
echo "步骤3: 保存销售规则..."

# The sales rules payload is a JSON object referencing the program created in step 1.
# Key fields:
#   openSaleTimeRule  — when tickets go on sale (relative to show start)
#   closeSaleTimeRule — when ticket sales close
#   openShowDefaultRule — purchase limits, eTicket format, transfer rules
REQ_JSON='{"programId":"'${PROGRAM_ID}'","openSaleTimeRule":{"relativeType":"relativeTime","beforePlayTime":"Y","minutes":0,"days":"","time":"","absTime":null,"beforePlayTime1":""},"closeSaleTimeRule":{"relativeType":"relativeTime","beforePlayTime":"N","beforePlayTime1":"","beforePlayTime2":"N","minutes":0,"days":"","time":"","absTime":null},"internalOpenSaleTimeRule":{"relativeType":"relativeTime","beforePlayTime":"Y","minutes":0,"days":"","time":"","absTime":null,"beforePlayTime1":""},"internalCloseSaleTimeRule":{"relativeType":"relativeTime","beforePlayTime":"N","beforePlayTime1":"","beforePlayTime2":"N","minutes":0,"days":"","time":"","absTime":null},"openShowDefaultRule":{"fixed":"Y","showCalendar":"Y","checkcard":"N","unionFlag":"","unionFlagArr":[],"maxBuyLimit":88,"maxBuyPerMember":88,"checkType":"eTicket","takeType":"eTicket","transfer":"Y","supportReserve":"Y","advanceMin":"0","display":"Y","advanceSendMin":0,"supportDynamicCode":"N","supportRefundPlan":"N","supportDeposit":"N"},"status":"N"}'

STEP3=$(curl -s -X POST "https://anticket.lengliwh.com/theatre/home/program/show/sale/rule/save.xhtml" \
  -H "accept: application/json, text/plain, */*" \
  -H "accept-language: zh-CN,zh;q=0.9" \
  -H "lang: zh-CN" \
  -H "origin: https://anticket.lengliwh.com" \
  -H "referer: https://anticket.lengliwh.com/menpiao/index.html" \
  -H "routerpath: menpiao:/menpiao/detail/rules" \
  -H "parentpath: menpiao:/menpiao/timeInventory" \
  -H "sec-fetch-dest: empty" \
  -H "sec-fetch-mode: cors" \
  -H "sec-fetch-site: same-origin" \
  -H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Content-Type: application/x-www-form-urlencoded;charset=UTF-8" \
  -b "$COOKIES" \
  --data-urlencode "req=${REQ_JSON}")

# Check that the response contains "success":true
if ! echo "$STEP3" | grep -q '"success":true'; then
  echo "FAILED step3: $STEP3"
  exit 1
fi
echo "OK | 销售规则保存成功"

echo ""
echo "========================================="
echo "全流程完成 (Full flow completed)"
echo "  项目ID (programId):      $PROGRAM_ID"
echo "  票价ID (ticketTypeId):   $TICKET_ID"
echo "  时间戳 (timestamp):      $TS"
echo "========================================="
