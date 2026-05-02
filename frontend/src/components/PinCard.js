import React from 'react';
import styled from 'styled-components';
import { Link } from 'react-router-dom';
import { useData } from '../context/DataContext';

const PinCardContainer = styled.div`
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
  margin-bottom: 16px;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
`;

const PinImage = styled.img`
  width: 100%;
  display: block;
  object-fit: cover;
  transition: transform 0.2s ease;
  
  ${PinCardContainer}:hover & {
    transform: scale(1.05);
  }
`;

const PinContent = styled.div`
  padding: 12px;
`;

const PinTitle = styled.h3`
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  color: ${({ theme }) => theme.colors.textPrimary};
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const PinDescription = styled.p`
  font-size: 12px;
  color: ${({ theme }) => theme.colors.textSecondary};
  line-height: 1.4;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const PinAuthor = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
`;

const AuthorAvatar = styled.img`
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
`;

const AuthorName = styled.span`
  font-size: 12px;
  font-weight: 500;
  color: ${({ theme }) => theme.colors.textPrimary};
`;

const PinActions = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: ${({ theme }) => theme.colors.background};
`;

const ActionButton = styled.button`
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 20px;
  border: none;
  background-color: ${({ theme, variant }) => 
    variant === 'primary' ? theme.colors.primary : 'transparent'};
  color: ${({ theme, variant }) => 
    variant === 'primary' ? 'white' : theme.colors.textPrimary};
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: ${({ theme, variant }) => 
      variant === 'primary' ? theme.colors.primaryHover : theme.colors.backgroundSecondary};
  }
`;

const ActionCount = styled.span`
  font-size: 12px;
  color: ${({ theme }) => theme.colors.textSecondary};
`;

const PinCard = ({ pin }) => {
  const { likePin, savePin } = useData();

  const handleLike = (e) => {
    e.preventDefault();
    e.stopPropagation();
    likePin(pin.id);
  };

  const handleSave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    savePin(pin.id);
  };

  return (
    
    <Link to={`/pin/${pin.id}`} className="pin-link">
      <PinCardContainer>
        <div style={{ overflow: 'hidden', borderRadius: '16px 16px 0 0' }}>
          <PinImage
            src={pin.imageUrl}
            alt={pin.title}
            style={{ height: `${Math.floor(Math.random() * 200) + 200}px` }}
          />
        </div>
        
        <PinContent>
          <PinTitle>{pin.title}</PinTitle>
          {pin.description && (
            <PinDescription>{pin.description}</PinDescription>
          )}
          
          <PinAuthor>
            <AuthorAvatar src={pin.authorAvatar} alt={pin.author} />
            <AuthorName>{pin.author}</AuthorName>
          </PinAuthor>
        </PinContent>
        
        <PinActions>
          <ActionButton 
            variant={pin.isLiked ? 'primary' : 'secondary'}
            onClick={handleLike}
          >
            {pin.isLiked ? '🔴' : '⚪'} Like
          </ActionButton>
          
          <ActionButton variant="secondary">
            💬 Comment
          </ActionButton>
          
          <ActionButton 
            variant={pin.isSaved ? 'primary' : 'secondary'}
            onClick={handleSave}
          >
            {pin.isSaved ? '📌' : '⭐'} Save
          </ActionButton>
        </PinActions>
        
        <div style={{ padding: '0 12px 12px', display: 'flex', gap: '16px' }}>
          <ActionCount>{pin.likes} likes</ActionCount>
          <ActionCount>{pin.saves} saves</ActionCount>
        </div>
      </PinCardContainer>
    </Link>
  );
};

export default PinCard;
