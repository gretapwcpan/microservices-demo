import React, { useState } from 'react';
import './AnalysisResults.css';

const AnalysisResults = ({ results, isLoading, onRetry }) => {
  const [activeTab, setActiveTab] = useState('analysis');

  if (isLoading) {
    return (
      <div className="analysis-results loading">
        <div className="loading-header">
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
          <h3>🎨 AI quanBuy is Analyzing...</h3>
          <p>Getting expert fashion advice just for you</p>
        </div>
        <div className="loading-steps">
          <div className="step active">📸 Analyzing your photo</div>
          <div className="step">🎨 Generating style recommendations</div>
          <div className="step">🛍️ Finding perfect products</div>
          <div className="step">💡 Creating personalized advice</div>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="analysis-results empty">
        <div className="empty-state">
          <span className="empty-icon">📷</span>
          <h3>Ready for Your Style Analysis</h3>
          <p>Upload a photo and ask a question to get personalized fashion advice from your AI quanBuy</p>
        </div>
      </div>
    );
  }

  if (results.error) {
    return (
      <div className="analysis-results error">
        <div className="error-state">
          <span className="error-icon">❌</span>
          <h3>Oops! Something went wrong</h3>
          <p>{results.error}</p>
          <button className="retry-button" onClick={onRetry}>
            🔄 Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="analysis-results">
      <div className="results-header">
        <h3>🎨 Your Personal Style Analysis</h3>
        <div className="confidence-score">
          <span className="score-label">Confidence:</span>
          <div className="score-bar">
            <div 
              className="score-fill" 
              style={{ width: `${(results.confidence_score || 0.9) * 100}%` }}
            ></div>
          </div>
          <span className="score-value">{Math.round((results.confidence_score || 0.9) * 100)}%</span>
        </div>
      </div>

      <div className="results-tabs">
        <button 
          className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          📝 Analysis
        </button>
        <button 
          className={`tab ${activeTab === 'recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('recommendations')}
        >
          🛍️ Products ({results.recommendations?.length || 0})
        </button>
        <button 
          className={`tab ${activeTab === 'tips' ? 'active' : ''}`}
          onClick={() => setActiveTab('tips')}
        >
          💡 Style Tips
        </button>
      </div>

      <div className="results-content">
        {activeTab === 'analysis' && (
          <div className="analysis-tab">
            <div className="analysis-text">
              {results.analysis?.split('\n').map((paragraph, index) => (
                <p key={index}>{paragraph}</p>
              ))}
            </div>
            {results.voice_response && (
              <div className="voice-response">
                <button className="play-voice-btn" onClick={() => speakText(results.voice_response)}>
                  🔊 Hear Analysis
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="recommendations-tab">
            {results.recommendations && results.recommendations.length > 0 ? (
              <div className="products-grid">
                {results.recommendations.map((product, index) => (
                  <div key={product.id || index} className="product-card">
                    <div className="product-header">
                      <h4>{product.name}</h4>
                      <span className="product-price">{product.price}</span>
                    </div>
                    <div className="product-reason">
                      <span className="reason-icon">✨</span>
                      <p>{product.reason}</p>
                    </div>
                    <button className="view-product-btn">
                      👀 View Product
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-products">
                <span className="no-products-icon">🛍️</span>
                <p>No specific product recommendations available</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'tips' && (
          <div className="tips-tab">
            {results.persuasion_points && results.persuasion_points.length > 0 ? (
              <div className="tips-list">
                {results.persuasion_points.map((tip, index) => (
                  <div key={index} className="tip-item">
                    <span className="tip-icon">💡</span>
                    <p>{tip}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="default-tips">
                <div className="tip-item">
                  <span className="tip-icon">💡</span>
                  <p>Confidence is your best accessory - wear your style with pride!</p>
                </div>
                <div className="tip-item">
                  <span className="tip-icon">✨</span>
                  <p>Small details like accessories can transform your entire look</p>
                </div>
                <div className="tip-item">
                  <span className="tip-icon">🎨</span>
                  <p>Color coordination creates visual harmony and sophistication</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="results-actions">
        <button className="secondary-btn" onClick={onRetry}>
          🔄 Analyze Again
        </button>
        <button className="primary-btn" onClick={() => shareResults(results)}>
          📤 Share Results
        </button>
      </div>
    </div>
  );
};

// Helper function to speak text using Web Speech API
const speakText = (text) => {
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    speechSynthesis.speak(utterance);
  }
};

// Helper function to share results
const shareResults = (results) => {
  if (navigator.share) {
    navigator.share({
      title: 'My AI Style Analysis',
      text: `Check out my personalized style analysis from AI quanBuy! Confidence score: ${Math.round((results.confidence_score || 0.9) * 100)}%`,
      url: window.location.href
    });
  } else {
    // Fallback for browsers without Web Share API
    const text = `My AI Style Analysis - Confidence: ${Math.round((results.confidence_score || 0.9) * 100)}%`;
    navigator.clipboard.writeText(text).then(() => {
      alert('Results copied to clipboard!');
    });
  }
};

export default AnalysisResults;