# language: en
# Source: Appendix C, Table C2 of the report. Data is stored in an isolated SQL database.
Feature: Dulce Miel registration and login

  @TC-F-001 @CA01 @HU01 @writes
  Scenario: TC-F-001 / CA01 - register a new account
    Given the visitor opens the registration page
    When the visitor registers a new synthetic account
    Then the visitor sees the registration confirmation

  @TC-F-002 @CA02 @HU01 @writes
  Scenario: TC-F-002 / CA02 - reject a duplicate email
    Given a synthetic test account exists
    When the visitor tries to register again with the same email
    Then the page shows a duplicate email error and keeps the entered name

  @TC-F-004 @CA04 @HU02
  Scenario: TC-F-004 / CA04 - reject invalid credentials
    Given the visitor opens the login page
    When the visitor enters invalid synthetic credentials
    Then the system rejects access without exposing sensitive data
