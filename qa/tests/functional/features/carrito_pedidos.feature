# language: en
Feature: Customer purchases and permissions

  @TC-F-009 @CA09 @HU05 @writes
  Scenario: TC-F-009 / CA09 - add a product from the catalog
    Given a synthetic customer is logged in
    When the customer adds Miel QA from the catalog
    Then the cart shows one item and the correct total

  @TC-F-014 @CA13 @HU06 @writes
  Scenario: TC-F-014 / CA13 - prevent checkout with an empty cart
    Given a synthetic customer is logged in
    When the customer opens checkout with an empty cart
    Then the customer cannot place an order

  @TC-F-018 @CA17 @HU08 @writes
  Scenario: TC-F-018 / CA17 - prevent customer access to the admin panel
    Given a synthetic customer is logged in
    When the customer navigates directly to the admin panel
    Then the system redirects the customer away from the admin panel

  @TC-NF-INT-002 @CNF-INT-02 @RNF06 @writes
  Scenario: TC-NF-INT-002 / CNF-INT-02 - keep the catalog after reloading while signed in
    Given a synthetic customer is logged in
    When the customer reloads the catalog while signed in
    Then the catalog still shows Miel QA
