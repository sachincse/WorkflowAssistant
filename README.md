# WorkflowAssistant

WorkflowAssistant is an AI-powered, agent-based workflow automation system designed to fully automate employee onboarding processes **without requiring code changes**, even when policies evolve or new APIs need to be integrated.

Instead of hardcoded workflows, WorkflowAssistant uses **LLM-driven dynamic orchestration** where specialized agents:

- Understand onboarding requests in natural language
- Discover available integrations from an API registry
- Interpret policy documents and enforce constraints
- Produce and execute a policy-compliant onboarding plan
- Ask follow-up questions when requirements are incomplete

## Why WorkflowAssistant

Traditional onboarding systems:

- Require frequent code changes when policies are updated
- Need engineering effort to integrate new APIs or services
- Break easily when requirements are incomplete or ambiguous

WorkflowAssistant solves this by combining:

- **Policies as documents** (editable, versionable, uploadable)
- **Integrations as config** (`api_registry.json`)
- **Agents + orchestration graph** (LangGraph)
- **LLM reasoning** to adapt the workflow at runtime

## Agentic Architecture (Diagram)

```mermaid
flowchart TB
  U[HR / Ops User\nNatural language onboarding request]

  UI[Streamlit UI\napp.py]
  ORCH[Workflow Engine\nworkflow_engine_full.py\n(LangGraph)]

  GUARD[Security Guard\nsecurity.py\nPII redaction / output validation]
  ASSIST[Conversation Agent\nCollect missing fields\nHuman-in-the-loop]
  POLICY[Policy Manager\npolicy_manager.py\nLoad + interpret policies]
  DOCS[(Policy Documents\nsecure_hr_policy.txt\nhealthcare_policy.txt)]

  APIS[(API Registry\napi_registry.json)]
  PLAN[Planner / Extractor Agent\nDerive structured needs + actions]
  EXEC[Executor Agent\nMap actions -> APIs\nRun or fallback]

  EXT[External Systems\nHR / LMS / Travel / Insurance / Email]
  AUDIT[Plan + Logs\nExplainability]

  U --> UI --> ORCH
  ORCH --> GUARD --> ASSIST

  ASSIST --> POLICY
  POLICY <--> DOCS

  ASSIST -->|User confirms summary| PLAN
  PLAN --> APIS
  PLAN --> POLICY
  PLAN --> EXEC

  EXEC --> EXT
  EXEC --> AUDIT
  AUDIT --> UI
  ASSIST --> UI
```

## How It Works (End-to-End)

1. **Requirement understanding (human-in-the-loop)**
   - HR/Ops triggers onboarding using natural language.
   - The assistant asks targeted follow-ups until all mandatory fields are captured (derived from the active policies).

2. **Policy-aware decision making**
   - Policies are stored as documents (`*.txt`).
   - The system reads and interprets them to decide constraints and required actions.
   - Example: different training by gender, relocation tier by role, insurance steps driven by healthcare policy.

3. **Dynamic API discovery (config-driven)**
   - Available integrations live in `api_registry.json`.
   - Agents match needed actions to available APIs at runtime.
   - New APIs can be added by updating config only.

4. **Intelligent orchestration (multi-step + adaptive)**
   - A LangGraph workflow coordinates the agents.
   - If an API is unavailable (e.g., in maintenance), the executor falls back to a manual step.

5. **Zero-code workflow evolution**
   - Policy updates: update/upload policy documents.
   - Integrations: add/update API registry entries.
   - No workflow rewrites are required.

## Key Capabilities

- **No-code onboarding automation**
- **LLM-driven workflow orchestration**
- **Dynamic API discovery & execution**
- **Policy-aware decision making**
- **Multi-agent collaboration**
- **Handles incomplete / ambiguous inputs**
- **Extensible via configuration and documents**

## Repo Structure

- **`app.py`**
  - Streamlit UI (chat interface + sidebar dashboard)
  - Lets you view active policies and upload new policy documents
- **`workflow_engine_full.py`**
  - Main orchestration engine (LangGraph)
  - Conversational assistant -> planner/extractor -> executor
- **`policy_manager.py`**
  - Loads policies and uses the LLM to derive mandatory fields and actions
- **`api_registry.json`**
  - Central API configuration repository (discoverable tools)
- **`secure_hr_policy.txt`, `healthcare_policy.txt`**
  - Policy documents used for decisions and required fields
- **`security.py`**
  - Basic PII redaction and output safety checks
- **`email_service.py`**
  - Gmail SMTP-based welcome email sender (demo integration)

## Setup & Run

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure environment variables

Create a `.env` file in the project root (or set environment variables in your shell):

- **`OPENAI_API_KEY`**
  - Required for `ChatOpenAI` usage (`gpt-4o-mini` is configured in code).
- **`GMAIL_USER`**
  - Gmail address used by the demo email integration.
- **`GMAIL_APP_PASSWORD`**
  - Gmail App Password (recommended) for SMTP login.
- **`TARGET_TEST_EMAIL`** *(optional)*
  - Where onboarding emails are sent in the demo.

### 3) Start the app

```bash
streamlit run app.py
```

## Configuration-Driven Integrations

### API Registry (`api_registry.json`)

The engine loads integrations from `api_registry.json` at runtime.

Each entry looks like:

```json
{
  "name": "SendGrid_Email",
  "description": "Sends welcome emails and notifications.",
  "status": "active",
  "endpoint": "https://api.sendgrid.mock/v3/mail/send"
}
```

To add a new integration:

- Add a new object under `apis`.
- Keep `status` as `active` to allow automatic execution.
- The executor will attempt to match APIs by keyword (e.g., `LMS`, `Insurance`, `HR`, `Travel`).

## Policy-Driven Behavior

Policies are plain text documents in the repo and can also be uploaded via the Streamlit sidebar.

- Updating policies changes:
  - Mandatory fields the assistant must collect
  - Mandatory actions that must be executed
  - Decision rules (e.g., relocation tier mapping)

## Example Flow

1. HR: "Onboard a senior engineer joining in London"
2. Assistant asks for missing required fields (based on policies), e.g. blood group, emergency contact.
3. Assistant summarizes captured details and asks for confirmation.
4. On confirmation, the engine:
   - Extracts a structured onboarding plan
   - Executes actions via discovered APIs
   - Returns a final, explainable execution report (automated vs manual vs failed)

## Use Cases

- Employee onboarding automation
- Role-based access provisioning
- HR & IT operations workflows
- Compliance-driven process automation
- Enterprise workflow orchestration

## Notes

- This project is built as an AI-native workflow design demo and emphasizes **adaptation via documents/config** over hardcoded workflow logic.
- Some endpoints in `api_registry.json` are mock URLs used for demonstration.