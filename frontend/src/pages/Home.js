import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import Masonry from 'react-masonry-css';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useData } from '../context/DataContext';
import PinCard from '../components/PinCard';
import LoadingSpinner from '../components/LoadingSpinner';

const HomeContainer = styled.div`
  padding: 20px 0;
`;

const Section = styled.section`
  margin-bottom: 40px;
`;

const SectionTitle = styled.h2`
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 24px;
  color: ${({ theme }) => theme.colors.textPrimary};
`;

const Subtitle = styled.p`
  font-size: 18px;
  color: ${({ theme }) => theme.colors.textSecondary};
  margin-bottom: 32px;
`;

const Home = () => {
  const { pins, trending, recommendations, loading, error } = useData();
  const [displayedPins, setDisplayedPins] = useState([]);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    // Initialize with recommendations first, then trending
    const initialPins = [...recommendations, ...trending];
    setDisplayedPins(initialPins);
  }, [recommendations, trending]);

  const loadMorePins = () => {
    // Simulate loading more pins
    if (displayedPins.length < pins.length) {
      setTimeout(() => {
        const newPins = pins.slice(displayedPins.length, displayedPins.length + 6);
        setDisplayedPins(prev => [...prev, ...newPins]);
      }, 1000);
    } else {
      setHasMore(false);
    }
  };

  const breakpointColumnsObj = {
    default: 4,
    1100: 3,
    700: 2,
    500: 1
  };

  if (error) {
    return (
      <HomeContainer>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h2>Something went wrong</h2>
          <p>{error}</p>
        </div>
      </HomeContainer>
    );
  }

  return (
    <HomeContainer>
      {/* Recommendations Section */}
      {recommendations.length > 0 && (
        <Section>
          <SectionTitle>Recommended for you</SectionTitle>
          <Subtitle>Pins you might love based on your interests</Subtitle>
          <Masonry
            breakpointCols={breakpointColumnsObj}
            className="my-masonry-grid"
            columnClassName="my-masonry-column"
          >
            <div className="recommendations-container">
            {recommendations.map((pin) => (
              <PinCard key={pin.id} pin={pin} />
            ))}
            </div>
          </Masonry>
        </Section>
      )}

      {/* Trending Section */}
      {trending.length > 0 && (
        <Section>
          <SectionTitle>Trending now</SectionTitle>
          <Subtitle>Popular pins from the Pinterest community</Subtitle>
          <Masonry
            breakpointCols={breakpointColumnsObj}
            className="my-masonry-grid"
            columnClassName="my-masonry-column"
          >
            {trending.map((pin) => (
              <PinCard key={pin.id} pin={pin} />
            ))}
          </Masonry>
        </Section>
      )}

      {/* All Pins with Infinite Scroll */}
      <Section>
        <SectionTitle>Explore</SectionTitle>
        <Subtitle>Discover ideas from around the world</Subtitle>
        
        <InfiniteScroll
          dataLength={displayedPins.length}
          next={loadMorePins}
          hasMore={hasMore}
          loader={<LoadingSpinner />}
          endMessage={
            <p style={{ textAlign: 'center', marginTop: '20px' }}>
              <b>Yay! You've seen it all</b>
            </p>
          }
        >
          <Masonry
            breakpointCols={breakpointColumnsObj}
            className="my-masonry-grid"
            columnClassName="my-masonry-column"
          >
            {displayedPins.map((pin) => (
              <PinCard key={pin.id} pin={pin} />
            ))}
          </Masonry>
        </InfiniteScroll>
      </Section>
    </HomeContainer>
  );
};

export default Home;
