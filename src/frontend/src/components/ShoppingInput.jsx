import React, { useState } from 'react';
import './ShoppingInput.css';

const ShoppingInput = ({ onSearchRequest, isLoading }) => {
  const [searchType, setSearchType] = useState('photo'); // 'photo', 'prompt', 'both'
  const [promptText, setPromptText] = useState('');
  const [selectedStores, setSelectedStores] = useState([]);
  const [draggedUrls, setDraggedUrls] = useState([]);

  const popularStores = [
    { name: 'Amazon', url: 'amazon.com', icon: '📦' },
    { name: 'Target', url: 'target.com', icon: '🎯' },
    { name: 'Walmart', url: 'walmart.com', icon: '🛒' },
    { name: 'Best Buy', url: 'bestbuy.com', icon: '🔌' },
    { name: 'Nordstrom', url: 'nordstrom.com', icon: '👗' },
    { name: 'Home Depot', url: 'homedepot.com', icon: '🔨' },
    { name: 'Wayfair', url: 'wayfair.com', icon: '🏠' },
    { name: 'Etsy', url: 'etsy.com', icon: '🎨' }
  ];

  const handleStoreToggle = (store) => {
    setSelectedStores(prev => 
      prev.find(s => s.url === store.url)
        ? prev.filter(s => s.url !== store.url)
        : [...prev, store]
    );
  };

  const handleUrlDrop = (e) => {
    e.preventDefault();
    const url = e.dataTransfer.getData('text/plain');
    
    if (url && url.startsWith('http')) {
      const domain = new URL(url).hostname.replace('www.', '');
      const newStore = {
        name: domain.charAt(0).toUpperCase() + domain.slice(1),
        url: domain,
        icon: '🌐',
        custom: true
      };
      
      if (!draggedUrls.find(s => s.url === domain)) {
        setDraggedUrls(prev => [...prev, newStore]);
      }
    }
  };

  const handleSearch = () => {
    const allSelectedStores = [...selectedStores, ...draggedUrls];
    
    if (searchType === 'prompt' && !promptText.trim()) {
      alert('Please enter what you\'re looking for');
      return;
    }
    
    if (allSelectedStores.length === 0) {
      // Let AI recommend stores
    }

    onSearchRequest({
      type: searchType,
      prompt: promptText,
      stores: allSelectedStores
    });
  };

  const removeCustomStore = (storeToRemove) => {
    setDraggedUrls(prev => prev.filter(s => s.url !== storeToRemove.url));
  };

  return (
    <div className="shopping-input-container">
      <div className="search-type-selector">
        <h5>What are you looking for?</h5>
        <div className="search-type-buttons">
          <button 
            className={`search-type-btn ${searchType === 'photo' ? 'active' : ''}`}
            onClick={() => setSearchType('photo')}
          >
            📷 I have a photo
          </button>
          <button 
            className={`search-type-btn ${searchType === 'prompt' ? 'active' : ''}`}
            onClick={() => setSearchType('prompt')}
          >
            💭 I need ideas
          </button>
          <button 
            className={`search-type-btn ${searchType === 'both' ? 'active' : ''}`}
            onClick={() => setSearchType('both')}
          >
            🔍 Both
          </button>
        </div>
      </div>

      {(searchType === 'prompt' || searchType === 'both') && (
        <div className="prompt-section">
          <label htmlFor="shopping-prompt">Describe what you need:</label>
          <textarea
            id="shopping-prompt"
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder="I need a gift for my mom who loves gardening... or I want to redecorate my living room... or I'm looking for workout clothes..."
            rows={3}
            className="prompt-input"
          />
        </div>
      )}

      <div className="stores-section">
        <h6>Where do you want to shop?</h6>
        <p className="stores-hint">Select stores or drag website URLs here</p>
        
        <div className="popular-stores">
          <h7>Popular Stores:</h7>
          <div className="stores-grid">
            {popularStores.map(store => (
              <button
                key={store.url}
                className={`store-btn ${selectedStores.find(s => s.url === store.url) ? 'selected' : ''}`}
                onClick={() => handleStoreToggle(store)}
              >
                <span className="store-icon">{store.icon}</span>
                <span className="store-name">{store.name}</span>
              </button>
            ))}
          </div>
        </div>

        <div 
          className="url-drop-zone"
          onDrop={handleUrlDrop}
          onDragOver={(e) => e.preventDefault()}
        >
          <div className="drop-zone-content">
            <span className="drop-icon">🔗</span>
            <p>Drag website URLs here to add custom stores</p>
          </div>
          
          {draggedUrls.length > 0 && (
            <div className="custom-stores">
              {draggedUrls.map(store => (
                <div key={store.url} className="custom-store-item">
                  <span className="store-icon">{store.icon}</span>
                  <span className="store-name">{store.name}</span>
                  <button 
                    className="remove-store-btn"
                    onClick={() => removeCustomStore(store)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="search-action">
        <button 
          className="search-btn"
          onClick={handleSearch}
          disabled={isLoading}
        >
          {isLoading ? '🔍 Searching...' : '🛍️ Find Products'}
        </button>
        
        {(selectedStores.length > 0 || draggedUrls.length > 0) && (
          <p className="selected-count">
            Searching across {selectedStores.length + draggedUrls.length} store{selectedStores.length + draggedUrls.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>
    </div>
  );
};

export default ShoppingInput;