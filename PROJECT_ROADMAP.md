# Adaptive Revenue Recovery Agent

> ## 🚨 PROJECT NORTH STAR — READ THIS BEFORE MAKING CHANGES
>
> **This project is NOT a Payment Link generator.**
>
> **This project is NOT an AI chatbot.**
>
> **This project is NOT a collection of disconnected AI demos.**
>
> The goal is to build a:
>
> **POLICY-GOVERNED, AUTONOMOUS REVENUE RECOVERY PLATFORM**
>
> that can detect failed payments, understand why recovery may be possible, make a safe recovery decision using AI + policy knowledge, execute the selected recovery asynchronously, communicate with the customer, observe payment lifecycle events, reconcile partial/full recovery, retry failures safely, and provide complete operational visibility.
>
> The system should ultimately be able to operate as a closed-loop recovery system with human intervention only when required.

---

# 1. THE MAIN GOAL

The product exists to recover revenue that would otherwise be lost after payment failure.

The intended lifecycle is:

```text
PAYMENT FAILURE
       │
       ▼
TRANSACTION
       │
       ▼
RECOVERY CASE
       │
       ▼
AI + POLICY / RAG
       │
       ▼
RECOVERY DECISION
       │
       ▼
SAFETY GATE
       │
       ▼
RECOVERY ACTION
       │
       ▼
ASYNC WORKER
       │
       ▼
PAYMENT / COMMUNICATION
       │
       ▼
WEBHOOK
       │
       ▼
RECONCILIATION
       │
       ├───────────────┐
       ▼               ▼
PARTIAL RECOVERY   FULL RECOVERY
       │               │
       ▼               ▼
CONTINUE            CLOSE CASE
       │               │
       └───────┬───────┘
               ▼
        COMMUNICATION
               │
               ▼
       MONITORING / AUDIT
               │
               ▼
          OPERATIONS
               │
               ▼
           DASHBOARD

2. WHAT MAKES THIS PROJECT DIFFERENT

The core value is NOT:

"AI can generate a recovery message."

The core value is:

AI-driven decision making + policy enforcement + autonomous execution + payment lifecycle reconciliation + reliability + customer communication + operational visibility.

The system must therefore answer:

Why should we recover this payment?

AI + transaction context + policy knowledge.

What recovery strategy should be used?

Recovery decision engine.

Is the decision safe?

Safety Gate.

Can the action actually be executed?

Recovery Action + Worker.

What happens if execution fails?

Retry + lease + attempt limits.

What happens if the customer partially pays?

Reconciliation.

What happens if the customer fully pays?

Recovery is confirmed and the case closes.

What happens if a webhook arrives twice?

Idempotency prevents duplicate processing.

What happens if a Payment Link expires or is cancelled?

The system must fail closed and must not claim a false recovery.

How do we communicate with the customer?

Communication layer.

How do operators know what is happening?

Monitoring + dashboard + audit trail.

3. FINAL PRODUCT DEFINITION

The final system should be:

Autonomous
       +
Policy-Governed
       +
AI-Assisted
       +
Financially Safe
       +
Event-Driven
       +
Idempotent
       +
Retryable
       +
Observable
       +
Operationally Usable

The word autonomous does NOT mean uncontrolled.

Every autonomous action must remain bounded by:

POLICY
  ↓
SAFETY
  ↓
AUTHORIZATION
  ↓
EXECUTION
  ↓
VERIFICATION
  ↓
AUDIT
4. FINAL ARCHITECTURE
                         ┌──────────────────────┐
                         │   PAYMENT FAILURE    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     TRANSACTION      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   RECOVERY CASE      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       AI + RAG ENGINE        │
                    │                              │
                    │ classification               │
                    │ recoverability               │
                    │ risk                         │
                    │ recommended action           │
                    │ policy knowledge             │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │    SAFETY GATE       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    RECOVERY ACTION   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    ACTION WORKER     │
                         │                      │
                         │ claim               │
                         │ lease               │
                         │ retry               │
                         │ execute             │
                         └──────────┬───────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   │                                 │
                   ▼                                 ▼
          ┌──────────────────┐              ┌──────────────────┐
          │     RAZORPAY     │              │  COMMUNICATION   │
          │                  │              │                  │
          │ Payment Link     │              │ Email / SMS etc. │
          │ Payment status   │              │ Templates        │
          └────────┬─────────┘              └────────┬─────────┘
                   │                                 │
                   ▼                                 │
          ┌──────────────────┐                       │
          │     WEBHOOK      │                       │
          └────────┬─────────┘                       │
                   │                                 │
                   ▼                                 │
          ┌──────────────────┐                       │
          │ RECONCILIATION   │◄──────────────────────┘
          │                  │
          │ partial payment  │
          │ full payment     │
          │ expired          │
          │ cancelled        │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  FINAL RECOVERY  │
          │     STATE        │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ AUDIT + METRICS  │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │   OPERATIONS     │
          │   DASHBOARD      │
          └──────────────────┘
5. PHASE ROADMAP
Phase 1–7 — Foundation + AI Recovery Engine
Status
████████████████████  COMPLETE

Core backend, recovery engine, AI decisioning, policy/RAG, safety and orchestration foundations were established.

Phase 8 — Reliable Recovery Orchestration
Goal

Make recovery actions reliable and safe under concurrent execution.

Includes
Atomic action claiming
Idempotency
Concurrent worker protection
Recovery orchestration
Safe execution boundaries
Status
████████████████████  COMPLETE
Verified
test_action_claim
test_action_idempotency
test_concurrent_workers

Important invariant:

ONE ACTION
    ↓
ONE OWNER
    ↓
ONE EXECUTION

A duplicate worker must never execute the same recovery action simultaneously.

Phase 9 — Payment Link Lifecycle + Reconciliation
Goal

Turn Payment Link creation into a complete recovery lifecycle.

Includes
Payment Link creation
Payment Link metadata
Partial payment
Cumulative recovery
Full recovery
Expiry
Cancellation
Webhook idempotency
Reconciliation
Status
████████████████████  COMPLETE
Verified
test_payment_link_lifecycle
test_webhook_idempotency

Important invariant:

PAYMENT LINK CREATED
        ↓
PAYMENT EVENTS
        ↓
RECONCILIATION
        ↓
RECOVERY STATE
Phase 10 — Autonomous Recovery Worker
Goal

Execute recovery actions asynchronously and safely.

Includes
Worker claim
Worker lease
Retry handling
Maximum attempt limits
Expired lease recovery
Concurrent worker protection
Execution failure handling
Status
████████████████████  IMPLEMENTED
Verified
test_action_claim
test_action_idempotency
test_worker_retry
test_concurrent_workers
Important

The worker must never blindly execute an action.

The lifecycle is:

PENDING
   ↓
CLAIM
   ↓
EXECUTING
   ↓
SUCCESS

or:

EXECUTING
   ↓
FAILURE
   ↓
RETRY / PENDING

or:

EXECUTING
   ↓
LEASE EXPIRES
   ↓
PENDING
Phase 11 — Communication / Notifications
Goal

Connect recovery actions to safe customer communication.

Recovery Decision
       ↓
Recovery Action
       ↓
Communication
       ↓
Customer
11.2 Template Engine

Status:

████████████████████  COMPLETE

Verified:

test_template_engine

Includes:

Template rendering
Email templates
SMS templates
Variable validation
Missing-variable protection
Unknown-variable protection
Template versioning
11.3 Communication Policy

Status:

████████████████████  COMPLETE

Verified:

test_communication_policy

Includes:

Allowed communication
Recovery confirmation rules
Manual escalation
Safe customer-facing information
Policy enforcement
No false recovery claims
11.4 Communication Service

Status:

████████████████████  COMPLETE

Verified:

test_communication_service

Includes:

Communication creation
Provider dispatch
Delivery state
Idempotency
Safe provider failure handling
11.5 Communication Integration

Status:

████████████████████  COMPLETE

Verified:

test_communication_integration

Includes:

Recovery case linkage
Recovery action linkage
Approved customer content
Policy provenance
Integration idempotency
Safe dispatch
11.6 Communication Trigger

Status:

████████████████████  COMPLETE

Verified:

test_communication_trigger

Triggers include:

Payment Link Created
        ↓
Communication

Partial Payment
        ↓
Communication

Confirmed Recovery
        ↓
Communication

Expired / Cancelled
        ↓
Safe handling
11.7 Communication Dispatcher

Status:

████████████████████  COMPLETE

Verified:

test_communication_dispatcher

Includes:

Trigger → communication mapping
Duplicate protection
Provider dispatch
Partial-payment communication
Recovery-success communication
Fail-closed handling
Entity validation
11.8 Live Lifecycle Integration
Architecture
AI Decision
   ↓
Safety Gate
   ↓
Recovery Action
   ↓
Razorpay Payment Link
   ↓
PAYMENT_LINK_CREATED
   ↓
Communication Dispatcher

Webhook side:

Razorpay Webhook
       ↓
Payment Link Event
       ↓
Reconciliation
       ↓
       ├── Partial Payment
       │       ↓
       │   Communication
       │
       └── Full Recovery
               ↓
          Communication

Expired / cancelled:

Expired / Cancelled
        ↓
No false recovery message
        ↓
Fail closed
11.9 Closed-Loop Recovery Communication

Status:

████████████████████  COMPLETE

Verified:

test_recovery_communication_lifecycle

The closed-loop test validates:

Payment Link
    ↓
Customer Communication
    ↓
Duplicate Protection
    ↓
Partial Payment
    ↓
Partial Communication
    ↓
Additional Payment
    ↓
Full Recovery
    ↓
Success Communication
    ↓
Final Recovery State
Phase 12 — Production Monitoring / Observability
Goal

Move from individual worker observability to complete system-level operational visibility.

Required metrics
Total failed payments
Recovery attempts
Recovery success rate
Partial recoveries
Recovered revenue
Failed recoveries
AI decisions
Escalations
Worker failures
Webhook failures
Communication failures
Status
████████████████░░░░  IMPLEMENTED / IN PROGRESS
Current Operations API
GET /api/v1/operations/summary

GET /api/v1/operations/recovery-cases

GET /api/v1/operations/recovery-cases/{case_id}

GET /api/v1/operations/recovery-actions/{action_id}

GET /api/v1/operations/webhooks

GET /api/v1/operations/audit-logs

GET /api/v1/operations/communications
Important distinction

Worker observability is NOT the same as production monitoring.

Phase 10:

Can the worker be trusted?

Phase 12:

Can the entire system be operated and understood?
Phase 13 — Dashboard / Operational Interface
Goal

Build a real operator interface.

Current system:

API
Database
Worker
Scripts
Webhooks

Target:

┌──────────────────────────────────────────────┐
│         REVENUE RECOVERY DASHBOARD           │
├──────────────────────────────────────────────┤
│ Failed Payments          1,284               │
│ Recovery Cases             842               │
│ Recovered Revenue      ₹4,82,300             │
│ Recovery Rate               67.4%             │
├──────────────────────────────────────────────┤
│ ACTIVE RECOVERY CASES                        │
│                                              │
│ #1024  Bank Declined   ₹2,000   Active       │
│ #1023  Payment Failed  ₹800     Partial      │
│ #1021  Timeout         ₹1,500   Recovered    │
└──────────────────────────────────────────────┘

Operator should eventually be able to inspect:

Transaction
AI decision
AI reasoning
Policy evidence
Safety Gate result
Recovery case
Recovery action
Payment Link
Webhook history
Reconciliation history
Communication history
Retry history
Audit history
Status
░░░░░░░░░░░░░░░░░░░░  NOT STARTED
Phase 14 — Production-Ready End Product
Goal

Turn the complete engine into a production-ready product.

Final definition:

An autonomous, policy-governed revenue recovery platform that detects failed payments, reasons about recoverability, selects a safe recovery strategy, executes it asynchronously, handles payment lifecycle events, reconciles partial/full payments, retries failures safely, communicates with customers, and provides operational visibility.

Status
░░░░░░░░░░░░░░░░░░░░  NOT STARTED
6. CURRENT PROJECT STATUS
FOUNDATION
████████████████████  100%

RECOVERY ENGINE
████████████████████  100%

AI + RAG + SAFETY
████████████████████  100%

ORCHESTRATION
████████████████████  100%

RAZORPAY EXECUTION
████████████████████  100%

WEBHOOKS
████████████████████  100%

RECONCILIATION
████████████████████  100%

RELIABILITY
████████████████████  100%

PAYMENT LIFECYCLE
████████████████████  100%

AUTONOMOUS WORKER
████████████████████  100%

COMMUNICATION
████████████████████  100%

SYSTEM MONITORING
████████████████░░░░  ~80%

DASHBOARD
░░░░░░░░░░░░░░░░░░░░  0%

PRODUCTION HARDENING
░░░░░░░░░░░░░░░░░░░░  0%
7. NON-NEGOTIABLE ENGINEERING RULES
Rule 1 — Never create a false recovery

Never tell the customer:

Payment recovered

unless recovery has been confirmed.

Correct:

Payment initiated
        ≠
Payment recovered
Rule 2 — Webhooks are authoritative for payment lifecycle

Do not assume:

Payment Link created
=
Payment successful

Payment must be verified through the payment lifecycle.

Rule 3 — Everything must be idempotent

Repeated events must not create:

duplicate recovery actions
duplicate Payment Links
duplicate communications
duplicate recovery amounts
duplicate state transitions
Rule 4 — Workers must claim before executing

Never:

query pending
↓
execute

Use:

query pending
↓
atomic claim
↓
lease
↓
execute
Rule 5 — Retries must be bounded

Never retry forever.

Use:

attempt_count
+
maximum attempts
+
lease expiry
Rule 6 — AI must not bypass safety

Architecture:

AI Decision
     ↓
Safety Gate
     ↓
Execution

Never:

AI
 ↓
direct financial execution
Rule 7 — Customer communication must be policy-governed

Never expose:

internal failure details
internal system errors
unsupported claims
unconfirmed recovery
sensitive internal reasoning
Rule 8 — Preserve financial metadata

Payment Link identifiers, URLs, payment IDs and recovery amounts are lifecycle information.

Do not overwrite important metadata accidentally during reconciliation.

Rule 9 — Do not modify unrelated files

When implementing a phase:

Change only files required by that phase.

Before modifying a critical file:

inspect
understand
change minimally
test
verify git diff
Rule 10 — Never run destructive/unrelated tests

Especially:

Do not run Gemini tests

when the Gemini/embedding quota is exhausted.

Use deterministic local tests wherever possible.

8. GEMINI / AI QUOTA RULE

The project has previously encountered:

429 RESOURCE_EXHAUSTED

from the Gemini embedding service.

This is an API quota problem.

It does NOT automatically mean that the underlying recovery architecture is broken.

When quota is exhausted:

DO NOT PANIC
DO NOT REWRITE THE ARCHITECTURE
DO NOT MODIFY RANDOM FILES
DO NOT RUN GEMINI TESTS REPEATEDLY

Instead:

Continue deterministic development
        ↓
Complete non-AI phases
        ↓
Use existing tests that do not require Gemini
        ↓
Return to live AI integration when quota is available
9. SAFE VERIFICATION COMMANDS

Run from:

F:\adaptive-revenue-recovery-agent

Activate environment:

.venv\Scripts\activate

Check repository:

git status

Check recent milestones:

git log --oneline -10

Check code changes:

git --no-pager diff

Check changed-file summary:

git --no-pager diff --stat
10. DATABASE VERIFICATION

Check database tables:

python -c "from backend.app.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"

Expected core tables include:

transactions
webhook_events
recovery_cases
recovery_actions
audit_logs
communications
policy_documents
policy_chunks
11. SERVER VERIFICATION

Start backend:

python -m uvicorn backend.app.main:app --reload

Expected:

Uvicorn running on http://127.0.0.1:8000

Check:

/

and:

/health
12. PHASE VERIFICATION COMMANDS
Phase 8
python -m backend.app.scripts.test_action_claim
python -m backend.app.scripts.test_action_idempotency
python -m backend.app.scripts.test_concurrent_workers
Phase 9
python -m backend.app.scripts.test_payment_link_lifecycle
python -m backend.app.scripts.test_webhook_idempotency
Phase 10
python -m backend.app.scripts.test_worker_retry
python -m backend.app.scripts.test_concurrent_workers
IMPORTANT

The live recovery-worker test may require the AI/embedding API depending on the current implementation.

If Gemini quota is exhausted, do not repeatedly run it.

Phase 11
python -m backend.app.scripts.test_template_engine
python -m backend.app.scripts.test_communication_policy
python -m backend.app.scripts.test_communication_service
python -m backend.app.scripts.test_communication_integration
python -m backend.app.scripts.test_communication_trigger
python -m backend.app.scripts.test_communication_dispatcher
python -m backend.app.scripts.test_recovery_communication_lifecycle
13. OPERATIONS API VERIFICATION

Open:

http://127.0.0.1:8000/docs

Verify:

GET /api/v1/operations/summary
GET /api/v1/operations/recovery-cases
GET /api/v1/operations/recovery-cases/{case_id}
GET /api/v1/operations/recovery-actions/{action_id}
GET /api/v1/operations/webhooks
GET /api/v1/operations/audit-logs
GET /api/v1/operations/communications
14. WHAT A HEALTHY RECOVERY CASE SHOULD LOOK LIKE

Example:

Transaction
     │
     ▼
Recovery Case
     │
     ├── classification
     ├── recoverability
     ├── risk score
     ├── revenue at risk
     └── recommended action
              │
              ▼
       Recovery Action
              │
              ├── status
              ├── attempts
              ├── lease
              └── result
              │
              ▼
       Payment / Communication
              │
              ▼
          Webhook
              │
              ▼
        Reconciliation
              │
              ▼
       Recovery Case State
15. IMPORTANT STATE DISTINCTIONS

Never confuse these:

Payment Link CREATED

with:

Payment RECEIVED

with:

Payment CAPTURED

with:

Recovery CONFIRMED

Likewise:

Communication CREATED

is not:

Communication SENT

and:

Communication SENT

is not:

Communication DELIVERED

The system must preserve these distinctions.

16. WHEN SOMETHING BREAKS

Follow this procedure.

Step 1

Check:

git status
Step 2

Check:

git --no-pager diff --stat
Step 3

Check exactly what changed:

git --no-pager diff
Step 4

Identify whether the failure is:

Code bug
Database problem
Configuration problem
External API problem
Quota problem
Test fixture problem
Step 5

Do NOT modify unrelated files.

Step 6

Fix the smallest necessary surface.

Step 7

Run the smallest relevant test.

Step 8

Run:

git status

again.

17. GIT CHECKPOINT RULE

Every major phase should have a clean Git checkpoint.

Before starting a new major phase:

git status

should ideally show:

nothing to commit, working tree clean

After completing the phase:

git add <only-required-files>
git commit -m "feat: complete phase X"

Then:

git push origin main

The repository should tell the same story as the roadmap.

18. CURRENT NEXT STEP

The project is currently beyond the core-engineering stage.

The next major objective is:

PHASE 12
SYSTEM-LEVEL MONITORING / OBSERVABILITY

Then:

PHASE 13
DASHBOARD / OPERATIONAL INTERFACE

Then:

PHASE 14
PRODUCTION HARDENING

Do NOT jump to dashboard work just because it looks visually impressive.

The correct order is:

RELIABLE ENGINE
      ↓
OBSERVABILITY
      ↓
DASHBOARD
      ↓
PRODUCTION HARDENING
19. THE ONE-SENTENCE GOAL

If you forget everything else, remember this:

We are building an autonomous, policy-governed revenue recovery platform that detects failed payments, decides how they can safely be recovered, executes recovery, communicates with customers, verifies payment outcomes, reconciles partial/full recovery, handles failures safely, and gives operators complete visibility.

20. THE "ARE WE BUILDING THE RIGHT THING?" CHECK

Before adding any feature, ask:

Question 1

Does this help recover lost revenue?

Question 2

Does this make recovery safer?

Question 3

Does this make recovery more autonomous?

Question 4

Does this improve reliability?

Question 5

Does this improve customer communication?

Question 6

Does this improve reconciliation or verification?

Question 7

Does this improve operational visibility?

Question 8

Does this help turn the system into a real product?

If the answer to all is:

NO

then the feature probably does not belong in the core project.

21. FINAL PRODUCT TEST

The ultimate demonstration should be:

1. Payment fails
        ↓
2. Transaction recorded
        ↓
3. Recovery Case created
        ↓
4. AI analyzes the case
        ↓
5. Policy/RAG provides relevant knowledge
        ↓
6. Safety Gate validates decision
        ↓
7. Recovery Action created
        ↓
8. Worker claims action
        ↓
9. Razorpay Payment Link created
        ↓
10. Customer communication generated
        ↓
11. Customer pays partially
        ↓
12. Webhook received
        ↓
13. Reconciliation records partial recovery
        ↓
14. Customer communication updated
        ↓
15. Customer pays remaining amount
        ↓
16. Webhook received
        ↓
17. Recovery becomes confirmed
        ↓
18. Success communication sent
        ↓
19. Case closes
        ↓
20. Audit + metrics updated
        ↓
21. Operator sees complete lifecycle
    in dashboard

That is the product.

Not:

AI → Payment Link

But:

FAILED PAYMENT
      ↓
INTELLIGENT DECISION
      ↓
SAFE AUTONOMOUS ACTION
      ↓
CUSTOMER INTERACTION
      ↓
VERIFIED FINANCIAL OUTCOME
      ↓
CLOSED-LOOP RECOVERY
      ↓
OPERATIONAL VISIBILITY
🚨 FINAL REMINDER

Do not lose the product vision while implementing individual files.

A single test passing is not the product.

A single AI response is not the product.

A Payment Link is not the product.

A dashboard is not the product.

The product is the complete autonomous revenue recovery lifecycle.

DETECT
  ↓
UNDERSTAND
  ↓
DECIDE
  ↓
VALIDATE
  ↓
EXECUTE
  ↓
COMMUNICATE
  ↓
OBSERVE
  ↓
RECONCILE
  ↓
VERIFY
  ↓
CLOSE
  ↓
LEARN / IMPROVE

Every future implementation should move the project toward this loop.


### One important correction

I would **not** put `Phase 11.9 = 100%` in the README until the current `test_recovery_communication_lifecycle` issue is resolved in your actual checkout. Your retrieved earlier test output shows the intended 11.9 test reached all 12 checks, :contentReference[oaicite:0]{index=0} but your current checkout hit the `recovery_notification_email` configuration mismatch. So the README should distinguish **architecture implemented** from **current checkout fully verified**.

Also, your current database already contains the `communications` table, and the operations API is exposing communications, which supports treating the communication layer as implemented rather than starting Phase 11 from zero.

And I am keeping your explicit constraint in mind for this project: **do not modify unrelated files and do not run the Gemini tests.**

Final Phase 13 plan

I'd now adjust our remaining roadmap to:

13.1 Configuration hardening          ✅
13.2 API security                     ✅
13.3 Worker reliability              ✅
13.4 Database/concurrency             ✅
13.5 Observability                    ✅

13.6 React + Vite Dashboard           ← NOW
13.7 Production Deployment
13.8 End-to-End Live Demonstration
13.9 Final Regression
13.10 GitHub Release Checkpoint

And 13.8 is important.

We'll actually verify the complete chain:

Frontend
   ↓
Backend
   ↓
Database
   ↓
Recovery Engine
   ↓
AI Decision
   ↓
Payment Execution
   ↓
Razorpay
   ↓
Webhook
   ↓
Reconciliation
   ↓
Communication
   ↓
Dashboard

So yes—I strongly recommend proceeding with React + Vite now.

The goal from this point shouldn't be “add a frontend.”

It should be:

Turn the already-built recovery engine into a publicly demonstrable, end-to-end SaaS product that a judge can open, understand, interact with, and verify.

That is a much stronger finish to this project.
