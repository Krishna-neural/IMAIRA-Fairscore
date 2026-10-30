"""CSS styling and design tokens for the IMAIRA-Fairscore AI Mock Interviewer."""

CUSTOM_CSS = """
<style>
/* Global App Container */
.main .block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 1080px;
}

/* Header & Hero */
.imaira-header {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    color: #f8fafc;
}
.imaira-header h1 {
    font-size: 1.85rem;
    font-weight: 700;
    margin: 0;
    color: #38bdf8;
}
.imaira-header p {
    margin: 0.4rem 0 0 0;
    color: #94a3b8;
    font-size: 0.95rem;
}

/* Badge styles */
.badge {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-right: 0.4rem;
}
.badge-category { background-color: #0369a1; color: #e0f2fe; }
.badge-intermediate { background-color: #0d9488; color: #ccfbf1; }
.badge-advanced { background-color: #d97706; color: #fef3c7; }
.badge-expert { background-color: #dc2626; color: #fee2e2; }
.badge-online { background-color: #16a34a; color: #dcfce7; }
.badge-direct { background-color: #6366f1; color: #e0e7ff; }

/* Question Card */
.question-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 5px solid #0284c7;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
@media (prefers-color-scheme: dark) {
    .question-card {
        background-color: #1e293b;
        border-color: #334155;
        border-left-color: #38bdf8;
    }
}
.question-prompt {
    font-size: 1.18rem;
    font-weight: 600;
    line-height: 1.5;
    margin: 0.6rem 0;
}

/* Score Card */
.score-metric-box {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
@media (prefers-color-scheme: dark) {
    .score-metric-box {
        background-color: #1e293b;
        border-color: #334155;
    }
}
.score-number {
    font-size: 2.1rem;
    font-weight: 800;
    color: #0284c7;
    line-height: 1.1;
}
.score-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    font-weight: 600;
    color: #64748b;
    margin-top: 0.2rem;
}

/* Proposition Card */
.proposition-card {
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    border: 1px solid #e2e8f0;
}
.prop-covered {
    background-color: #f0fdf4;
    border-color: #bbf7d0;
    color: #166534;
}
.prop-partial {
    background-color: #fffbeb;
    border-color: #fde68a;
    color: #92400e;
}
.prop-missing {
    background-color: #fef2f2;
    border-color: #fecaca;
    color: #991b1b;
}

/* Coaching Feedback Card */
.feedback-box {
    background-color: #fdf4ff;
    border: 1px solid #f0abfc;
    border-left: 4px solid #c026d3;
    border-radius: 6px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.75rem;
}
.feedback-quote {
    font-style: italic;
    color: #475569;
    font-size: 0.88rem;
    margin-bottom: 0.3rem;
}
.feedback-fix {
    font-weight: 600;
    color: #86198f;
    font-size: 0.95rem;
}

/* Fairness Note */
.fairness-banner {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 0.85rem 1.2rem;
    margin-top: 1rem;
    font-size: 0.88rem;
    color: #1e40af;
}
</style>
"""
