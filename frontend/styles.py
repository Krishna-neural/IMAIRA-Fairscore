"""CSS styling and design tokens for the IMAIRA-Fairscore AI Mock Interviewer.
Theme 6: Professional & Corporate (Enterprise Assessment Platform).
"""

CUSTOM_CSS = """
<style>
/* Global App Container */
.main .block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 1100px;
}

/* Header & Hero */
.imaira-header {
    background-color: #101C35;
    border: 1px solid #172846;
    border-radius: 8px;
    padding: 1.75rem 2rem;
    margin-bottom: 1.5rem;
    color: #FFFFFF;
}
.imaira-header h1 {
    font-size: 1.85rem;
    font-weight: 800;
    margin: 0;
    color: #FFFFFF;
    letter-spacing: -0.02em;
}
.imaira-header p {
    margin: 0.4rem 0 0 0;
    color: #94A3B8;
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
.badge-category { background-color: #EDF3FA; color: #2457A6; border: 1px solid #D0E1F9; }
.badge-intermediate { background-color: #E2E8F0; color: #101C35; border: 1px solid #CBD5E1; }
.badge-advanced { background-color: #FFF8E1; color: #D99A27; border: 1px solid #FFE082; }
.badge-expert { background-color: #FFEBEE; color: #D9534F; border: 1px solid #FFCDD2; }
.badge-online { background-color: #E8F5E9; color: #198754; border: 1px solid #C8E6C9; }
.badge-direct { background-color: #EDF3FA; color: #2457A6; border: 1px solid #D0E1F9; }

/* Question Card */
.question-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 5px solid #2457A6;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 3px rgba(16, 28, 53, 0.06);
}
.question-prompt {
    font-size: 1.18rem;
    font-weight: 700;
    line-height: 1.5;
    margin: 0.6rem 0;
    color: #101C35;
}

/* Score Card */
.score-metric-box {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 1.25rem;
    text-align: center;
}
.score-number {
    font-size: 2.25rem;
    font-weight: 800;
    color: #2457A6;
    line-height: 1.1;
}
.score-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    font-weight: 700;
    color: #17243A;
    margin-top: 0.25rem;
}

/* Proposition Card */
.proposition-card {
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    border: 1px solid #E2E8F0;
}
.prop-covered {
    background-color: #E8F5E9;
    border-color: #C8E6C9;
    color: #198754;
    font-weight: 600;
}
.prop-partial {
    background-color: #FFF8E1;
    border-color: #FFE082;
    color: #D99A27;
    font-weight: 600;
}
.prop-missing {
    background-color: #FFEBEE;
    border-color: #FFCDD2;
    color: #D9534F;
    font-weight: 600;
}

/* Coaching Feedback Card */
.feedback-box {
    background-color: #EDF3FA;
    border: 1px solid #D0E1F9;
    border-left: 4px solid #2457A6;
    border-radius: 6px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.75rem;
}
.feedback-quote {
    font-style: italic;
    color: #65748B;
    font-size: 0.88rem;
    margin-bottom: 0.3rem;
}
.feedback-fix {
    font-weight: 600;
    color: #101C35;
    font-size: 0.95rem;
}

/* Fairness Note */
.fairness-banner {
    background-color: #EDF3FA;
    border: 1px solid #D0E1F9;
    border-radius: 8px;
    padding: 0.85rem 1.2rem;
    margin-top: 1rem;
    font-size: 0.88rem;
    color: #2457A6;
    font-weight: 500;
}
</style>
"""
