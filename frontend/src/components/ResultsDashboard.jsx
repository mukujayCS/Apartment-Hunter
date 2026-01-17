import React from 'react'
import './ResultsDashboard.css'

function ResultsDashboard({ results, onReset }) {
  const { text_analysis, image_analysis, student_reviews, questions, overall_assessment } = results

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'low': return 'success'
      case 'medium': return 'warning'
      case 'high': return 'danger'
      default: return 'warning'
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'low': return 'info'
      case 'medium': return 'warning'
      case 'high': return 'danger'
      default: return 'warning'
    }
  }

  // Helper function to sort by severity/priority/importance (high → medium → low)
  const sortBySeverity = (items) => {
    if (!items || items.length === 0) return []

    // Separate items by priority level
    const high = []
    const medium = []
    const low = []

    items.forEach(item => {
      const priority = (item.severity || item.priority || item.importance || 'medium').toLowerCase()
      if (priority === 'high') {
        high.push(item)
      } else if (priority === 'low') {
        low.push(item)
      } else {
        medium.push(item)
      }
    })

    // Concatenate: high first, then medium, then low
    return [...high, ...medium, ...low]
  }

  // Helper function to sort by recency (most recent → recent → older)
  const sortByRecency = (comments) => {
    return [...comments].sort((a, b) => {
      const weightA = a.recency_weight || 1.0
      const weightB = b.recency_weight || 1.0
      return weightB - weightA  // Descending order (highest weight first)
    })
  }

  return (
    <div className="results-dashboard">
      {/* Overall Assessment Banner */}
      <div className={`overall-banner card risk-${getRiskColor(overall_assessment.risk_level)}`}>
        <div className="banner-content">
          <div className="banner-icon">
            {overall_assessment.risk_level === 'low' && '✅'}
            {overall_assessment.risk_level === 'medium' && '⚠️'}
            {overall_assessment.risk_level === 'high' && '🚨'}
          </div>
          <div className="banner-text">
            <h2 className="banner-title">
              Overall Risk: {overall_assessment.risk_level.toUpperCase()}
            </h2>
            <p className="banner-recommendation">
              {overall_assessment.recommendation}
            </p>
            <p className="banner-summary">
              {overall_assessment.summary}
            </p>
          </div>
        </div>

        <div className="banner-stats">
          <div className="stat">
            <span className="stat-value">{overall_assessment.red_flag_count}</span>
            <span className="stat-label">Red Flags</span>
          </div>
          <div className="stat">
            <span className="stat-value">{overall_assessment.photo_issue_count}</span>
            <span className="stat-label">Photo Issues</span>
          </div>
          <div className="stat">
            <span className="stat-value">{overall_assessment.student_score.toFixed(1)}/5.0</span>
            <span className="stat-label">Student Score</span>
          </div>
        </div>
      </div>

      {/* Main Results Grid */}
      <div className="results-grid">
        {/* Text Analysis */}
        <div className="result-card card">
          <h3 className="section-title">
            <span className="section-icon">📝</span>
            Listing Description Analysis
          </h3>

          {text_analysis.red_flags && text_analysis.red_flags.length > 0 ? (
            <div className="subsection">
              <h4 className="subsection-title">🚩 Red Flags Found</h4>
              <div className="flags-list">
                {sortBySeverity(text_analysis.red_flags).map((flag, index) => (
                  <div key={index} className={`flag-item severity-${getSeverityColor(flag.severity)}`}>
                    <div className="flag-header">
                      <span className="flag-text">{flag.flag}</span>
                      <span className={`severity-badge badge-${getSeverityColor(flag.severity)}`}>
                        {flag.severity}
                      </span>
                    </div>
                    <p className="flag-reason">{flag.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="no-issues">No major red flags detected in the listing text!</p>
          )}

          {text_analysis.missing_info && text_analysis.missing_info.length > 0 && (
            <div className="subsection">
              <h4 className="subsection-title">❓ Missing Information</h4>
              <div className="missing-list">
                {sortBySeverity(text_analysis.missing_info).map((info, index) => (
                  <div key={index} className="missing-item">
                    <span className="missing-icon">•</span>
                    <div>
                      <strong>{info.item}</strong>
                      <p className="missing-why">{info.why}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {text_analysis.summary && (
            <div className="summary-box">
              <strong>Summary:</strong> {text_analysis.summary}
            </div>
          )}
        </div>

        {/* Image Analysis */}
        <div className="result-card card">
          <h3 className="section-title">
            <span className="section-icon">📷</span>
            Photo Quality Analysis
          </h3>

          <div className="quality-score">
            <div className="score-circle">
              <span className="score-value">{image_analysis.quality_score}/10</span>
            </div>
            <span className="score-label">Quality Score</span>
          </div>

          {image_analysis.photo_issues && image_analysis.photo_issues.length > 0 && (
            <div className="subsection">
              <h4 className="subsection-title">⚠️ Photo Issues</h4>
              <div className="issues-list">
                {sortBySeverity(image_analysis.photo_issues).map((issue, index) => (
                  <div key={index} className={`issue-item severity-${getSeverityColor(issue.severity)}`}>
                    <div className="issue-header">
                      <span className="issue-text">{issue.issue}</span>
                      {issue.photo_number > 0 && (
                        <span className="photo-badge">Photo #{issue.photo_number}</span>
                      )}
                    </div>
                    <p className="issue-explanation">{issue.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {image_analysis.positive_observations && image_analysis.positive_observations.length > 0 && (
            <div className="subsection">
              <h4 className="subsection-title">✨ Positive Observations</h4>
              <div className="positive-list">
                {image_analysis.positive_observations.map((obs, index) => (
                  <div key={index} className="positive-item">
                    <span className="positive-icon">✓</span>
                    <span>{obs.observation}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Student Reviews */}
        <div className="result-card card full-width">
          <h3 className="section-title">
            <span className="section-icon">💬</span>
            Student Insights from r/{student_reviews.subreddit}
          </h3>

          <div className="student-stats">
            <div className="sentiment-breakdown">
              <div className="sentiment-bar">
                <div
                  className="sentiment-positive"
                  style={{ width: `${(student_reviews.sentiment_breakdown.positive / student_reviews.total_mentions) * 100}%` }}
                />
                <div
                  className="sentiment-neutral"
                  style={{ width: `${(student_reviews.sentiment_breakdown.neutral / student_reviews.total_mentions) * 100}%` }}
                />
                <div
                  className="sentiment-negative"
                  style={{ width: `${(student_reviews.sentiment_breakdown.negative / student_reviews.total_mentions) * 100}%` }}
                />
              </div>
              <div className="sentiment-labels">
                <span className="label-positive">
                  {student_reviews.sentiment_breakdown.positive} Positive
                </span>
                <span className="label-neutral">
                  {student_reviews.sentiment_breakdown.neutral} Neutral
                </span>
                <span className="label-negative">
                  {student_reviews.sentiment_breakdown.negative} Negative
                </span>
              </div>
            </div>
          </div>

          <div className="comments-container">
            {sortByRecency(student_reviews.comments).map((comment, index) => (
              <div key={index} className={`comment sentiment-${comment.sentiment}`}>
                <div className="comment-header">
                  <span className="comment-category">{comment.category}</span>
                  <span className="comment-meta">
                    {comment.user_type} • {comment.time_posted} • ⬆️ {comment.score}
                  </span>
                </div>
                <p className="comment-text">{comment.text}</p>
                <div className="comment-footer">
                  <span className={`sentiment-tag tag-${comment.sentiment}`}>
                    {comment.sentiment}
                  </span>
                  {comment.recency_weight && comment.recency_weight >= 1.5 && (
                    <span className="recency-badge">Most Recent</span>
                  )}
                  {comment.recency_weight && comment.recency_weight >= 1.2 && comment.recency_weight < 1.5 && (
                    <span className="recency-badge">Recent</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="data-note">
            <span className="note-icon">ℹ️</span>
            {student_reviews.note}
          </div>
        </div>

        {/* Questions to Ask */}
        <div className="result-card card full-width">
          <h3 className="section-title">
            <span className="section-icon">❓</span>
            Important Questions to Ask the Landlord
          </h3>
          <p className="section-description">
            Based on the red flags and missing info, here are key questions you should ask:
          </p>

          <div className="questions-list">
            {sortBySeverity(questions).slice(0, 10).map((q, index) => (
              <div key={index} className={`question-item priority-${q.priority}`}>
                <div className="question-number">{index + 1}</div>
                <div className="question-content">
                  <p className="question-text">{q.question}</p>
                  <div className="question-meta">
                    <span className={`priority-badge badge-${getSeverityColor(q.priority)}`}>
                      {q.priority} priority
                    </span>
                    <span className="question-category">{q.category.replace('_', ' ')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button className="btn btn-primary btn-large" onClick={onReset}>
          <span>🔍</span>
          Analyze Another Listing
        </button>
      </div>
    </div>
  )
}

export default ResultsDashboard
