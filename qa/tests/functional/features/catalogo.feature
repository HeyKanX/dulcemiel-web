# language: en
# Source: Appendix C, Table C2 of the report. Test product with stock of 5.
Feature: Public catalog browsing

  @TC-F-005 @CA05 @HU03
  Scenario: TC-F-005 / CA05 - show essential details for a published product
    Given the visitor opens the catalog
    Then the visitor finds the synthetic product with its name, price, and availability

  @TC-F-007 @CA07 @HU04
  Scenario: TC-F-007 / CA07 - show the details of an existing product
    Given the visitor opens the catalog
    When the visitor opens the synthetic product details
    Then the visitor sees its description, price, stock, and category

  @TC-F-008 @CA08 @HU04
  Scenario: TC-F-008 / CA08 - report a nonexistent product
    Given the visitor opens a nonexistent product detail
    Then the visitor sees a clear message and a link to return
