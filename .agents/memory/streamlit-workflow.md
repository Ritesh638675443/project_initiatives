---
name: Streamlit workflow startup
description: Startup settings needed for the Streamlit preview workflow in this workspace.
---

The Streamlit workflow must set `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` and use
`--server.headless true`; otherwise the first launch can pause on Streamlit's email
onboarding prompt before opening its configured port.

**Why:** The workflow runner has no interactive terminal input, so the onboarding prompt
causes a false port-timeout failure even when the app code is healthy.

**How to apply:** Preserve these settings when restarting or recreating the Streamlit
workflow.