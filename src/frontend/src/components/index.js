import React from 'react';
import { createRoot } from 'react-dom/client';
import PhotoUpload from './PhotoUpload.jsx';
import ShoppingInput from './ShoppingInput.jsx';
import ProductResults from './ProductResults.jsx';

// Main QuanBuy App Component
const QuanBuyApp = () => {
  const [photo, setPhoto] = React.useState(null);
  const [searchResults, setSearchResults] = React.useState(null);
  const [isSearching, setIsSearching] = React.useState(false);
  const [showPhotoUpload, setShowPhotoUpload] = React.useState(true);

  const handlePhotoSelect = (photoData) => {
    setPhoto(photoData);
  };

  const handleSearchRequest = async (searchData) => {
    const { type, prompt, stores } = searchData;
    
    if (type !== 'prompt' && !photo) {
      alert('Please upload a photo for visual search');
      return;
    }

    setIsSearching(true);
    setSearchResults(null);
    
    try {
      const requestBody = {
        search_type: type,
        user_id: 'web-user',
        stores: stores.map(s => ({ name: s.name, url: s.url }))
      };

      if (photo && (type === 'photo' || type === 'both')) {
        requestBody.image_base64 = photo.base64;
      }

      if (prompt && (type === 'prompt' || type === 'both')) {
        requestBody.search_prompt = prompt;
      }

      const response = await fetch('/api/search-products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const results = await response.json();
      setSearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults({ error: error.message });
    } finally {
      setIsSearching(false);
    }
  };

  const handleRetry = () => {
    setSearchResults(null);
    setPhoto(null);
    setShowPhotoUpload(true);
  };

  return (
    <div className="quanbuy-app">
      {showPhotoUpload && (
        <div className="app-section">
          <PhotoUpload 
            onPhotoSelect={handlePhotoSelect}
            currentPhoto={photo}
          />
        </div>
      )}

      <div className="app-section">
        <ShoppingInput 
          onSearchRequest={handleSearchRequest}
          isLoading={isSearching}
        />
      </div>

      <div className="app-section">
        <ProductResults 
          results={searchResults}
          isLoading={isSearching}
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

  mountShoppingInput: (elementId, props = {}) => {
    const container = document.getElementById(elementId);
    if (container) {
      const root = createRoot(container);
      root.render(<ShoppingInput {...props} />);
    }
  },

  mountProductResults: (elementId, props = {}) => {
    const container = document.getElementById(elementId);
    if (container) {
      const root = createRoot(container);
      root.render(<ProductResults {...props} />);
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
  
  if (document.getElementById('shopping-input-react')) {
    window.QuanBuyComponents.mountShoppingInput('shopping-input-react');
  }
  
  if (document.getElementById('product-results-react')) {
    window.QuanBuyComponents.mountProductResults('product-results-react');
  }
});