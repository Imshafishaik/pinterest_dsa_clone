import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import Masonry from 'react-masonry-css';
import { useData } from '../context/DataContext';
import PinCard from '../components/PinCard';
import LoadingSpinner from '../components/LoadingSpinner';

const SearchContainer = styled.div`
  padding: 20px 0;
`;

const SearchHeader = styled.div`
  margin-bottom: 32px;
`;

const SearchTitle = styled.h1`
  font-size: 32px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.textPrimary};
  margin-bottom: 8px;
`;

const SearchSubtitle = styled.p`
  font-size: 16px;
  color: ${({ theme }) => theme.colors.textSecondary};
`;

const AutocompleteContainer = styled.div`
  background: white;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
`;

const AutocompleteTitle = styled.h3`
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: ${({ theme }) => theme.colors.textPrimary};
`;

const AutocompleteList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
`;

const AutocompleteItem = styled.button`
  padding: 8px 16px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: 20px;
  background: white;
  color: ${({ theme }) => theme.colors.textPrimary};
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.backgroundSecondary};
    border-color: ${({ theme }) => theme.colors.textPrimary};
  }
`;

const AlgorithmInfo = styled.div`
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 32px;
  text-align: center;
`;

const Search = () => {
  const { searchResults, searchPins, loading } = useData();
  const [searchQuery, setSearchQuery] = useState('');
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState([]);

  const popularSearches = [
    'DIY crafts', 'Home decor', 'Recipes', 'Fashion trends', 
    'Travel photography', 'Fitness tips', 'Art projects', 'Garden ideas'
  ];

  useEffect(() => {
    // Mock autocomplete suggestions
    setAutocompleteSuggestions(popularSearches);
  }, []);

  const handleSearch = (query) => {
    setSearchQuery(query);
    if (query.trim()) {
      searchPins(query);
    }
  };

  const handleAutocompleteClick = (suggestion) => {
    handleSearch(suggestion);
  };

  const breakpointColumnsObj = {
    default: 4,
    1100: 3,
    700: 2,
    500: 1
  };

  return (
    <SearchContainer>
      <SearchHeader>
        <SearchTitle>Search</SearchTitle>
        <SearchSubtitle>Discover ideas with smart search autocomplete</SearchSubtitle>
      </SearchHeader>

      <AlgorithmInfo>
        <h3>🔍 Search Autocomplete Algorithm</h3>
        <p>
          Powered by Trie data structure with O(m) prefix traversal and frequency-based ranking.
          Provides instant suggestions as you type with personalized recommendations.
        </p>
      </AlgorithmInfo>

      <AutocompleteContainer>
        <AutocompleteTitle>Popular searches</AutocompleteTitle>
        <AutocompleteList>
          {autocompleteSuggestions.map((suggestion, index) => (
            <AutocompleteItem
              key={index}
              onClick={() => handleAutocompleteClick(suggestion)}
            >
              {suggestion}
            </AutocompleteItem>
          ))}
        </AutocompleteList>
      </AutocompleteContainer>

      {searchQuery && (
        <div style={{ marginBottom: '24px' }}>
          <h3>Results for "{searchQuery}"</h3>
          <p>Found {searchResults.length} results</p>
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {searchResults.length > 0 ? (
            <Masonry
              breakpointCols={breakpointColumnsObj}
              className="my-masonry-grid"
              columnClassName="my-masonry-column"
            >
              {searchResults.map((pin) => (
                <PinCard key={pin.id} pin={pin} />
              ))}
            </Masonry>
          ) : searchQuery ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <h3>No results found</h3>
              <p>Try searching for something else</p>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <h3>Start searching</h3>
              <p>Type in the search bar above to find pins</p>
            </div>
          )}
        </>
      )}
    </SearchContainer>
  );
};

export default Search;
