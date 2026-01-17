import React, { useState } from 'react'
import InputForm from './components/InputForm'
import ResultsDashboard from './components/ResultsDashboard'
import './App.css'

function App() {
  const [analysisResults, setAnalysisResults] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = async (formData) => {
    setIsLoading(true)
    setError(null)
    setAnalysisResults(null)

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`)
      }

      const data = await response.json()
      setAnalysisResults(data)
    } catch (err) {
      setError(err.message)
      console.error('Analysis error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setAnalysisResults(null)
    setError(null)
  }

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <header className="app-header">
          <h1 className="app-title">
            <span className="icon">🏠</span>
            Apartment Hunter
          </h1>
          <p className="app-subtitle">
            AI-powered listing analysis to help students make informed apartment choices
          </p>
        </header>

        {/* Main Content */}
        {!analysisResults ? (
          <div className="fade-in">
            <InputForm
              onAnalyze={handleAnalyze}
              isLoading={isLoading}
              error={error}
            />
          </div>
        ) : (
          <div className="fade-in">
            <ResultsDashboard
              results={analysisResults}
              onReset={handleReset}
            />
          </div>
        )}

        {/* Footer */}
        <footer className="app-footer">
          <p>
            Built with <span style={{color: 'red'}}>♥</span> using Google Gemini AI & Mock Reddit Data
          </p>
          <p className="footer-note">
            Demo project • Reddit API requires pre-approval (Nov 2025) • Using realistic mock data
          </p>
        </footer>
      </div>
    </div>
  )
}

export default App
