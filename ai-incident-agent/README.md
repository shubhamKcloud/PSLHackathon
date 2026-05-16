# AI Incident Agent

This repository contains a proposed solution for an AI-driven incident management agent that continuously monitors application and infrastructure logs, detects anomalies and errors, performs root cause analysis, creates incident tickets, generates candidate code fixes, and supports automated remediation workflows.

## Goals

- Continuous log ingestion and anomaly detection
- Automatic error classification and root cause analysis
- Actionable incident ticket creation
- AI-powered code fix generation suggestions
- Integration points for automated remediation and observability tools

## Structure

- `src/ai_incident_agent/`
  - `agent.py` - orchestrates monitoring, analysis, ticketing, and remediation
  - `log_monitor.py` - collects local logs and detects anomalies
  - `cloudwatch_monitor.py` - collects logs from AWS CloudWatch
  - `analyzer.py` - performs root cause analysis and triage
  - `ticketing.py` - creates actionable incident tickets
  - `remediator.py` - generates remediation recommendations and code fix artifacts
  - `runner.py` - entry point for the agent runtime
  - `ticketing_tool.py` - CLI helper to create file-based tickets

- `tests/` - basic automation tests and integration stubs

### log and ticket folders

- `logs/` - sample input logs for the agent
- `tickets/` - generated incident ticket files
- `knowledgeBase/` - predefined incident templates and root cause metadata

## Setup

### 1. Install dependencies
```bash
make install
```

### 2. Configure OpenAI API (for GPT-4 analysis)

Copy the `.env.example` file to `.env` and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and replace `your_api_key_here` with your actual OpenAI API key:

```
OPENAI_API_KEY=sk-...your-key...
```

The agent will use GPT-4 for:
- **Root cause analysis** — analyzing log anomalies when no matched KB entry exists
- **Remediation suggestions** — generating actionable fixes and playbooks

When a known failure pattern is found in `knowledgeBase/`, the agent uses that KB entry first to create incident tickets and avoids unnecessary AI analysis.

### 3. Optional: Enable CloudWatch Monitoring

To monitor an AWS CloudWatch log group, set these environment variables before running:

```bash
export CLOUDWATCH_LOG_GROUP="/aws/lambda/my-app"
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
```

Then start the agent:
```bash
make monitor
```

The agent will now collect logs from both local files and CloudWatch, running the same incident detection and ticketing pipeline on all logs.

## Quick start with Make

From the project root:

```bash
make install
make monitor
make web
make test
```

- `make install` creates the virtual environment and installs the package
- `make monitor` starts continuous log monitoring and incident creation
- `make web` launches the web dashboard at `http://localhost:5000`
- `make test` runs the basic test suite

## Typical workflow

**Terminal 1** - Start the log monitor:
```bash
make monitor
```

**Terminal 2** - Launch the web dashboard:
```bash
make web
```

Then open `http://localhost:5000` in your browser to view incidents in real-time.

## Features Implemented

✅ Continuous local log monitoring with anomaly detection  
✅ AWS CloudWatch log group monitoring  
✅ GPT-4 powered root cause analysis  
✅ GPT-4 powered remediation suggestions  
✅ File-based incident storage (JSON)  
✅ Real-time web dashboard for incident visualization  
✅ Simple CLI for ticket management  
✅ Knowledge base first incident creation for known patterns like `Failed health check: timeout`  

## Next steps

1. Add ticketing adapters for Jira, ServiceNow, GitHub Issues, PagerDuty
2. Implement secure credentials management and observability for the agent itself
3. Add automated remediation playbooks with guardrails and approvals
4. Enhance log parsing and anomaly detection with custom rules
5. Add integrations for Prometheus, Kubernetes, ELK, Splunk
