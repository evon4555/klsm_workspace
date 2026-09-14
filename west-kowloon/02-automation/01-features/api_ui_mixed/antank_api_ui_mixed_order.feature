# =============================================================================
# API+UI mixed official ticketing flow
#
#   Flow    : API login -> program search -> show order create -> cancel order
#             -> browser UI status check on the official domain.
#   Source  : C:\Users\klsm\Downloads\wangyifan\anticket-jmeter
#   Pattern : API executes the business chain; UI verifies the final order state.
#
#   The captured HAR confirmed this stable non-seat flow:
#   getProgramById -> listBydate -> tickettype/list -> order/create
#   -> cancelOrder. It intentionally stops before payment.
# =============================================================================
Feature: Website API+UI mixed ticketing order cancellation

  @api_ui_mixed @order_cancel @ticketing @api @ui @SIT-TC-WEB-TKT-079
  Scenario: SIT-TC-WEB-TKT-079 API+UI mixed show order can be cancelled before payment
    Given a registered Website user is available for API+UI mixed ticketing validation
    When  I create and cancel a show order through the official APIs
    Then  the browser UI check confirms the same order is cancelled
