from dataclasses import dataclass


VALID_PRIORITIES = {
    "Low",
    "Medium",
    "High",
    "Critical",
}


@dataclass
class PriorityResult:
    priority: str
    reason: str
    overridden: bool


CRITICAL_KEYWORDS = [
    "all employees",
    "all users",
    "entire company",
    "company-wide",
    "company wide",
    "organization-wide",
    "organisation-wide",
    "ransomware",
    "active security breach",
    "major data loss",
]

HIGH_KEYWORDS = [
    "multiple users",
    "several users",
    "entire department",
    "whole department",
    "vip user",
    "urgent work blocked",
    "security risk",
]

LOW_KEYWORDS = [
    "information request",
    "desktop shortcut",
    "cosmetic issue",
    "non-urgent",
    "how do i",
    "how can i",
]


def contains_keyword(ticket: str, keywords: list[str]) -> bool:
    normalized_ticket = ticket.lower()

    return any(
        keyword.lower() in normalized_ticket
        for keyword in keywords
    )


def determine_priority(
    ticket: str,
    ai_priority: str,
    ai_reason: str,
    reply_language: str,
) -> PriorityResult:
    normalized_priority = ai_priority.strip().title()

    if normalized_priority not in VALID_PRIORITIES:
        normalized_priority = "Medium"

    is_german = reply_language.strip().lower() == "german"

    if contains_keyword(ticket, CRITICAL_KEYWORDS):
        reason = (
            "Das Ticket weist auf einen unternehmensweiten Ausfall, "
            "einen schwerwiegenden Sicherheitsvorfall oder eine "
            "vergleichbar kritische Auswirkung hin."
            if is_german
            else (
                "The ticket indicates a company-wide outage, "
                "major security incident, or similarly critical impact."
            )
        )

        return PriorityResult(
            priority="Critical",
            reason=reason,
            overridden=normalized_priority != "Critical",
        )

    if contains_keyword(ticket, HIGH_KEYWORDS):
        reason = (
            "Das Ticket betrifft mehrere Benutzer, eine gesamte Abteilung "
            "oder weist auf ein dringendes Sicherheitsrisiko hin."
            if is_german
            else (
                "The ticket indicates multiple affected users, "
                "department-level impact, or an urgent security risk."
            )
        )

        return PriorityResult(
            priority="High",
            reason=reason,
            overridden=normalized_priority not in {
                "High",
                "Critical",
            },
        )

    if contains_keyword(ticket, LOW_KEYWORDS):
        reason = (
            "Das Ticket scheint eine kleinere, informative, kosmetische "
            "oder nicht dringende Anfrage zu sein."
            if is_german
            else (
                "The ticket appears to be a minor, informational, "
                "cosmetic, or non-urgent request."
            )
        )

        return PriorityResult(
            priority="Low",
            reason=reason,
            overridden=normalized_priority != "Low",
        )

    return PriorityResult(
        priority=normalized_priority,
        reason=ai_reason,
        overridden=False,
    )