import React from 'react';
import { createRoot } from 'react-dom/client';
import PhotoUpload from './PhotoUpload.jsx';
import VoiceInput from './VoiceInput.jsx';
import AnalysisResults from './AnalysisResults.jsx';

// Main QuanBuy App Component
const QuanBuyApp = () => {
  const [photo, setPhoto] = React.useState(null);
  const [questionText, setQuestionText] = React.useState('');
  const [occasion, setOccasion] = React.useState('');
  const [budget, setBudget] = React.useState('');
  const [analysisResults, setAnalysisResults] = React.useState(null);
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);

  const handlePhotoSelect = (photoData) => {
    setPhoto(photoData);
  };

  const handleVoiceInput = (transcript) => {
    console.log('Voice input received:', transcript);
  };

  const handleTextChange = (text) => {
    setQuestionText(text);
  };

  const handleAnalyze = async () => {
    if (!photo || !questionText.trim()) {
      alert('Please upload a photo and ask a question');
      return;
    }

    setIsAnalyzing(true);
    
    try {
      const response = await fetch('/api/analyze-style', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: photo.base64,
          user_question: questionText,
          occasion: occasion,
          budget_range: budget,
          user_id: 'web-user'
        })
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const results = await response.json();
      setAnalysisResults(results);
    } catch (error) {
      console.error('Analysis error:', error);
      setAnalysisResults({ error: error.message });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRetry = () => {
    setAnalysisResults(null);
    setPhoto(null);
    setQuestionText('');
    setOccasion('');
    setBudget('');
  };

  return (
    <div className="quanbuy-app">
      <div className="app-section">
        <PhotoUpload 
          onPhotoSelect={handlePhotoSelect}
          currentPhoto={photo}
        />
      </div>

      <div className="app-section">
        <VoiceInput 
          onVoiceInput={handleVoiceInput}
          onTextChange={handleTextChange}
          currentText={questionText}
        />
      </div>

      <div className="app-section">
        <div className="question-form">
          <h5>💬 Ask Your quanBuy</h5>
          <textarea
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            placeholder="How do I look? What would you suggest? Is this appropriate for..."
            rows={3}
            className="question-input"
          />
          
          <div className="form-row">
            <div className="form-group">
              <label>Occasion:</label>
              <select value={occasion} onChange={(e) => setOccasion(e.target.value)}>
                <option value="">Select occasion</option>
                <option value="work">Work</option>
                <option value="casual">Casual</option>
                <option value="formal">Formal</option>
                <option value="date">Date</option>
                <option value="party">Party</option>
                <option value="travel">Travel</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Budget:</label>
              <select value={budget} onChange={(e) => setBudget(e.target.value)}>
                <option value="">Any budget</option>
                <option value="under-50">Under $50</option>
                <option value="50-100">$50 - $100</option>
                <option value="100-200">$100 - $200</option>
                <option value="200+">$200+</option>
              </select>
            </div>
          </div>

          <button 
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={!photo || !questionText.trim() || isAnalyzing}
          >
            {isAnalyzing ? '🎨 Analyzing...' : '🎨 Get Style Advice'}
          </button>
        </div>
      </div>

      <div className="app-section">
        <AnalysisResults 
          results={analysisResults}
          isLoading={isAnalyzing}
          onRetry={handleRetry}
        />
      </div>
    </div>
  );
};

// Mount React components to DOM elements
window.QuanBuyComponents = {
  // Mount the full app
  mountApp: (elementId) => {
    const container = document.getElementById(elementId);
    if (container) {
      const root = createRoot(container);
      root.render(<QuanBuyApp />);
    }
  },

  // Mount individual components
  mountPhotoUpload: (elementId, props = {}) => {
    const container = document.getElementById(elementId);
    if (container) {
      const root = createRoot(container);
      root.render(<PhotoUpload {...props} />);
    }
  },

  mountVoiceInput: (elementId, props = {}) => {
    const container = document.getElementById(elementId);
    if (container) {
      const root = createRoot(container);
      root.render(<VoiceInput {...props} />);
    }
  },

  mountAnalysisResults: (elementId, props = {}) => {
    const container = document.getElementById(elementId);
    if (container) {
      const root = createRoot(container);
      root.render(<AnalysisResults {...props} />);
    }
  }
};

// Auto-mount if elements exist
document.addEventListener('DOMContentLoaded', () => {
  // Try to mount the full app first
  if (document.getElementById('quanbuy-app')) {
    window.QuanBuyComponents.mountApp('quanbuy-app');
  }
  
  // Fallback to individual components
  if (document.getElementById('photo-upload-react')) {
    window.QuanBuyComponents.mountPhotoUpload('photo-upload-react');
  }
  
  if (document.getElementById('voice-input-react')) {
    window.QuanBuyComponents.mountVoiceInput('voice-input-react');
  }
  
  if (document.getElementById('analysis-results-react')) {
    window.QuanBuyComponents.mountAnalysisResults('analysis-results-react');
  }
});