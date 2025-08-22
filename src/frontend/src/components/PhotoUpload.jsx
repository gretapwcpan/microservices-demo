import React, { useState, useRef } from 'react';
import './PhotoUpload.css';

const PhotoUpload = ({ onPhotoSelect, currentPhoto }) => {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = async (file) => {
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      alert('Image must be smaller than 5MB');
      return;
    }

    setUploading(true);
    
    try {
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target.result.split(',')[1]; // Remove data:image/...;base64, prefix
        onPhotoSelect({
          file,
          base64,
          preview: e.target.result
        });
        setUploading(false);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error reading file:', error);
      setUploading(false);
      alert('Error reading file. Please try again.');
    }
  };

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="photo-upload-container">
      <div 
        className={`photo-upload-area ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />
        
        {uploading ? (
          <div className="upload-spinner">
            <div className="spinner"></div>
            <p>Processing image...</p>
          </div>
        ) : currentPhoto ? (
          <div className="photo-preview">
            <img src={currentPhoto.preview} alt="Your outfit" />
            <div className="photo-overlay">
              <button className="change-photo-btn" onClick={(e) => { e.stopPropagation(); handleClick(); }}>
                📷 Change Photo
              </button>
            </div>
          </div>
        ) : (
          <div className="upload-placeholder">
            <div className="upload-icon">📷</div>
            <h3>Upload Product Photo</h3>
            <p>Upload a photo of an item you want to find across different stores</p>
            <button className="upload-btn">Choose Photo</button>
            <div className="upload-hints">
              <small>Supports JPG, PNG • Max 5MB</small>
            </div>
          </div>
        )}
      </div>
      
      {currentPhoto && (
        <div className="photo-info">
          <span className="photo-name">📎 {currentPhoto.file.name}</span>
          <span className="photo-size">{(currentPhoto.file.size / 1024 / 1024).toFixed(1)}MB</span>
        </div>
      )}
    </div>
  );
};

export default PhotoUpload;