Feature: Continuous integration
  Every push and pull request must prove the project still builds and passes its checks
  on the operating systems the owner and CI use, without handing CI more access than needed.

  Scenario: Checks run on Linux and on Windows
    Given a push or a pull request
    When the CI workflow runs
    Then lint, typecheck, JavaScript tests and Python tests run on ubuntu and on windows

  Scenario: The desktop app is smoke-tested for real on Linux
    Given the CI workflow runs on ubuntu
    When the app has been built
    Then the Electron smoke test launches it under a virtual display and checks the sidecar

  Scenario: Third-party actions cannot change under us
    Given any "uses:" line in a workflow
    Then it references a full 40-character commit SHA, not a tag or branch

  Scenario: The workflow token has least privilege
    Given the CI workflow
    Then its GITHUB_TOKEN permissions are read-only for contents
    And checkout does not persist the token in the git config
    And the workflow does not use the pull_request_target trigger
