SENSITIVE_CATEGORIES = frozenset({
    "customer_data", "financial_data", "private_report", "sensitive",
})


def default_risk_level(event_type: str, resource_category: str | None, provided: str | None) -> str:
    if provided:
        return provided
    if event_type == "file.downloaded" and resource_category in SENSITIVE_CATEGORIES:
        return "high"
    if event_type == "user.login_failed":
        return "medium"
    if event_type == "role.changed":
        return "high"
    if event_type in ("sensitive_download.detected", "failed_access_spike.detected"):
        return "high"
    return "low"
