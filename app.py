"""SIGMA Domain Mini Project Abstract Submission Portal."""

from __future__ import annotations

import hmac
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitAPIException

import database
import storage
from utils import (
    DOMAINS,
    MAX_PDF_SIZE,
    TAGS,
    YEARS,
    build_acknowledgement,
    build_excel,
    build_pdf_zip,
    display_timestamp,
    get_admin_credentials,
    members_dataframe,
    safe_filename,
    submission_register_dataframe,
    submissions_dataframe,
    submission_table_rows,
    validate_pdf,
)


st.set_page_config(
    page_title="SIGMA Abstract Submission Portal",
    page_icon="SIGMA",
    layout="wide",
    initial_sidebar_state="expanded",
)

database.init_db()
storage.ensure_storage()


def go_to(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def is_admin() -> bool:
    return bool(st.session_state.get("admin_authenticated", False))


def render_brand_header() -> None:
    st.title("SIGMA - PROJECT & INITIATIVES")
    st.caption("Domain Mini Project Abstract Submission Portal")
    st.markdown("**Department of Industrial Engineering · Anna University, Chennai**")


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## SIGMA")
        st.caption("Anna University · Industrial Engineering")
        st.divider()

        if is_admin():
            pages = {
                "Dashboard": "Admin Dashboard",
                "Submissions": "Submissions",
                "Teams": "Teams",
                "PDFs": "PDF Library",
                "Download Data": "Download Data",
                "Settings": "Settings",
            }
        else:
            pages = {
                "Home": "Home",
                "Submit Abstract": "Submit Abstract",
                "Guidelines": "Guidelines",
                "Admin Login": "Admin Login",
            }

        current = st.session_state.get("page", "Home")
        if current not in pages.values():
            current = "Admin Dashboard" if is_admin() else "Home"
        selected_label = st.radio(
            "Navigate",
            list(pages.keys()),
            index=list(pages.values()).index(current),
            label_visibility="collapsed",
        )
        selected_page = pages[selected_label]
        if selected_page != st.session_state.get("page"):
            st.session_state.page = selected_page
            st.rerun()

        st.divider()
        if is_admin():
            st.success("Admin session active")
            if st.button("Log out", use_container_width=True):
                st.session_state.admin_authenticated = False
                st.session_state.page = "Home"
                st.rerun()
        else:
            st.caption("Student access")


def render_home() -> None:
    render_brand_header()
    st.divider()
    st.subheader("Domain Mini Project Abstract Submission")
    st.write(
        "Each domain must showcase a mini-project on SIGMA. Domain teams bring "
        "together 10 members from different TAGs to collaborate, execute, and "
        "showcase meaningful project work."
    )

    left, right = st.columns([2, 1])
    with left:
        st.info(
            "Participation and showcase are mandatory for all domains. "
            "The experience you build here can become a strong addition to your resume."
        )
        st.markdown("### Ready to submit?")
        st.write(
            "Keep your project details and PDF abstract ready. The form takes only a few minutes."
        )
        action_one, action_two = st.columns(2)
        with action_one:
            if st.button("Submit an abstract", type="primary", use_container_width=True):
                go_to("Submit Abstract")
        with action_two:
            if st.button("Admin login", use_container_width=True):
                go_to("Admin Login")
    with right:
        st.metric("Maximum team size", "10 members")
        st.metric("Accepted file", "PDF only")
        st.metric("Maximum file size", f"{MAX_PDF_SIZE // (1024 * 1024)} MB")

    st.divider()
    st.subheader("How it works")
    columns = st.columns(3)
    for column, number, title, description in zip(
        columns,
        ["01", "02", "03"],
        ["Prepare", "Submit", "Showcase"],
        [
            "Collect the project title, abstract, guide details, and member information.",
            "Upload one PDF abstract and receive a unique SIGMA Submission ID.",
            "Keep your acknowledgement and stay ready for the domain showcase.",
        ],
    ):
        with column:
            st.markdown(f"### {number}")
            st.markdown(f"**{title}**")
            st.write(description)

    st.divider()
    st.caption("Learn · Collaborate · Build · Showcase")


def render_guidelines() -> None:
    render_brand_header()
    st.header("Submission guidelines")
    st.write(
        "Please review these requirements before starting. A team can submit once for "
        "each domain; duplicate team/domain submissions are blocked automatically."
    )
    with st.expander("What to prepare", expanded=True):
        st.markdown(
            """
            - A clear team name and project title.
            - The Team Leader's Gmail address for official communication.
            - The SIGMA TAGs represented by your team.
            - Details for at least one team member and up to 10 members.
            - One final PDF abstract, no larger than 10 MB.
            """
        )
    with st.expander("Team member requirements"):
        st.markdown(
            """
            Every filled member row must include a name, register number, year, and TAG.
            Register numbers must be unique within the team. The first member is mandatory.
            """
        )
    with st.expander("After submission"):
        st.write(
            "A unique SIGMA Submission ID and a text acknowledgement will be shown immediately. "
            "Save the acknowledgement for your records."
        )
    if st.button("Start a submission", type="primary"):
        go_to("Submit Abstract")


def render_submit() -> None:
    render_brand_header()
    st.header("Submit project abstract")
    st.write("Complete the form below. Fields marked with * are required.")

    st.info(
        "One submission is allowed per team and domain. Your PDF must be a valid PDF file "
        f"under {MAX_PDF_SIZE // (1024 * 1024)} MB."
    )

    # Initialize member count
    if "member_count" not in st.session_state:
        st.session_state.member_count = 1

    with st.form("submission_form", clear_on_submit=False):

        # --------------------------------------------------
        # PROJECT INFORMATION
        # --------------------------------------------------

        st.subheader("Project information")

        project_left, project_right = st.columns(2)

        with project_left:
            domain = st.selectbox(
                "Domain name *",
                ["Select a domain"] + DOMAINS,
            )

            team_name = st.text_input(
                "Team name *",
                max_chars=120,
            )

            project_title = st.text_input(
                "Project title *",
                max_chars=180,
            )

        with project_right:
            team_leader_email = st.text_input(
                "Team Leader Gmail *",
                placeholder="teamleader@gmail.com",
                max_chars=120,
                help="This Gmail will be used for official SIGMA communication.",
            )

            project_tags = st.multiselect(
                "TAG(s) represented *",
                TAGS,
            )

            abstract = st.text_area(
                "Project abstract",
                height=150,
                max_chars=5000,
                help="Optional here if the detailed abstract is included in the PDF.",
            )

        # --------------------------------------------------
        # TEAM INFORMATION
        # --------------------------------------------------

        st.subheader("Team information")

        st.caption(
            f"Team members added: {st.session_state.member_count} / 10"
        )

        members: list[dict[str, str]] = []

        for index in range(st.session_state.member_count):

            with st.expander(
                f"Team member {index + 1}",
                expanded=index == 0,
            ):

                member_left, member_middle, member_right = st.columns(3)

                with member_left:

                    member_name = st.text_input(
                        "Name *",
                        key=f"member_name_{index}",
                        max_chars=120,
                    )

                    register_number = st.text_input(
                        "Register number *",
                        key=f"member_register_{index}",
                        max_chars=40,
                    )

                with member_middle:

                    year = st.selectbox(
                        "Year *",
                        ["Select year"] + YEARS,
                        key=f"member_year_{index}",
                    )

                with member_right:

                    tag = st.selectbox(
                        "TAG *",
                        ["Select TAG"] + TAGS,
                        key=f"member_tag_{index}",
                    )

            members.append(
                {
                    "name": member_name,
                    "register_number": register_number,
                    "year": year,
                    "tag": tag,
                }
            )

        # --------------------------------------------------
        # MEMBER BUTTON
        # --------------------------------------------------

        # --------------------------------------------------
        # MEMBER BUTTONS
        # --------------------------------------------------
        
        st.caption("Manage team members")
        
        add_member = False
        remove_member = False
        
        button_left, button_right = st.columns(2)
        
        with button_left:
            if st.session_state.member_count < 10:
                add_member = st.form_submit_button(
                    "＋ Add more members",
                    use_container_width=True,
                )
            else:
                st.success("Maximum of 10 team members reached.")
        
        with button_right:
            if st.session_state.member_count > 1:
                remove_member = st.form_submit_button(
                    "− Remove last member",
                    use_container_width=True,
                )

        # --------------------------------------------------
        # PDF UPLOAD
        # --------------------------------------------------

        st.subheader("Upload project abstract")

        uploaded_file = st.file_uploader(
            "Upload Project Abstract (PDF)",
            type=["pdf"],
            accept_multiple_files=False,
            help=f"PDF only, maximum {MAX_PDF_SIZE // (1024 * 1024)} MB.",
        )

        if uploaded_file is not None:
            st.caption(f"Selected file: {uploaded_file.name}")
            st.success("PDF selected and ready for validation.")

        # --------------------------------------------------
        # SUBMIT BUTTON
        # --------------------------------------------------

        submitted = st.form_submit_button(
            "Submit abstract",
            type="primary",
        )

    # ------------------------------------------------------
    # ADD MEMBER ACTION
    # ------------------------------------------------------

    # ------------------------------------------------------
    # MEMBER ACTIONS
    # ------------------------------------------------------
    
    if add_member:
        if st.session_state.member_count < 10:
            st.session_state.member_count += 1
    
        st.rerun()
    
    
    if remove_member:
        if st.session_state.member_count > 1:
            last_index = st.session_state.member_count - 1
    
            # Clear the removed member's saved form values
            st.session_state.pop(f"member_name_{last_index}", None)
            st.session_state.pop(f"member_register_{last_index}", None)
            st.session_state.pop(f"member_year_{last_index}", None)
            st.session_state.pop(f"member_tag_{last_index}", None)
    
            st.session_state.member_count -= 1
    
        st.rerun()

    # ------------------------------------------------------
    # SUBMISSION ACTION
    # ------------------------------------------------------

    if not submitted:
        return

    # ------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------

    errors: list[str] = []

    if domain == "Select a domain":
        errors.append("Select a domain.")

    if not team_name.strip():
        errors.append("Enter a team name.")

    if not project_title.strip():
        errors.append("Enter a project title.")

    if not team_leader_email.strip():
        errors.append("Enter the Team Leader Gmail.")
    elif not team_leader_email.lower().endswith("@gmail.com"):
        errors.append("Enter a valid Gmail address.")

    if not project_tags:
        errors.append("Select at least one project TAG.")

    if not members or len(members) > 10:
        errors.append("A team must have between 1 and 10 members.")

    # ------------------------------------------------------
    # TEAM MEMBER VALIDATION
    # ------------------------------------------------------

    register_numbers: list[str] = []

    for index, member in enumerate(members, start=1):

        if not member["name"].strip():
            errors.append(
                f"Enter a name for team member {index}."
            )

        if not member["register_number"].strip():
            errors.append(
                f"Enter a register number for team member {index}."
            )

        if member["year"] == "Select year":
            errors.append(
                f"Select a year for team member {index}."
            )

        if member["tag"] == "Select TAG":
            errors.append(
                f"Select a TAG for team member {index}."
            )

        normalized_register = (
            member["register_number"].strip().casefold()
        )

        if normalized_register:
            register_numbers.append(normalized_register)

    if len(register_numbers) != len(set(register_numbers)):
        errors.append(
            "Register numbers must be unique within the team."
        )

    # ------------------------------------------------------
    # PDF VALIDATION
    # ------------------------------------------------------

    pdf_bytes = (
        uploaded_file.getvalue()
        if uploaded_file is not None
        else b""
    )

    if uploaded_file is None:

        errors.append(
            "Upload the project abstract PDF."
        )

    else:

        pdf_error = validate_pdf(
            uploaded_file.name,
            pdf_bytes,
        )

        if pdf_error:
            errors.append(pdf_error)

    # ------------------------------------------------------
    # SHOW ERRORS
    # ------------------------------------------------------

    if errors:

        st.warning(
            "Please complete the following required fields:"
        )

        for error in errors:
            st.markdown(f"- {error}")

        return

    # ------------------------------------------------------
    # SAVE SUBMISSION
    # ------------------------------------------------------

    temp_path = None
    submission_id = None

    try:

        temp_path = storage.save_temp_pdf(pdf_bytes)

        submission_id = database.create_submission(
            domain=domain,
            team_name=team_name,
            project_title=project_title,
            abstract=abstract,
            guide=team_leader_email,
            tags=project_tags,
            pdf_filename=safe_filename(
                uploaded_file.name,
                fallback="abstract.pdf",
            ),
            pdf_path=str(temp_path),
            members=members,
        )

        final_path = storage.finalize_pdf(
            temp_path,
            submission_id,
            domain,
            team_name,
            project_title,
        )

        database.update_pdf_path(
            submission_id,
            str(final_path),
        )

        st.session_state.last_submission_id = submission_id
        st.session_state.show_submission_celebration = True

        # Reset for next submission
        st.session_state.member_count = 1

        st.session_state.page = "Confirmation"

        st.rerun()

    except database.DuplicateSubmissionError:

        if temp_path:
            storage.remove_file(temp_path)

        st.error(
            "A submission for this team and domain already exists. "
            "Please contact the SIGMA coordinator if you need to "
            "replace or update your submission."
        )

    except (OSError, ValueError):

        if temp_path:
            storage.remove_file(temp_path)

        if submission_id:
            database.delete_submission(submission_id)

        st.error(
            "We could not save this submission. Please try again."
        )

    except Exception:

        if temp_path:
            storage.remove_file(temp_path)

        if submission_id:
            database.delete_submission(submission_id)

        st.error(
            "We could not save this submission. Please try again."
        )

def render_confirmation() -> None:
    submission_id = st.session_state.get("last_submission_id")
    submission = database.get_submission(submission_id) if submission_id else None
    if submission is None:
        st.warning("The acknowledgement is no longer available in this session.")
        if st.button("Return home"):
            go_to("Home")
        return

    if st.session_state.pop("show_submission_celebration", False):
        st.balloons()
        st.toast("Congratulations! Your team has been added successfully.", icon="🎉")
    
    st.success("🎉 Congratulations! Your team has been added successfully.")
    st.header("Submission Successful")
    st.write(
        "Your project abstract and team details have been successfully recorded "
        "in the SIGMA submission portal."
    )
    summary = {
        "Submission ID": submission["submission_id"],
        "Team Name": submission["team_name"],
        "Domain": submission["domain"],
        "Project": submission["project_title"],
        "Members": submission["member_count"],
        "Submitted On": display_timestamp(submission),
    }
    st.table(pd.DataFrame([summary]).T.rename(columns={0: "Details"}))
    st.download_button(
        "Download acknowledgement",
        data=build_acknowledgement(submission),
        file_name=f"{submission['submission_id']}_acknowledgement.txt",
        mime="text/plain",
        type="primary",
    )
    st.info("Save your Submission ID. You may now close this page.")
    if st.button("Submit another abstract"):
        st.session_state.pop("last_submission_id", None)
        go_to("Submit Abstract")


def render_admin_login() -> None:
    render_brand_header()
    st.header("Admin login")
    st.write("Sign in to manage submissions and download collected data.")
    with st.form("admin_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login = st.form_submit_button("Sign in", type="primary")
    if login:
        expected_username, expected_password = get_admin_credentials()
        if hmac.compare_digest(username.strip(), expected_username) and hmac.compare_digest(
            password, expected_password
        ):
            st.session_state.admin_authenticated = True
            st.session_state.page = "Admin Dashboard"
            st.rerun()
        st.error("Invalid username or password.")


def filtered_submissions(submissions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not submissions:
        return []
    st.subheader("Filters")
    filter_columns = st.columns(5)
    domains = sorted({item["domain"] for item in submissions})
    with filter_columns[0]:
        domain_filter = st.multiselect("Domain", domains)
    with filter_columns[1]:
        year_filter = st.multiselect(
            "Year",
            sorted({year for item in submissions for year in item["years"]}),
        )
    with filter_columns[2]:
        tag_filter = st.multiselect(
            "TAG",
            sorted(
                {
                    tag
                    for item in submissions
                    for tag in (item["tags"] + item["member_tags"])
                }
            ),
        )
    with filter_columns[3]:
        team_filter = st.text_input("Team name contains")
    with filter_columns[4]:
        title_filter = st.text_input("Project title contains")

    available_dates = sorted(
        date.fromisoformat(item["submission_date"]) for item in submissions
    )
    date_start, date_end = st.date_input(
        "Submission date range",
        value=(available_dates[0], available_dates[-1]),
        min_value=available_dates[0],
        max_value=available_dates[-1],
    )
    if not isinstance(date_end, date):
        date_end = date_start

    filtered = []
    for item in submissions:
        item_date = date.fromisoformat(item["submission_date"])
        combined_tags = set(item["tags"] + item["member_tags"])
        if domain_filter and item["domain"] not in domain_filter:
            continue
        if year_filter and not set(year_filter).intersection(item["years"]):
            continue
        if tag_filter and not set(tag_filter).intersection(combined_tags):
            continue
        if team_filter.casefold() not in item["team_name"].casefold():
            continue
        if title_filter.casefold() not in item["project_title"].casefold():
            continue
        if not (date_start <= item_date <= date_end):
            continue
        filtered.append(item)
    return filtered


def render_metrics(submissions: list[dict[str, Any]]) -> None:
    today = date.today().isoformat()
    metrics = st.columns(5)
    metrics[0].metric("Total submissions", len(submissions))
    metrics[1].metric("Total domains", len({item["domain"] for item in submissions}))
    metrics[2].metric("Total teams", len({item["team_name"].casefold() for item in submissions}))
    metrics[3].metric(
        "Total students", sum(int(item["member_count"]) for item in submissions)
    )
    metrics[4].metric(
        "Today's submissions",
        sum(1 for item in submissions if item["submission_date"] == today),
    )


def render_pdf_preview(pdf_bytes: bytes) -> None:
    """Show the embedded viewer when available without breaking admin pages."""

    try:
        if hasattr(st, "pdf"):
            st.pdf(pdf_bytes)
        else:
            st.info("PDF preview is unavailable. Use the download button below.")
    except StreamlitAPIException:
        st.info(
            "PDF preview is unavailable in this environment. "
            "Use the download button below to open the PDF."
        )


def render_submission_detail(submission: dict[str, Any]) -> None:
    st.divider()
    st.subheader("Submission details")
    st.caption(f"{submission['submission_id']} · {display_timestamp(submission)}")
    detail_left, detail_right = st.columns(2)
    with detail_left:
        st.markdown(f"**Domain:** {submission['domain']}")
        st.markdown(f"**Team:** {submission['team_name']}")
        st.markdown(f"**Project:** {submission['project_title']}")
        st.markdown(f"**Team Leader Gmail:** {submission['guide']}")
        st.markdown(f"**Project TAGs:** {', '.join(submission['tags'])}")
    with detail_right:
        st.markdown("**Abstract**")
        st.write(submission["abstract"] or "No abstract text entered; refer to the uploaded PDF.")

    st.markdown("**Team members**")
    st.dataframe(
        pd.DataFrame(
            submission["members"],
            columns=["member_number", "name", "register_number", "year", "tag"],
        ).rename(
            columns={
                "member_number": "No.",
                "name": "Name",
                "register_number": "Register Number",
                "year": "Year",
                "tag": "TAG",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    try:
        pdf_bytes = storage.read_pdf(submission["pdf_path"])
        render_pdf_preview(pdf_bytes)
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name=submission["pdf_filename"],
            mime="application/pdf",
        )
    except (FileNotFoundError, ValueError, OSError):
        st.warning("The PDF file is missing from local storage.")

    st.divider()
    if st.button(
        "Cancel and delete this submission",
        key=f"cancel_delete_{submission['submission_id']}",
    ):
        st.session_state.confirm_delete_id = submission["submission_id"]
        st.rerun()

    if st.session_state.get("confirm_delete_id") == submission["submission_id"]:
        st.warning(
            "This permanently deletes the submission record, team members, and stored PDF. "
            "This action cannot be undone."
        )
        keep_column, delete_column = st.columns(2)
        with keep_column:
            if st.button(
                "Keep submission",
                key=f"keep_delete_{submission['submission_id']}",
            ):
                st.session_state.pop("confirm_delete_id", None)
                st.rerun()
        with delete_column:
            if st.button(
                "Delete permanently",
                key=f"confirm_delete_{submission['submission_id']}",
                type="primary",
            ):
                current = database.get_submission(submission["submission_id"])
                database.delete_submission(submission["submission_id"])
                if current:
                    storage.remove_file(current["pdf_path"])
                st.session_state.pop("confirm_delete_id", None)
                st.toast("Submission deleted.")
                st.rerun()


def render_admin_dashboard() -> None:
    st.title("Admin Dashboard")
    st.caption("SIGMA submission monitoring and management")
    submissions = database.list_submissions()
    render_metrics(submissions)
    st.divider()
    st.subheader("Recent submissions")
    if not submissions:
        st.info("No submissions have been received yet.")
        return
    st.dataframe(
        pd.DataFrame(submission_table_rows(submissions[:10])),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Use the Submissions page to filter and inspect the full collection.")


def render_admin_submissions() -> None:
    st.title("Submissions")
    submissions = database.list_submissions()
    if not submissions:
        st.info("No submissions have been received yet.")
        return
    filtered = filtered_submissions(submissions)
    st.dataframe(
        pd.DataFrame(submission_table_rows(filtered)),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Showing {len(filtered)} of {len(submissions)} submissions.")
    if filtered:
        options = [item["submission_id"] for item in filtered]
        selected_id = st.selectbox("Open submission", options)
        selected = database.get_submission(selected_id)
        if selected:
            render_submission_detail(selected)


def render_admin_teams() -> None:
    st.title("Teams")
    submissions = database.list_submissions()
    if not submissions:
        st.info("No teams have been submitted yet.")
        return
    rows = []
    for submission in submissions:
        for member in database.get_submission(submission["submission_id"]).get("members", []):
            rows.append(
                {
                    "Domain": submission["domain"],
                    "Team Name": submission["team_name"],
                    "Project Title": submission["project_title"],
                    "Member": member["name"],
                    "Register Number": member["register_number"],
                    "Year": member["year"],
                    "TAG": member["tag"],
                }
            )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_admin_pdfs() -> None:
    st.title("PDF Library")
    submissions = database.list_submissions()
    if not submissions:
        st.info("No PDFs have been submitted yet.")
        return
    st.write(f"{len(submissions)} abstract PDF(s) are recorded.")
    selected_id = st.selectbox(
        "Select an abstract",
        [item["submission_id"] for item in submissions],
        format_func=lambda value: next(
            (
                f"{item['submission_id']} · {item['team_name']} · {item['pdf_filename']}"
                for item in submissions
                if item["submission_id"] == value
            ),
            value,
        ),
    )
    selected = database.get_submission(selected_id)
    if selected:
        try:
            pdf_bytes = storage.read_pdf(selected["pdf_path"])
            render_pdf_preview(pdf_bytes)
            st.download_button(
                "Download selected PDF",
                data=pdf_bytes,
                file_name=selected["pdf_filename"],
                mime="application/pdf",
                type="primary",
            )
        except (FileNotFoundError, ValueError, OSError):
            st.error("This PDF file is missing from local storage.")


def render_download_data() -> None:
    st.title("Download data")
    submissions = database.list_submissions()
    if not submissions:
        st.info("There is no data to download yet.")
        return
    st.write("Download structured records for reporting or archival.")
    complete_submissions = [
        database.get_submission(item["submission_id"]) for item in submissions
    ]
    complete_submissions = [item for item in complete_submissions if item is not None]
    register_df = submission_register_dataframe(submissions)
    excel_bytes = build_excel(complete_submissions)
    submissions_csv = submissions_dataframe(submissions).to_csv(index=False).encode("utf-8")
    members_csv = members_dataframe(
        complete_submissions
    ).to_csv(index=False).encode("utf-8")
    register_csv = register_df.to_csv(index=False).encode("utf-8")
    zip_bytes, pdf_count = build_pdf_zip(submissions, storage.read_pdf)

    st.subheader("Team submission register")
    st.dataframe(register_df, use_container_width=True, hide_index=True)

    first, second, third = st.columns(3)
    with first:
        st.download_button(
            "Download Excel",
            data=excel_bytes,
            file_name="SIGMA_Submissions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with second:
        st.download_button(
            "Download submissions CSV",
            data=submissions_csv,
            file_name="SIGMA_Submissions.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Download team members CSV",
            data=members_csv,
            file_name="SIGMA_Team_Members.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Download team register CSV",
            data=register_csv,
            file_name="SIGMA_Team_Submission_Register.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with third:
        st.download_button(
            "Download all abstract PDFs",
            data=zip_bytes,
            file_name="SIGMA_Abstract_Submissions.zip",
            mime="application/zip",
            use_container_width=True,
            disabled=pdf_count == 0,
        )
        st.caption(f"{pdf_count} PDF(s) included in the ZIP.")


def render_settings() -> None:
    st.title("Settings")
    st.write("Runtime and storage information for the coordinator.")
    status = storage.storage_status()
    settings = {
        "Database": str(database.DB_PATH),
        "PDF storage": status["root"],
        "Maximum PDF size": f"{MAX_PDF_SIZE // (1024 * 1024)} MB",
        "Available domains": len(DOMAINS),
        "Admin credentials": "Streamlit secrets or local fallback",
    }
    st.table(pd.DataFrame([settings]).T.rename(columns={0: "Value"}))
    st.warning(
        "Local SQLite and file storage are suitable for a prototype or a single persistent "
        "server. Streamlit Cloud local files are not durable across every deployment event; "
        "move the storage adapter to Supabase Storage, Google Drive, or S3 for production."
    )
    st.markdown(
        """
        **Configure admin credentials with Streamlit secrets**

        Add an `admin` section in `.streamlit/secrets.toml`:

        ```toml
        [admin]
        username = "admin"
        password = "replace-with-a-strong-password"
        ```
        """
    )


def render_current_page() -> None:
    page = st.session_state.get("page", "Home")
    if page.startswith("Admin") or page in {
        "Submissions",
        "Teams",
        "PDFs",
        "Download Data",
        "Settings",
    }:
        if not is_admin():
            st.session_state.page = "Admin Login"
            render_admin_login()
            return
    pages = {
        "Home": render_home,
        "Submit Abstract": render_submit,
        "Guidelines": render_guidelines,
        "Confirmation": render_confirmation,
        "Admin Login": render_admin_login,
        "Admin Dashboard": render_admin_dashboard,
        "Submissions": render_admin_submissions,
        "Teams": render_admin_teams,
        "PDFs": render_admin_pdfs,
        "Download Data": render_download_data,
        "Settings": render_settings,
    }
    pages.get(page, render_home)()


if "page" not in st.session_state:
    st.session_state.page = "Home"

render_sidebar()
render_current_page()
