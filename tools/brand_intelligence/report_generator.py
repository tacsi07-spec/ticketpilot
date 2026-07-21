from __future__ import annotations

from html import escape
from pathlib import Path

from tools.brand_intelligence.models import (
    BrandCandidate,
    CheckStatus,
)


class HtmlReportGenerator:
    """HTML-riport készítése egy BrandCandidate objektumból."""

    STATUS_LABELS = {
        CheckStatus.CLEAR: "Low risk",
        CheckStatus.WARNING: "Warning",
        CheckStatus.CONFLICT: "Conflict",
        CheckStatus.UNKNOWN: "Unknown",
        CheckStatus.MANUAL_REVIEW: "Manual review",
    }

    STATUS_ICONS = {
        CheckStatus.CLEAR: "✓",
        CheckStatus.WARNING: "!",
        CheckStatus.CONFLICT: "×",
        CheckStatus.UNKNOWN: "?",
        CheckStatus.MANUAL_REVIEW: "⚖",
    }

    def render(
        self,
        candidate: BrandCandidate,
    ) -> str:
        """A teljes HTML-dokumentum előállítása."""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>{escape(candidate.name)} – Brand Intelligence Report</title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            background: #f3f5f9;
            color: #182230;
            font-family:
                Inter,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
            line-height: 1.6;
        }}

        .page {{
            width: min(1100px, calc(100% - 32px));
            margin: 40px auto;
        }}

        .hero {{
            padding: 42px;
            border-radius: 24px;
            color: white;
            background:
                linear-gradient(
                    135deg,
                    #172554,
                    #2563eb
                );
            box-shadow:
                0 24px 60px rgba(30, 64, 175, 0.22);
        }}

        .eyebrow {{
            margin: 0 0 10px;
            color: #bfdbfe;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}

        h1 {{
            margin: 0;
            font-size: clamp(38px, 7vw, 68px);
            line-height: 1.05;
        }}

        .hero-subtitle {{
            max-width: 680px;
            margin: 18px 0 0;
            color: #dbeafe;
            font-size: 17px;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 28px;
        }}

        .summary-card {{
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.10);
            backdrop-filter: blur(8px);
        }}

        .summary-label {{
            margin-bottom: 6px;
            color: #bfdbfe;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .summary-value {{
            font-size: 25px;
            font-weight: 750;
        }}

        .section {{
            margin-top: 24px;
            padding: 30px;
            border: 1px solid #e4e7ec;
            border-radius: 20px;
            background: white;
            box-shadow:
                0 8px 28px rgba(16, 24, 40, 0.06);
        }}

        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 22px;
        }}

        .section h2 {{
            margin: 0;
            font-size: 23px;
        }}

        .section-description {{
            margin: 4px 0 0;
            color: #667085;
            font-size: 14px;
        }}

        .score {{
            min-width: 72px;
            padding: 8px 12px;
            border-radius: 999px;
            background: #eff6ff;
            color: #1d4ed8;
            font-size: 14px;
            font-weight: 700;
            text-align: center;
        }}

        .result-list {{
            display: grid;
            gap: 12px;
        }}

        .result-card {{
            padding: 18px;
            border: 1px solid #eaecf0;
            border-radius: 14px;
            background: #fcfcfd;
        }}

        .result-top {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 14px;
        }}

        .result-title {{
            margin: 0;
            font-size: 17px;
            font-weight: 700;
            overflow-wrap: anywhere;
        }}

        .result-meta {{
            margin-top: 5px;
            color: #667085;
            font-size: 14px;
        }}

        .result-details {{
            margin: 12px 0 0;
            color: #475467;
            font-size: 14px;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }}

        .status-clear {{
            background: #ecfdf3;
            color: #027a48;
        }}

        .status-warning {{
            background: #fffaeb;
            color: #b54708;
        }}

        .status-conflict {{
            background: #fef3f2;
            color: #b42318;
        }}

        .status-unknown,
        .status-manual-review {{
            background: #f2f4f7;
            color: #344054;
        }}

        .empty-state {{
            padding: 20px;
            border: 1px dashed #d0d5dd;
            border-radius: 14px;
            color: #667085;
            text-align: center;
        }}

        .recommendation {{
            padding: 24px;
            border-radius: 16px;
        }}

        .recommendation-positive {{
            border: 1px solid #a6f4c5;
            background: #ecfdf3;
            color: #05603a;
        }}

        .recommendation-negative {{
            border: 1px solid #fecdca;
            background: #fef3f2;
            color: #912018;
        }}

        .recommendation h3 {{
            margin: 0 0 8px;
        }}

        .recommendation p {{
            margin: 0;
        }}

        .rejection-list {{
            margin: 18px 0 0;
            padding-left: 20px;
        }}

        .legal-summary {{
            margin-bottom: 18px;
            padding: 18px;
            border-radius: 14px;
            background: #f8fafc;
        }}

        .legal-summary p {{
            margin: 5px 0;
        }}

        .sources {{
            margin-top: 18px;
            color: #667085;
            font-size: 13px;
        }}

        .disclaimer {{
            margin-top: 26px;
            padding: 20px;
            border-radius: 14px;
            background: #f9fafb;
            color: #667085;
            font-size: 13px;
        }}

        a {{
            color: #175cd3;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        footer {{
            padding: 28px 10px;
            color: #98a2b3;
            font-size: 13px;
            text-align: center;
        }}

        @media (max-width: 640px) {{
            .page {{
                width: min(100% - 20px, 1100px);
                margin: 10px auto;
            }}

            .hero,
            .section {{
                padding: 22px;
                border-radius: 16px;
            }}

            .section-header,
            .result-top {{
                align-items: flex-start;
                flex-direction: column;
            }}
        }}

        @media print {{
            body {{
                background: white;
            }}

            .page {{
                width: 100%;
                margin: 0;
            }}

            .hero,
            .section {{
                box-shadow: none;
                break-inside: avoid;
            }}
        }}
    </style>
</head>

<body>
    <main class="page">
        {self._render_hero(candidate)}
        {self._render_domains(candidate)}
        {self._render_companies(candidate)}
        {self._render_similarity(candidate)}
        {self._render_legal(candidate)}
        {self._render_final_recommendation(candidate)}

        <footer>
            Generated by TicketPilot Brand Intelligence
        </footer>
    </main>
</body>
</html>
"""

    def save(
        self,
        candidate: BrandCandidate,
        output_path: str | Path,
    ) -> Path:
        """A riport mentése HTML-fájlba."""

        path = Path(output_path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            self.render(candidate),
            encoding="utf-8",
        )

        return path.resolve()

    def _render_hero(
        self,
        candidate: BrandCandidate,
    ) -> str:
        recommendation = (
            "Rejected"
            if candidate.rejected
            else "Recommended"
        )

        recommendation_class = (
            "status-conflict"
            if candidate.rejected
            else "status-clear"
        )

        return f"""
<section class="hero">
    <p class="eyebrow">Brand Intelligence Report</p>
    <h1>{escape(candidate.name)}</h1>

    <p class="hero-subtitle">
        Domain, company, similarity and preliminary legal
        risk assessment.
    </p>

    <div class="summary-grid">
        <div class="summary-card">
            <div class="summary-label">Overall score</div>
            <div class="summary-value">
                {candidate.final_score:.2f} / 10
            </div>
        </div>

        <div class="summary-card">
            <div class="summary-label">Recommendation</div>
            <div class="summary-value">
                <span class="badge {recommendation_class}">
                    {recommendation}
                </span>
            </div>
        </div>

        <div class="summary-card">
            <div class="summary-label">Domain score</div>
            <div class="summary-value">
                {candidate.domain_score:.2f} / 10
            </div>
        </div>

        <div class="summary-card">
            <div class="summary-label">Legal score</div>
            <div class="summary-value">
                {candidate.trademark_score:.2f} / 10
            </div>
        </div>
    </div>
</section>
"""

    def _render_domains(
        self,
        candidate: BrandCandidate,
    ) -> str:
        cards: list[str] = []

        for result in candidate.domains:
            details = (
                f'<p class="result-details">'
                f'{escape(result.details)}</p>'
                if result.details
                else ""
            )

            availability = ""

            if result.possibly_available is True:
                availability = "Possibly available"
            elif result.possibly_available is False:
                availability = "Likely registered"

            meta_parts = [
                result.extension,
                availability,
            ]

            meta = " · ".join(
                escape(part)
                for part in meta_parts
                if part
            )

            cards.append(
                f"""
<div class="result-card">
    <div class="result-top">
        <div>
            <p class="result-title">
                {escape(result.domain)}
            </p>
            <div class="result-meta">{meta}</div>
        </div>
        {self._status_badge(result.status)}
    </div>
    {details}
</div>
"""
            )

        return self._section(
            title="Domains",
            description=(
                "Availability signals for relevant domain extensions."
            ),
            score=candidate.domain_score,
            body=self._cards_or_empty(
                cards,
                "No domain results available.",
            ),
        )

    def _render_companies(
        self,
        candidate: BrandCandidate,
    ) -> str:
        cards: list[str] = []

        for match in candidate.company_matches:
            title = escape(match.name)

            if match.website:
                safe_url = escape(
                    match.website,
                    quote=True,
                )
                title = (
                    f'<a href="{safe_url}" '
                    f'target="_blank" '
                    f'rel="noopener noreferrer">'
                    f'{title}</a>'
                )

            meta_parts = [
                match.industry,
                match.country,
                f"Similarity: {match.similarity_score:.0f}%",
            ]

            meta = " · ".join(
                escape(str(part))
                for part in meta_parts
                if part
            )

            details = (
                f'<p class="result-details">'
                f'{escape(match.details)}</p>'
                if match.details
                else ""
            )

            cards.append(
                f"""
<div class="result-card">
    <div class="result-top">
        <div>
            <p class="result-title">{title}</p>
            <div class="result-meta">{meta}</div>
        </div>
        {self._status_badge(match.conflict_risk)}
    </div>
    {details}
</div>
"""
            )

        return self._section(
            title="Company check",
            description=(
                "Existing companies and products with potentially "
                "conflicting names."
            ),
            score=candidate.company_conflict_score,
            body=self._cards_or_empty(
                cards,
                "No credible company conflicts found.",
            ),
        )

    def _render_similarity(
        self,
        candidate: BrandCandidate,
    ) -> str:
        cards: list[str] = []

        for result in candidate.similarity_results:
            meta = (
                f"Final similarity: {result.final_score:.0f}% · "
                f"Phonetic: {result.phonetic_score:.0f}% · "
                f"Visual: {result.ratio_score:.0f}%"
            )

            details = (
                f'<p class="result-details">'
                f'{escape(result.details)}</p>'
                if result.details
                else ""
            )

            cards.append(
                f"""
<div class="result-card">
    <div class="result-top">
        <div>
            <p class="result-title">
                {escape(result.candidate_name)}
                &nbsp;↔&nbsp;
                {escape(result.compared_name)}
            </p>
            <div class="result-meta">
                {escape(meta)}
            </div>
        </div>
        {self._status_badge(result.status)}
    </div>
    {details}
</div>
"""
            )

        return self._section(
            title="Name similarity",
            description=(
                "Visual, phonetic and structural similarity analysis."
            ),
            score=candidate.similarity_score,
            body=self._cards_or_empty(
                cards,
                "No company names were available for similarity analysis.",
            ),
        )

    def _render_legal(
        self,
        candidate: BrandCandidate,
    ) -> str:
        if not candidate.legal_results:
            return self._section(
                title="Legal intelligence",
                description=(
                    "Preliminary trademark and legal research."
                ),
                score=candidate.trademark_score,
                body=self._empty_state(
                    "No legal research result available."
                ),
            )

        result_blocks: list[str] = []

        for legal_result in candidate.legal_results:
            match_cards: list[str] = []

            for match in legal_result.matches:
                title = escape(match.name)

                if match.source_url:
                    safe_url = escape(
                        match.source_url,
                        quote=True,
                    )
                    title = (
                        f'<a href="{safe_url}" '
                        f'target="_blank" '
                        f'rel="noopener noreferrer">'
                        f'{title}</a>'
                    )

                meta_parts = [
                    match.database,
                    match.jurisdiction,
                    match.status_text,
                    (
                        f"Similarity: "
                        f"{match.similarity_score:.0f}%"
                    ),
                    (
                        f"Industry overlap: "
                        f"{match.industry_overlap_score:.0f}%"
                    ),
                ]

                meta = " · ".join(
                    escape(str(part))
                    for part in meta_parts
                    if part
                )

                extra_details: list[str] = []

                if match.owner:
                    extra_details.append(
                        f"Owner: {match.owner}"
                    )

                if match.registration_number:
                    extra_details.append(
                        "Registration/application: "
                        f"{match.registration_number}"
                    )

                if match.goods_services:
                    extra_details.append(
                        "Goods and services: "
                        f"{match.goods_services}"
                    )

                if match.details:
                    extra_details.append(match.details)

                details_html = "".join(
                    f'<p class="result-details">'
                    f'{escape(detail)}</p>'
                    for detail in extra_details
                )

                match_cards.append(
                    f"""
<div class="result-card">
    <div class="result-top">
        <div>
            <p class="result-title">{title}</p>
            <div class="result-meta">{meta}</div>
        </div>
        {self._status_badge(match.conflict_risk)}
    </div>
    {details_html}
</div>
"""
                )

            sources = ""

            if legal_result.sources_checked:
                source_text = ", ".join(
                    escape(source)
                    for source in legal_result.sources_checked
                )
                sources = (
                    f'<div class="sources">'
                    f'<strong>Sources checked:</strong> '
                    f'{source_text}</div>'
                )

            result_blocks.append(
                f"""
<div class="legal-summary">
    <p>
        <strong>Status:</strong>
        {escape(self._status_label(legal_result.status))}
    </p>
    <p>
        <strong>Summary:</strong>
        {escape(legal_result.summary or "No summary provided.")}
    </p>
    <p>
        <strong>Recommendation:</strong>
        {escape(
            legal_result.recommendation
            or "Manual legal review is recommended."
        )}
    </p>
    {sources}
</div>

<div class="result-list">
    {self._cards_or_empty(
        match_cards,
        "No credible trademark matches found.",
    )}
</div>

<div class="disclaimer">
    {escape(legal_result.disclaimer)}
</div>
"""
            )

        return self._section(
            title="Legal intelligence",
            description=(
                "Preliminary trademark research based on public sources."
            ),
            score=candidate.trademark_score,
            body="".join(result_blocks),
        )

    def _render_final_recommendation(
        self,
        candidate: BrandCandidate,
    ) -> str:
        if candidate.rejected:
            reasons = "".join(
                f"<li>{escape(reason)}</li>"
                for reason in candidate.rejection_reasons
            )

            body = f"""
<div class="recommendation recommendation-negative">
    <h3>Not recommended without further review</h3>
    <p>
        One or more high-risk findings were identified.
    </p>
    <ul class="rejection-list">
        {reasons}
    </ul>
</div>
"""
        else:
            body = """
<div class="recommendation recommendation-positive">
    <h3>Recommended for continued evaluation</h3>
    <p>
        No automatic rejection reason was identified.
        Final human and legal review is still recommended
        before registration or commercial launch.
    </p>
</div>
"""

        return self._section(
            title="Final recommendation",
            description=(
                "Consolidated outcome of the automated analysis."
            ),
            score=None,
            body=body,
        )

    def _section(
        self,
        title: str,
        description: str,
        body: str,
        score: float | None,
    ) -> str:
        score_html = ""

        if score is not None:
            score_html = (
                f'<div class="score">{score:.2f} / 10</div>'
            )

        return f"""
<section class="section">
    <div class="section-header">
        <div>
            <h2>{escape(title)}</h2>
            <p class="section-description">
                {escape(description)}
            </p>
        </div>
        {score_html}
    </div>

    {body}
</section>
"""

    def _status_badge(
        self,
        status: CheckStatus,
    ) -> str:
        label = escape(self._status_label(status))
        icon = escape(
            self.STATUS_ICONS.get(status, "?")
        )
        css_class = self._status_css_class(status)

        return (
            f'<span class="badge {css_class}">'
            f"{icon} {label}"
            f"</span>"
        )

    def _status_label(
        self,
        status: CheckStatus,
    ) -> str:
        return self.STATUS_LABELS.get(
            status,
            status.value.replace("_", " ").title(),
        )

    @staticmethod
    def _status_css_class(
        status: CheckStatus,
    ) -> str:
        return (
            "status-"
            + status.value.replace("_", "-")
        )

    def _cards_or_empty(
        self,
        cards: list[str],
        empty_message: str,
    ) -> str:
        if not cards:
            return self._empty_state(empty_message)

        return (
            '<div class="result-list">'
            + "".join(cards)
            + "</div>"
        )

    @staticmethod
    def _empty_state(
        message: str,
    ) -> str:
        return (
            '<div class="empty-state">'
            f"{escape(message)}"
            "</div>"
        )