# SIGMA Abstract Submission Portal

A purely Streamlit application for the Department of Industrial Engineering, Anna
University, to collect SIGMA Domain Mini Project abstract PDFs and manage them
through a coordinator dashboard.

## Features

- Student submission form with project and team details.
- Up to 10 validated team members.
- PDF-only upload validation with a 10 MB limit.
- Duplicate protection for the same team and domain.
- Unique SIGMA Submission IDs.
- Text acknowledgement download after submission.
- Admin dashboard with summary metrics, filters, details, PDF preview/download,
  team submission register, Excel export, CSV exports, and an all-PDF ZIP archive.
- Admin can cancel and permanently delete a submission after confirmation.
- SQLite metadata storage and separate local PDF storage.

## Run locally

```bash
streamlit run app.py
```

The app creates these folders automatically:

```text
data/
├── sigma.db
└── submissions/
```

The SQLite database stores metadata and the `data/submissions/` folder stores the
actual PDFs. You can override both locations with `SIGMA_DB_PATH` and
`SIGMA_STORAGE_DIR`.

The initial local fallback login is:

```text
Username: admin
Password: admin123
```

For any shared or deployed instance, configure a strong password in
`.streamlit/secrets.toml`:

```toml
[admin]
username = "admin"
password = "replace-with-a-strong-password"
```

Do not commit the real `secrets.toml` file.

## Streamlit Cloud deployment

1. Push this project to a GitHub repository.
2. Create a new app in Streamlit Community Cloud.
3. Select the repository and set the main file to `app.py`.
4. Add the dependencies from `requirements.txt` through the repository.
5. In the app settings, add the following secrets:

   ```toml
   [admin]
   username = "admin"
   password = "replace-with-a-strong-password"
   ```

6. Deploy.

SQLite and local files are intentionally used for the initial version. A hosted
Streamlit deployment may not guarantee local-file durability through every
rebuild or redeploy. The database and storage calls are isolated in
`database.py` and `storage.py`, so they can be replaced with Supabase Storage,
Google Drive, or S3 without changing the form and dashboard code.