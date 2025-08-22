import React, { useState } from 'react';
import './ProductResults.css';

const ProductResults = ({ results, isLoading, onRetry }) => {
  const [sortBy, setSortBy] = useState('relevance'); // 'relevance', 'price_low', 'price_high', 'store'
  const [filterStore, setFilterStore] = useState('all');

  if (isLoading) {
    return (
      <div className="results-loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
        <h5>🔍 Searching across stores...</h5>
        <p>Finding the best matches and prices for you</p>
      </div>
    );
  }

  if (!results) {
    return null;
  }

  if (results.error) {
    return (
      <div className="results-error">
        <div className="error-icon">❌</div>
        <h5>Search Failed</h5>
        <p>{results.error}</p>
        <button className="retry-btn" onClick={onRetry}>
          🔄 Try Again
        </button>
      </div>
    );
  }

  const { products = [], search_query, total_found, stores_searched } = results;

  // Get unique stores for filter
  const availableStores = [...new Set(products.map(p => p.store))];

  // Sort and filter products
  const filteredProducts = products
    .filter(product => filterStore === 'all' || product.store === filterStore)
    .sort((a, b) => {
      switch (sortBy) {
        case 'price_low':
          return parseFloat(a.price.replace(/[^0-9.]/g, '')) - parseFloat(b.price.replace(/[^0-9.]/g, ''));
        case 'price_high':
          return parseFloat(b.price.replace(/[^0-9.]/g, '')) - parseFloat(a.price.replace(/[^0-9.]/g, ''));
        case 'store':
          return a.store.localeCompare(b.store);
        case 'relevance':
        default:
          return b.confidence - a.confidence;
      }
    });

  return (
    <div className="product-results">
      <div className="results-header">
        <div className="results-summary">
          <h4>🛍️ Search Results</h4>
          <p>Found {total_found} products across {stores_searched} stores</p>
          {search_query && <p className="search-query">Searched for: "{search_query}"</p>}
        </div>
        
        <div className="results-controls">
          <div className="sort-controls">
            <label htmlFor="sort-select">Sort by:</label>
            <select 
              id="sort-select"
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="relevance">Best Match</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
              <option value="store">Store Name</option>
            </select>
          </div>
          
          <div className="filter-controls">
            <label htmlFor="store-filter">Store:</label>
            <select 
              id="store-filter"
              value={filterStore} 
              onChange={(e) => setFilterStore(e.target.value)}
            >
              <option value="all">All Stores</option>
              {availableStores.map(store => (
                <option key={store} value={store}>{store}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="products-grid">
        {filteredProducts.map((product, index) => (
          <div key={`${product.store}-${index}`} className="product-card">
            <div className="product-image">
              {product.image_url ? (
                <img src={product.image_url} alt={product.name} />
              ) : (
                <div className="no-image">📦</div>
              )}
              <div className="confidence-badge">
                {Math.round(product.confidence * 100)}% match
              </div>
            </div>
            
            <div className="product-info">
              <div className="product-header">
                <h6 className="product-name">{product.name}</h6>
                <div className="store-badge">{product.store}</div>
              </div>
              
              <div className="product-price">
                <span className="current-price">{product.price}</span>
                {product.original_price && product.original_price !== product.price && (
                  <span className="original-price">{product.original_price}</span>
                )}
                {product.discount && (
                  <span className="discount-badge">{product.discount}</span>
                )}
              </div>
              
              {product.rating && (
                <div className="product-rating">
                  <span className="stars">{'⭐'.repeat(Math.floor(product.rating))}</span>
                  <span className="rating-text">{product.rating} ({product.review_count || 0} reviews)</span>
                </div>
              )}
              
              <div className="product-details">
                {product.availability && (
                  <span className={`availability ${product.availability.toLowerCase().includes('stock') ? 'in-stock' : 'out-stock'}`}>
                    {product.availability}
                  </span>
                )}
                {product.shipping && (
                  <span className="shipping">{product.shipping}</span>
                )}
              </div>
            </div>
            
            <div className="product-actions">
              <a 
                href={product.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="view-product-btn"
              >
                View on {product.store}
              </a>
              {product.buy_now_url && (
                <a 
                  href={product.buy_now_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="buy-now-btn"
                >
                  🛒 Buy Now
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {filteredProducts.length === 0 && (
        <div className="no-results">
          <div className="no-results-icon">🔍</div>
          <h5>No products found</h5>
          <p>Try adjusting your filters or search criteria</p>
          <button className="retry-btn" onClick={onRetry}>
            🔄 New Search
          </button>
        </div>
      )}
      
      <div className="results-footer">
        <button className="new-search-btn" onClick={onRetry}>
          🔍 Start New Search
        </button>
      </div>
    </div>
  );
};

export default ProductResults;