---
name: Streamlit PDF preview
description: PDF preview dependency and fallback behavior for the submission portal.
---

Keep `streamlit[pdf]` in `requirements.txt`, but retain a guarded download-only
fallback around `st.pdf`; the workspace package installer may not install Python
extras even when the deployment requirements file supports them.

**Why:** Admin PDF pages must remain usable when the optional embedded viewer
component is unavailable.

**How to apply:** Treat preview as an enhancement and never let `st.pdf` block
download or delete operations.