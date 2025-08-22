import React, { useState, useEffect, useRef } from 'react';
import './VoiceInput.css';

const VoiceInput = ({ onVoiceInput, onTextChange, currentText = '' }) => {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
    // Check if browser supports speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      setIsSupported(true);
      
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognition.onstart = () => {
        setIsListening(true);
        setError('');
      };
      
      recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        const fullTranscript = finalTranscript || interimTranscript;
        setTranscript(fullTranscript);
        
        if (finalTranscript) {
          onVoiceInput(finalTranscript);
          onTextChange(currentText + ' ' + finalTranscript);
        }
      };
      
      recognition.onerror = (event) => {
        setError(`Speech recognition error: ${event.error}`);
        setIsListening(false);
      };
      
      recognition.onend = () => {
        setIsListening(false);
        setTranscript('');
      };
      
      recognitionRef.current = recognition;
    } else {
      setIsSupported(false);
      setError('Speech recognition not supported in this browser');
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [onVoiceInput, onTextChange, currentText]);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setError('');
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  if (!isSupported) {
    return (
      <div className="voice-input-container">
        <div className="voice-input-error">
          <span className="error-icon">⚠️</span>
          <p>Voice input not supported in this browser</p>
          <small>Try Chrome, Edge, or Safari for voice features</small>
        </div>
      </div>
    );
  }

  return (
    <div className="voice-input-container">
      <div className="voice-input-header">
        <h5>🎤 Voice Input</h5>
        <p>Ask your question out loud - perfect for trying on clothes!</p>
      </div>
      
      <div className="voice-controls">
        <button
          className={`voice-btn ${isListening ? 'listening' : ''}`}
          onClick={toggleListening}
          disabled={!!error}
        >
          {isListening ? (
            <>
              <span className="mic-icon recording">🎤</span>
              <span>Stop Recording</span>
            </>
          ) : (
            <>
              <span className="mic-icon">🎤</span>
              <span>Start Voice Input</span>
            </>
          )}
        </button>
        
        {isListening && (
          <div className="listening-indicator">
            <div className="sound-wave">
              <div className="wave wave1"></div>
              <div className="wave wave2"></div>
              <div className="wave wave3"></div>
            </div>
            <span>Listening...</span>
          </div>
        )}
      </div>
      
      {transcript && (
        <div className="voice-transcript">
          <div className="transcript-header">
            <span className="transcript-icon">💬</span>
            <span>You said:</span>
          </div>
          <div className="transcript-text">"{transcript}"</div>
        </div>
      )}
      
      {error && (
        <div className="voice-error">
          <span className="error-icon">❌</span>
          <span>{error}</span>
          <button className="retry-btn" onClick={startListening}>
            Try Again
          </button>
        </div>
      )}
      
      <div className="voice-tips">
        <h6>💡 Voice Tips:</h6>
        <ul>
          <li>"How do I look in this outfit?"</li>
          <li>"What accessories would go with this?"</li>
          <li>"Is this appropriate for work?"</li>
          <li>"Compare these two items"</li>
        </ul>
      </div>
    </div>
  );
};

export default VoiceInput;