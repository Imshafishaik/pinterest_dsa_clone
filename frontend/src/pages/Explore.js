import React from 'react';
import styled from 'styled-components';
import Masonry from 'react-masonry-css';
import { useData } from '../context/DataContext';
import PinCard from '../components/PinCard';
import LoadingSpinner from '../components/LoadingSpinner';

const ExploreContainer = styled.div`
  padding: 20px 0;
`;

const ExploreHeader = styled.div`
  text-align: center;
  margin-bottom: 40px;
`;

const ExploreTitle = styled.h1`
  font-size: 32px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.textPrimary};
  margin-bottom: 8px;
`;

const ExploreSubtitle = styled.p`
  font-size: 16px;
  color: ${({ theme }) => theme.colors.textSecondary};
`;

const AlgorithmInfo = styled.div`
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
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

const Explore = () => {
  const { trending, loading } = useData();

  const breakpointColumnsObj = {
    default: 4,
    1100: 3,
    700: 2,
    500: 1
  };

  return (
    <ExploreContainer>
      <ExploreHeader>
        <ExploreTitle>Trending Now</ExploreTitle>
        <ExploreSubtitle>Discover what's popular on Pinterest</ExploreSubtitle>
      </ExploreHeader>

      {/* <AlgorithmInfo>
        <AlgorithmTitle>🔥 Trending Detection Algorithm</AlgorithmTitle>
        <AlgorithmDescription>
          This explore page is powered by a Priority Queue (Max-Heap) to maintain the top-K trending pins in real-time, factoring in interaction velocity within a sliding time window.
        </AlgorithmDescription>
      </AlgorithmInfo> */}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <Masonry
          breakpointCols={breakpointColumnsObj}
          className="my-masonry-grid"
          columnClassName="my-masonry-column"
        >
          {trending.map((pin) => (
            <PinCard key={pin.id} pin={pin} />
          ))}
        </Masonry>
      )}

      {!loading && trending.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h3>No trending pins yet</h3>
          <p>Interact with some pins to generate trending content!</p>
        </div>
      )}
    </ExploreContainer>
  );
};

export default Explore;
