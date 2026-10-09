import re
from datetime import datetime, timezone
from typing import Optional, Any


def _format_ics_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _escape_ics_text(text: Optional[str]) -> str:
    if not text:
        return ""
    clean = str(text)
    clean = clean.replace("\\", "\\\\")
    clean = clean.replace(";", "\\;")
    clean = clean.replace(",", "\\,")
    clean = clean.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    return clean


def generate_ics_calendar(interview: Any) -> str:
    now_str = _format_ics_datetime(datetime.now(timezone.utc))
    start_dt = getattr(interview, "scheduled_at", None)

    if not start_dt and getattr(interview, "slots", None):
        for slot in interview.slots:
            if getattr(slot, "is_selected", False):
                start_dt = slot.start_time
                break
        if not start_dt and len(interview.slots) > 0:
            start_dt = interview.slots[0].start_time

    if not start_dt:
        start_dt = datetime.now(timezone.utc)

    duration = getattr(interview, "duration_minutes", 45) or 45
    end_dt = getattr(interview, "end_time", None)
    if not end_dt and hasattr(start_dt, "timestamp"):
        from datetime import timedelta
        end_dt = start_dt + timedelta(minutes=duration)

    start_str = _format_ics_datetime(start_dt)
    end_str = _format_ics_datetime(end_dt)

    job_title = getattr(interview, "job_title", "")
    if not job_title and getattr(interview, "job", None):
        job_title = getattr(interview.job, "title", "Job Position")

    company_name = getattr(interview, "company_name", "")
    if not company_name and getattr(interview, "company", None):
        company_profile = getattr(interview.company, "company_profile", None)
        company_name = getattr(company_profile, "company_name", None) or f"{interview.company.first_name} {interview.company.last_name}"

    candidate_name = getattr(interview, "candidate_name", "")
    if not candidate_name and getattr(interview, "candidate", None):
        candidate_name = f"{interview.candidate.first_name} {interview.candidate.last_name}"

    candidate_email = getattr(interview, "candidate_email", "")
    if not candidate_email and getattr(interview, "candidate", None):
        candidate_email = interview.candidate.email or ""

    company_email = ""
    if getattr(interview, "company", None):
        company_email = interview.company.email or ""

    interview_type = getattr(interview, "interview_type", "Company Interview")
    meeting_platform = getattr(interview, "meeting_platform", "Google Meet")
    meeting_link = getattr(interview, "meeting_link", "") or ""
    location = getattr(interview, "location", "") or meeting_link or "Virtual (Google Meet)"

    summary = f"{interview_type}: {candidate_name} - {company_name} ({job_title})"
    description = (
        f"Interview for position: {job_title}\\n"
        f"Company: {company_name}\\n"
        f"Candidate: {candidate_name}\\n"
        f"Platform: {meeting_platform}\\n"
        f"Meeting Link: {meeting_link}\\n"
        f"Duration: {duration} minutes"
    )
    if getattr(interview, "notes", None):
        description += f"\\nNotes: {_escape_ics_text(interview.notes)}"

    uid = f"interview-{getattr(interview, 'id', 1)}-{now_str}@skill2career.com"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Skill2Career//Interview Scheduling System//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_str}",
        f"DTSTART:{start_str}",
        f"DTEND:{end_str}",
        f"SUMMARY:{_escape_ics_text(summary)}",
        f"DESCRIPTION:{description}",
        f"LOCATION:{_escape_ics_text(location)}",
        "STATUS:CONFIRMED",
    ]

    if company_email:
        lines.append(f"ORGANIZER;CN={_escape_ics_text(company_name)}:mailto:{company_email}")
    if candidate_email:
        lines.append(f"ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;CN={_escape_ics_text(candidate_name)}:mailto:{candidate_email}")

    lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    lines.append("")

    return "\r\n".join(lines)


generate_interview_ics = generate_ics_calendar
