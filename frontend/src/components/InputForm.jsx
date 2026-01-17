import React, { useState } from 'react'
import './InputForm.css'

const UNIVERSITIES = [
  'UIUC', 'Berkeley', 'UMich', 'Stanford', 'MIT', 'Harvard',
  'Cornell', 'Columbia', 'UCLA', 'USC', 'Northwestern', 'Yale',
  'Princeton', 'Penn', 'Duke', 'Johns Hopkins', 'Other'
]

function InputForm({ onAnalyze, isLoading, error }) {
  const [formData, setFormData] = useState({
    listingText: '',
    address: '',
    university: 'UIUC'
  })
  const [images, setImages] = useState([])
  const [isDragging, setIsDragging] = useState(false)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }

  const handleFileInput = (e) => {
    const files = Array.from(e.target.files)
    handleFiles(files)
  }

  const handleFiles = (files) => {
    const imageFiles = files.filter(file => file.type.startsWith('image/'))
    const remainingSlots = 5 - images.length

    if (imageFiles.length > remainingSlots) {
      alert(`You can only upload ${remainingSlots} more image(s). Maximum 5 total.`)
      return
    }

    setImages(prev => [...prev, ...imageFiles.slice(0, remainingSlots)])
  }

  const removeImage = (index) => {
    setImages(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!formData.listingText.trim()) {
      alert('Please enter the apartment listing description')
      return
    }

    // Create FormData object for file upload
    const submitData = new FormData()
    submitData.append('listing_text', formData.listingText)
    submitData.append('address', formData.address)
    submitData.append('university', formData.university)

    // Append images
    images.forEach((image) => {
      submitData.append('images', image)
    })

    onAnalyze(submitData)
  }

  return (
    <div className="input-form-container card">
      <h2 className="form-title">Analyze Your Apartment Listing</h2>
      <p className="form-description">
        Paste the listing description, upload photos, and let AI identify red flags
      </p>

      <form onSubmit={handleSubmit} className="input-form">
        {/* Listing Text */}
        <div className="form-group">
          <label htmlFor="listingText" className="form-label">
            Apartment Listing Description *
          </label>
          <textarea
            id="listingText"
            name="listingText"
            value={formData.listingText}
            onChange={handleInputChange}
            placeholder="Paste the apartment listing description here... (e.g., 'Cozy 2BR apartment near campus, recently updated...')"
            rows={8}
            className="form-textarea"
            required
          />
          <p className="form-hint">
            Copy and paste the full listing description from the rental website
          </p>
        </div>

        {/* Address */}
        <div className="form-group">
          <label htmlFor="address" className="form-label">
            Address (Optional)
          </label>
          <input
            type="text"
            id="address"
            name="address"
            value={formData.address}
            onChange={handleInputChange}
            placeholder="123 Main St, Champaign, IL"
            className="form-input"
          />
          <p className="form-hint">
            Helps match with student reviews from the area
          </p>
        </div>

        {/* University */}
        <div className="form-group">
          <label htmlFor="university" className="form-label">
            University *
          </label>
          <select
            id="university"
            name="university"
            value={formData.university}
            onChange={handleInputChange}
            className="form-select"
            required
          >
            {UNIVERSITIES.map(uni => (
              <option key={uni} value={uni}>{uni}</option>
            ))}
          </select>
          <p className="form-hint">
            Used to find relevant student reviews from your university's subreddit
          </p>
        </div>

        {/* Image Upload */}
        <div className="form-group">
          <label className="form-label">
            Listing Photos (Optional, max 5)
          </label>

          <div
            className={`image-dropzone ${isDragging ? 'dragging' : ''}`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => document.getElementById('fileInput').click()}
          >
            <div className="dropzone-content">
              <span className="dropzone-icon">📷</span>
              <p className="dropzone-text">
                Drag & drop images here, or click to select
              </p>
              <p className="dropzone-hint">
                PNG, JPG, JPEG up to 10MB each • {images.length}/5 uploaded
              </p>
            </div>
            <input
              id="fileInput"
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileInput}
              style={{ display: 'none' }}
            />
          </div>

          {/* Image Previews */}
          {images.length > 0 && (
            <div className="image-previews">
              {images.map((image, index) => (
                <div key={index} className="image-preview">
                  <img
                    src={URL.createObjectURL(image)}
                    alt={`Preview ${index + 1}`}
                  />
                  <button
                    type="button"
                    className="remove-image"
                    onClick={(e) => {
                      e.stopPropagation()
                      removeImage(index)
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          className="btn btn-primary btn-large submit-btn"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <div className="spinner" />
              Analyzing...
            </>
          ) : (
            <>
              <span>🔍</span>
              Analyze Listing
            </>
          )}
        </button>
      </form>
    </div>
  )
}

export default InputForm
