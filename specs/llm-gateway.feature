Feature: Unified LLM access with caching, fallback and quota ledger
  As the app
  I want every AI call to go through one client
  So that free quota is used wisely and the app keeps working when a provider fails

  Scenario: Identical requests are served from cache
    Given I generated tags for chunk "c123" with prompt template "tag-v1"
    When the same request is made again
    Then no provider is called
    And the usage ledger records a cache hit

  Scenario: Fallback ladder when the gateway is rate limited
    Given OmniRoute returns a rate limit error
    When a gate question batch is requested
    Then the client tries the Gemini API key tier
    And if that fails it tries the local Ollama model
    And if that fails the job is queued for later

  Scenario: The quiz is never blocked by the cloud
    Given no cloud provider is reachable
    When the recall gate opens
    Then a smaller local-model quiz is offered
    And the user is told that the quiz is in offline mode

  Scenario: Structured output is validated
    Given the provider returns invalid JSON for a schema
    When the client validates the response
    Then it retries once with a repair prompt
    And if still invalid it falls back to the next tier

  Scenario: Usage is recorded without secrets
    Given any LLM call completes
    Then the ledger stores provider, model, task, token counts and status
    And no prompt text containing API keys is stored

  Scenario: Billing safety
    Given the settings screen lists providers
    Then each provider shows whether it is a recurring free pool or a one-time credit
    And one-time credit providers are disabled by default
