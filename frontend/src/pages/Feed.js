import React from 'react';
import styled from 'styled-components';
import Masonry from 'react-masonry-css';
import { useData } from '../context/DataContext';
import PinCard from '../components/PinCard';
import LoadingSpinner from '../components/LoadingSpinner';

const FeedContainer = styled.div`
  padding: 20px 0;
`;

const FeedHeader = styled.div`
  text-align: center;
  margin-bottom: 40px;
`;

const FeedTitle = styled.h1`
  font-size: 32px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.textPrimary};
  margin-bottom: 8px;
`;

const FeedSubtitle = styled.p`
  font-size: 16px;
  color: ${({ theme }) => theme.colors.textSecondary};
`;

const AlgorithmInfo = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 32px;
  text-align: center;
`;

const AlgorithmTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
`;

const AlgorithmDescription = styled.p`
  font-size: 14px;
  opacity: 0.9;
  line-height: 1.4;
`;

const Feed = () => {
  const { feed, loading } = useData();

  const breakpointColumnsObj = {
    default: 4,
    1100: 3,
    700: 2,
    500: 1
  };

  return (
    <FeedContainer>
      <FeedHeader>
        <FeedTitle>Your Smart Feed</FeedTitle>
        <FeedSubtitle>Personalized content powered by advanced algorithms</FeedSubtitle>
      </FeedHeader>

      <AlgorithmInfo>
        <AlgorithmTitle>🧠 Smart Feed Ranking Algorithm</AlgorithmTitle>
        <AlgorithmDescription>
          This feed is generated using O(n log k) k-way merge algorithm with personalized scoring based on:
          engagement metrics, recency, user affinity, and board preferences.
        </AlgorithmDescription>
      </AlgorithmInfo>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <Masonry
          breakpointCols={breakpointColumnsObj}
          className="my-masonry-grid"
          columnClassName="my-masonry-column"
        >
          {feed.map((pin) => (
            <PinCard key={pin.id} pin={pin} />
          ))}
        </Masonry>
      )}

      {!loading && feed.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h3>No feed items yet</h3>
          <p>Start following users and saving pins to see your personalized feed!</p>
        </div>
      )}
    </FeedContainer>
  );
};

export default Feed;
