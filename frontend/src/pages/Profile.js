import React from 'react';
import styled from 'styled-components';
import Masonry from 'react-masonry-css';
import { useData } from '../context/DataContext';
import PinCard from '../components/PinCard';

const ProfileContainer = styled.div`
  padding: 20px 0;
`;

const ProfileHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 40px;
  
  @media (max-width: 768px) {
    flex-direction: column;
    text-align: center;
  }
`;

const ProfileAvatar = styled.img`
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`;

const ProfileInfo = styled.div`
  flex: 1;
`;

const ProfileName = styled.h1`
  font-size: 32px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.textPrimary};
  margin-bottom: 8px;
`;

const ProfileUsername = styled.p`
  font-size: 18px;
  color: ${({ theme }) => theme.colors.textSecondary};
  margin-bottom: 16px;
`;

const ProfileBio = styled.p`
  font-size: 16px;
  line-height: 1.6;
  color: ${({ theme }) => theme.colors.textPrimary};
  margin-bottom: 24px;
`;

const ProfileStats = styled.div`
  display: flex;
  gap: 32px;
  
  @media (max-width: 768px) {
    justify-content: center;
  }
`;

const StatItem = styled.div`
  text-align: center;
`;

const StatNumber = styled.div`
  font-size: 24px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.textPrimary};
`;

const StatLabel = styled.div`
  font-size: 14px;
  color: ${({ theme }) => theme.colors.textSecondary};
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 12px;
  margin-top: 24px;
  
  @media (max-width: 768px) {
    justify-content: center;
  }
`;

const ActionButton = styled.button`
  padding: 12px 24px;
  border-radius: 24px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  
  ${({ variant, theme }) => {
    if (variant === 'primary') {
      return `
        background-color: ${theme.colors.primary};
        color: white;
        &:hover {
          background-color: ${theme.colors.primaryHover};
        }
      `;
    } else {
      return `
        background-color: ${theme.colors.backgroundSecondary};
        color: ${theme.colors.textPrimary};
        &:hover {
          background-color: ${theme.colors.border};
        }
      `;
    }
  }}
`;

const TabsContainer = styled.div`
  border-bottom: 1px solid ${({ theme }) => theme.colors.border};
  margin-bottom: 32px;
`;

const TabsList = styled.ul`
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
`;

const TabButton = styled.button`
  padding: 16px 24px;
  border: none;
  background: none;
  font-size: 16px;
  font-weight: 500;
  color: ${({ theme, active }) => 
    active ? theme.colors.textPrimary : theme.colors.textSecondary};
  border-bottom: 2px solid ${({ theme, active }) => 
    active ? theme.colors.primary : 'transparent'};
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    color: ${({ theme }) => theme.colors.textPrimary};
  }
`;

const Profile = () => {
  const { pins, likePin, savePin, followUser } = useData();
  const [activeTab, setActiveTab] = React.useState('created');
  const [userPins, setUserPins] = React.useState([]);

  // Mock user data
  const user = {
    name: 'Alice Johnson',
    username: '@alice_creative',
    avatar: 'https://picsum.photos/200/200?random=alice',
    bio: 'DIY enthusiast | Home decor lover | Finding inspiration in everyday things 🎨✨',
    followers: 1234,
    following: 567,
    pins: 89,
    isFollowing: false
  };

  React.useEffect(() => {
    // Filter pins for this user (mock data)
    const userCreatedPins = pins.filter(pin => pin.author === 'Alice');
    setUserPins(userCreatedPins);
  }, [pins]);

  const handleFollow = () => {
    followUser('alice');
  };

  const breakpointColumnsObj = {
    default: 4,
    1100: 3,
    700: 2,
    500: 1
  };

  return (
    <ProfileContainer>
      <ProfileHeader>
        <ProfileAvatar src={user.avatar} alt={user.name} />
        <ProfileInfo>
          <ProfileName>{user.name}</ProfileName>
          <ProfileUsername>{user.username}</ProfileUsername>
          <ProfileBio>{user.bio}</ProfileBio>
          
          <ProfileStats>
            <StatItem>
              <StatNumber>{user.pins}</StatNumber>
              <StatLabel>Pins</StatLabel>
            </StatItem>
            <StatItem>
              <StatNumber>{user.followers.toLocaleString()}</StatNumber>
              <StatLabel>Followers</StatLabel>
            </StatItem>
            <StatItem>
              <StatNumber>{user.following}</StatNumber>
              <StatLabel>Following</StatLabel>
            </StatItem>
          </ProfileStats>
          
          <ActionButtons>
            <ActionButton variant="primary" onClick={handleFollow}>
              {user.isFollowing ? 'Following' : 'Follow'}
            </ActionButton>
            <ActionButton variant="secondary">Message</ActionButton>
            <ActionButton variant="secondary">Share</ActionButton>
          </ActionButtons>
        </ProfileInfo>
      </ProfileHeader>

      <TabsContainer>
        <TabsList>
          <TabButton 
            active={activeTab === 'created'} 
            onClick={() => setActiveTab('created')}
          >
            Created
          </TabButton>
          <TabButton 
            active={activeTab === 'saved'} 
            onClick={() => setActiveTab('saved')}
          >
            Saved
          </TabButton>
          <TabButton 
            active={activeTab === 'liked'} 
            onClick={() => setActiveTab('liked')}
          >
            Liked
          </TabButton>
        </TabsList>
      </TabsContainer>

      {activeTab === 'created' && (
        <Masonry
          breakpointCols={breakpointColumnsObj}
          className="my-masonry-grid"
          columnClassName="my-masonry-column"
        >
          {userPins.map((pin) => (
            <PinCard key={pin.id} pin={pin} />
          ))}
        </Masonry>
      )}

      {activeTab === 'saved' && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h3>Saved Pins</h3>
          <p>Pins you've saved will appear here</p>
        </div>
      )}

      {activeTab === 'liked' && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h3>Liked Pins</h3>
          <p>Pins you've liked will appear here</p>
        </div>
      )}
    </ProfileContainer>
  );
};

export default Profile;
