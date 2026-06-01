import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useParams } from 'react-router-dom';
import { useData } from '../context/DataContext';
import LoadingSpinner from '../components/LoadingSpinner';
import axios from 'axios';

const PinDetailContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
`;

const PinImageContainer = styled.div`
  position: relative;
  width: 100%;
  margin-bottom: 24px;
`;

const PinImage = styled.img`
  width: 100%;
  border-radius: 16px;
  display: block;
`;

const VisualSearchButton = styled.button`
  position: absolute;
  bottom: 16px;
  right: 16px;
  background-color: rgba(255, 255, 255, 0.9);
  color: ${({ theme }) => theme.colors.textPrimary};
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: all 0.2s;
  
  &:hover {
    background-color: white;
    transform: scale(1.05);
  }
`;

const PinContent = styled.div`
  display: flex;
  gap: 24px;
  
  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const PinMain = styled.div`
  flex: 1;
`;

const PinTitle = styled.h1`
  font-size: 32px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.textPrimary};
  margin-bottom: 16px;
`;

const PinDescription = styled.p`
  font-size: 16px;
  line-height: 1.6;
  color: ${({ theme }) => theme.colors.textPrimary};
  margin-bottom: 24px;
`;

const PinMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
`;

const MetaItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: ${({ theme }) => theme.colors.textSecondary};
`;

const PinSidebar = styled.div`
  width: 300px;
  
  @media (max-width: 768px) {
    width: 100%;
  }
`;

const AuthorCard = styled.div`
  background: white;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
`;

const AuthorHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
`;

const AuthorAvatar = styled.img`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
`;

const AuthorInfo = styled.div`
  flex: 1;
`;

const AuthorName = styled.div`
  font-weight: 600;
  color: ${({ theme }) => theme.colors.textPrimary};
`;

const AuthorUsername = styled.div`
  font-size: 14px;
  color: ${({ theme }) => theme.colors.textSecondary};
`;

const FollowButton = styled.button`
  padding: 8px 16px;
  border-radius: 20px;
  border: none;
  background-color: ${({ theme }) => theme.colors.primary};
  color: white;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.primaryHover};
  }
`;

const CommentsSection = styled.div`
  background: white;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
`;

const CommentsTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: ${({ theme }) => theme.colors.textPrimary};
`;

const Comment = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
`;

const CommentAvatar = styled.img`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
`;

const CommentContent = styled.div`
  flex: 1;
`;

const CommentAuthor = styled.div`
  font-weight: 600;
  font-size: 14px;
  color: ${({ theme }) => theme.colors.textPrimary};
  margin-bottom: 4px;
`;

const CommentText = styled.div`
  font-size: 14px;
  color: ${({ theme }) => theme.colors.textPrimary};
  line-height: 1.4;
`;

const CommentTime = styled.div`
  font-size: 12px;
  color: ${({ theme }) => theme.colors.textSecondary};
  margin-top: 4px;
`;

const RelatedPins = styled.div`
  margin-top: 32px;
`;

const RelatedSectionTitle = styled.h2`
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 16px;
  color: ${({ theme }) => theme.colors.textPrimary};
`;

const RelatedGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
`;

const RelatedPin = styled.div`
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
  }
`;

const RelatedImage = styled.img`
  width: 100%;
  height: 150px;
  object-fit: cover;
`;

const RelatedPinTitle = styled.div`
  padding: 8px;
  font-size: 14px;
  font-weight: 500;
  color: ${({ theme }) => theme.colors.textPrimary};
  background: white;
`;

const PinDetail = () => {
  const { id } = useParams();
  const { pins, likePin, savePin, followUser } = useData();
  const [pin, setPin] = useState(null);
  console.log(".......pin", pin);

  const [loading, setLoading] = useState(true);
  const [visualSearchResults, setVisualSearchResults] = useState([]);
  const [isSearchingVisual, setIsSearchingVisual] = useState(false);

  useEffect(() => {
    // Find the pin by ID
    const foundPin = pins.find(p => p.id === parseInt(id));
    if (foundPin) {
      setPin(foundPin);
      // Automatically run visual search on load
      performVisualSearch(foundPin.imageUrl);
    }
    setLoading(false);
  }, [id, pins]);

  const performVisualSearch = async (imageUrl) => {
    setIsSearchingVisual(true);
    try {
      const response = await axios.post('http://localhost:5001/api/visual-search', { image_url: imageUrl });
      if (response.data && response.data.results) {
        setVisualSearchResults(response.data.results);
      }
    } catch (error) {
      console.error('Visual search failed', error);
    } finally {
      setIsSearchingVisual(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!pin) {
    return (
      <PinDetailContainer>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h2>Pin not found</h2>
          <p>The pin you're looking for doesn't exist.</p>
        </div>
      </PinDetailContainer>
    );
  }

  const mockComments = [
    {
      id: 1,
      author: 'Sarah',
      avatar: 'https://picsum.photos/50/50?random=sarah',
      text: 'This looks amazing! I love the creativity here.',
      time: '2 hours ago'
    },
    {
      id: 2,
      author: 'Mike',
      avatar: 'https://picsum.photos/50/50?random=mike',
      text: 'Great tutorial! Can\'t wait to try this myself.',
      time: '5 hours ago'
    },
    {
      id: 3,
      author: 'Emma',
      avatar: 'https://picsum.photos/50/50?random=emma',
      text: 'Perfect for my weekend project! Thanks for sharing.',
      time: '1 day ago'
    }
  ];

  const displayRelatedPins = visualSearchResults.length > 0
    ? visualSearchResults
    : pins.filter(p => p.id !== pin.id && p.category === pin.category).slice(0, 4);

  return (
    <PinDetailContainer>
      <PinImageContainer>
        <PinImage src={pin.image_url} alt={pin.title} />
        <VisualSearchButton onClick={() => performVisualSearch(pin.imageUrl)}>
          {isSearchingVisual ? 'Searching...' : '🔍 Visual Search'}
        </VisualSearchButton>
      </PinImageContainer>

      <PinContent>
        <PinMain>
          <PinTitle>{pin.title}</PinTitle>
          <PinDescription>{pin.description}</PinDescription>

          <PinMeta>
            <MetaItem>
              <span>❤️</span>
              <span>{pin.likes} likes</span>
            </MetaItem>
            <MetaItem>
              <span>📌</span>
              <span>{pin.saves} saves</span>
            </MetaItem>
            <MetaItem>
              <span>💬</span>
              <span>{mockComments.length} comments</span>
            </MetaItem>
          </PinMeta>

          <div style={{ display: 'flex', gap: '12px', marginBottom: '32px' }}>
            <button
              onClick={() => likePin(pin.id)}
              style={{
                padding: '12px 24px',
                borderRadius: '24px',
                border: 'none',
                backgroundColor: pin.isLiked ? '#E60023' : '#EFEFEF',
                color: pin.isLiked ? 'white' : '#111111',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              {pin.isLiked ? '❤️ Liked' : '🤍 Like'}
            </button>

            <button
              onClick={() => savePin(pin.id)}
              style={{
                padding: '12px 24px',
                borderRadius: '24px',
                border: 'none',
                backgroundColor: pin.isSaved ? '#E60023' : '#EFEFEF',
                color: pin.isSaved ? 'white' : '#111111',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              {pin.isSaved ? '📌 Saved' : '⭐ Save'}
            </button>

            <button style={{
              padding: '12px 24px',
              borderRadius: '24px',
              border: '1px solid #111111',
              backgroundColor: 'transparent',
              color: '#111111',
              fontWeight: '600',
              cursor: 'pointer'
            }}>
              💬 Comment
            </button>

            <button style={{
              padding: '12px 24px',
              borderRadius: '24px',
              border: '1px solid #111111',
              backgroundColor: 'transparent',
              color: '#111111',
              fontWeight: '600',
              cursor: 'pointer'
            }}>
              🔗 Share
            </button>
          </div>
        </PinMain>

        <PinSidebar>
          <AuthorCard>
            <AuthorHeader>
              <AuthorAvatar src={pin.authorAvatar} alt={pin.author} />
              <AuthorInfo>
                <AuthorName>{pin.author || 'Unknown'}</AuthorName>
                <AuthorUsername>@{(pin.author || 'unknown').toLowerCase()}</AuthorUsername>
              </AuthorInfo>
              <FollowButton onClick={() => followUser(pin.author)}>Follow</FollowButton>
            </AuthorHeader>
          </AuthorCard>

          <CommentsSection>
            <CommentsTitle>Comments</CommentsTitle>
            {mockComments.map(comment => (
              <Comment key={comment.id}>
                <CommentAvatar src={comment.avatar} alt={comment.author} />
                <CommentContent>
                  <CommentAuthor>{comment.author}</CommentAuthor>
                  <CommentText>{comment.text}</CommentText>
                  <CommentTime>{comment.time}</CommentTime>
                </CommentContent>
              </Comment>
            ))}
          </CommentsSection>
        </PinSidebar>
      </PinContent>

      <RelatedPins>
        <RelatedSectionTitle>
          {visualSearchResults.length > 0 ? 'Visually Similar Pins' : 'More like this'}
        </RelatedSectionTitle>
        <RelatedGrid>
          {displayRelatedPins.map(relatedPin => (
            <RelatedPin key={relatedPin.pin_id || relatedPin.id}>
              <RelatedImage src={relatedPin.image_url || relatedPin.imageUrl} alt={relatedPin.title || 'Similar Pin'} />
              <RelatedPinTitle>
                {relatedPin.title || 'Visually Similar'}
                {relatedPin.similarity_score && <span style={{ float: 'right', color: '#666' }}>{(relatedPin.similarity_score * 100).toFixed(0)}% Match</span>}
              </RelatedPinTitle>
            </RelatedPin>
          ))}
        </RelatedGrid>
      </RelatedPins>
    </PinDetailContainer>
  );
};

export default PinDetail;
