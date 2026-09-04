import json

from app.llm.client import LLMClient
from app.models.schemas import (
    GeneratedTest,
    GenerationResult,
)


class GeneratorAgent:

    def __init__(self):
        self.llm = LLMClient()

    def generate(self, plan):

        print()
        print("=" * 70)
        print("[AIVAR - STEP 4] TEST GENERATION")
        print("=" * 70)

        print("[GENERATOR INPUT]")
        print(f"Application URL : {plan.application_url}")
        print(f"Total scenarios : {len(plan.scenarios)}")

        print()
        print("[SCENARIOS TO GENERATE]")

        for scenario in plan.scenarios:
            print(
                f"    {scenario.id} | "
                f"{scenario.category} | "
                f"{scenario.priority} | "
                f"{scenario.name}"
            )

        # =========================================================
        # MOCK MODE
        # =========================================================

        if self.llm.provider == "mock":

            tests = []

            for scenario in plan.scenarios:

                # Demo login flow
                if "login" in scenario.name.lower():

                    tests.append(
                        GeneratedTest(
                            id=f"TC-{scenario.id}",
                            scenario_id=scenario.id,
                            name=scenario.name,
                            steps=[
                                {
                                    "action": "navigate",
                                    "target": None,
                                    "value": plan.application_url,
                                },
                                {
                                    "action": "fill",
                                    "target": {
                                        "role": "textbox",
                                        "name": "username",
                                    },
                                    "value": "demo@example.com",
                                },
                                {
                                    "action": "fill",
                                    "target": {
                                        "role": "textbox",
                                        "name": "password",
                                    },
                                    "value": "password",
                                },
                                {
                                    "action": "click",
                                    "target": {
                                        "role": "button",
                                        "name": "Login",
                                    },
                                    "value": None,
                                },
                                {
                                    "action": "assert_visible",
                                    "target": {
                                        "role": "button",
                                        "name": "Logout",
                                    },
                                    "value": None,
                                },
                            ],
                            business_assertions=[
                                "Successful login should show the logout control."
                            ],
                        )
                    )

                # Generic fallback
                else:

                    tests.append(
                        GeneratedTest(
                            id=f"TC-{scenario.id}",
                            scenario_id=scenario.id,
                            name=scenario.name,
                            steps=[
                                {
                                    "action": "navigate",
                                    "target": None,
                                    "value": plan.application_url,
                                }
                            ],
                            business_assertions=[
                                scenario.expected_outcome
                            ],
                        )
                    )

            result = GenerationResult(tests=tests)

            print()
            print("[GENERATOR OUTPUT - MOCK]")
            print(result.model_dump_json(indent=2))

            print("=" * 70)

            return result

        # =========================================================
        # LLM MODE
        # =========================================================

        system_prompt = """
You are AIVAR's Test Generation Agent.

Your job is to convert a software test plan into executable browser
test cases.

The generated tests will be executed by a Python Playwright executor.

Therefore, the output MUST follow the exact JSON structure specified
below.

============================================================
ALLOWED TEST ACTIONS
============================================================

Each test step MUST use exactly one of these actions:

1. navigate
2. fill
3. click
4. assert_visible
5. assert_text

============================================================
STEP FORMAT
============================================================

Each step has this structure:

{
  "action": "click",
  "target": {
    "role": "button",
    "name": "Login"
  },
  "value": null
}

For fill:

{
  "action": "fill",
  "target": {
    "role": "textbox",
    "name": "username"
  },
  "value": "demo@example.com"
}

For navigate:

{
  "action": "navigate",
  "target": null,
  "value": "http://example.com"
}

For assert_visible:

{
  "action": "assert_visible",
  "target": {
    "role": "button",
    "name": "Logout"
  },
  "value": null
}

For assert_text:

{
  "action": "assert_text",
  "target": {
    "role": "heading",
    "name": "Dashboard"
  },
  "value": "Dashboard"
}

============================================================
LOCATOR RULES
============================================================

Prefer semantic locators.

Preferred target fields:

1. role + name
2. label
3. text
4. id
5. selector

Do NOT invent selectors when the application observation does not
provide enough information.

For example, do not invent:

"#random-button"

when no such selector was observed.

Use only information supported by the application observation
or test plan.

============================================================
TEST DESIGN RULES
============================================================

For every planned scenario:

1. Generate one executable test.
2. Start with navigation when required.
3. Use realistic values.
4. Include the actions necessary to execute the scenario.
5. Include business assertions whenever possible.
6. Do not add unrelated actions.
7. Do not invent application functionality.

The test must represent the business intent of the scenario.

============================================================
EXACT OUTPUT STRUCTURE
============================================================

Return ONLY this JSON structure:

{
  "tests": [
    {
      "id": "TC-S001",
      "scenario_id": "S001",
      "name": "Valid login",
      "steps": [
        {
          "action": "navigate",
          "target": null,
          "value": "http://example.com"
        },
        {
          "action": "fill",
          "target": {
            "role": "textbox",
            "name": "username"
          },
          "value": "demo@example.com"
        },
        {
          "action": "click",
          "target": {
            "role": "button",
            "name": "Login"
          },
          "value": null
        }
      ],
      "business_assertions": [
        "Dashboard should be displayed after successful login."
      ]
    }
  ]
}

IMPORTANT:

- Return ONLY JSON.
- Do NOT return markdown.
- Do NOT use ```json.
- Do NOT add commentary.
- Do NOT use "generated_tests".
- Do NOT use "test_cases".
- The root field MUST be "tests".
- Every test MUST contain:
  id
  scenario_id
  name
  steps
  business_assertions
"""

        schema_hint = """
{
  "tests": [
    {
      "id": "string",
      "scenario_id": "string",
      "name": "string",
      "steps": [
        {
          "action": "navigate | fill | click | assert_visible | assert_text",
          "target": {
            "role": "string",
            "name": "string",
            "label": "string",
            "text": "string",
            "id": "string",
            "selector": "string"
          },
          "value": "string"
        }
      ],
      "business_assertions": [
        "string"
      ]
    }
  ]
}
"""

        user_prompt = json.dumps(
            plan.model_dump(),
            indent=2
        )

        print()
        print("[ACTION] Sending test plan to LLM for test generation...")

        data = self.llm.json_call(
            system=system_prompt,
            user=user_prompt,
            schema_hint=schema_hint,
        )

        print()
        print("[GENERATOR] Validating LLM response...")

        result = GenerationResult.model_validate(data)

        print()
        print("[GENERATOR OUTPUT - VALIDATED]")
        print(f"Generated tests : {len(result.tests)}")

        for test in result.tests:

            print()
            print(
                f"    {test.id} | "
                f"{test.scenario_id} | "
                f"{test.name}"
            )

            print(
                f"    Steps: {len(test.steps)}"
            )

            for index, step in enumerate(test.steps):

                print(
                    f"        Step {index + 1}: "
                    f"{step.action} | "
                    f"target={step.target} | "
                    f"value={step.value}"
                )

            print(
                f"    Business assertions: "
                f"{len(test.business_assertions)}"
            )

        print("=" * 70)

        return result