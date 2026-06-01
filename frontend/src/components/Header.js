import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styled, { ThemeConsumer } from 'styled-components';
import { useData } from '../context/DataContext';
import Notifications from './Notifications';

const HeaderContainer = styled.header`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: white;
  border-bottom: 1px solid ${({ theme }) => theme.colors.border};
  z-index: 1000;
  display: flex;
  align-items: center;
  padding: 0 16px;
`;

const HeaderContent = styled.div`
  max-width: 1260px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled(Link)`
  font-size: 24px;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary};
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const LogoIcon = styled.div`
  width: 32px;
  height: 32px;
  background-color: ${({ theme }) => theme.colors.primary};
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
`;

const Nav = styled.nav`
  display: flex;
  align-items: center;
  gap: 24px;
  
  @media (max-width: 768px) {
    display: none;
  }
`;

const NavLink = styled(Link)`
  color: ${({ theme }) => theme.colors.textPrimary};
  text-decoration: none;
  font-weight: 500;
  font-size: 16px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.backgroundSecondary};
  }
  
  &.active {
    background-color: ${({ theme }) => theme.colors.backgroundSecondary};
    color: ${({ theme }) => theme.colors.primary};
  }
`;

const SearchContainer = styled.div`
  flex: 1;
  max-width: 600px;
  margin: 0 24px;
  
  @media (max-width: 768px) {
    margin: 0 16px;
    max-width: none;
  }
`;

const SearchBox = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const SearchInput = styled.input`
  width: 100%;
  padding: 12px 16px 12px 44px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: 24px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.2s ease;
  
  &:focus {
    border-color: ${({ theme }) => theme.colors.textPrimary};
  }
  
  &::placeholder {
    color: ${({ theme }) => theme.colors.textSecondary};
  }
`;

const SearchIcon = styled.div`
  position: absolute;
  left: 16px;
  color: ${({ theme }) => theme.colors.textSecondary};
  pointer-events: none;
`;

const Actions = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const IconButton = styled.button`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s ease;
  color: ${({ theme }) => theme.colors.textPrimary};
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.backgroundSecondary};
  }
`;

const Avatar = styled.button`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid ${({ theme }) => theme.colors.border};
  cursor: pointer;
  padding: 0;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`;

const CreateButton = styled.button`
  background-color: ${({ theme }) => theme.colors.primary};
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 24px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.primaryHover};
  }
  
  @media (max-width: 768px) {
    display: none;
  }
`;

const MobileMenuButton = styled.button`
  display: none;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: ${({ theme }) => theme.colors.textPrimary};
  
  @media (max-width: 768px) {
    display: block;
  }
`;

const UserAvatar = styled.img`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 8px;
`;

const Username = styled.span`
  font-weight: 600;
  color: #333;
  margin-right: 12px;
`;

const LogoutButton = styled.button`
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;

  &:hover {
    background: #f0f0f0;
    color: #333;
  }
`;

const SearchButton = styled.button`
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
  padding: 8px;
  border-radius: 50%;

  &:hover {
    background: #f0f0f0;
    color: #333;
  }
`;

const Header = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const navigate = useNavigate();
  const { searchPins, loading, currentUser, logout } = useData();

  const handleCreatePin = () => {
    navigate('/create');
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);

    if (query.trim()) {
      setIsSearching(true);
      searchPins(query);
      navigate('/search');
    } else {
      setIsSearching(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate('/search');
    }
  };

  return (
    <HeaderContainer>
      <HeaderContent>
        <Logo to="/">
          <LogoIcon>P</LogoIcon>
          Pinterest
        </Logo>

        <Nav>
          <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
            Home
          </NavLink>
          <NavLink to="/feed" className={({ isActive }) => isActive ? 'active' : ''}>
            Feed
          </NavLink>
          <NavLink to="/explore">Explore</NavLink>
        </Nav>

        <SearchContainer>
          <form onSubmit={handleSearchSubmit}>
            <SearchBox>
              <SearchIcon>🔍</SearchIcon>
              <SearchInput
                type="text"
                placeholder="Search for ideas"
                value={searchQuery}
                onChange={handleSearch}
              />
            </SearchBox>
          </form>
        </SearchContainer>

        <Actions>
          {currentUser ? (
            <>
              <UserAvatar src={currentUser.avatar_url || `https://picsum.photos/50/50?random=${currentUser.id}`} />
              <Username>{currentUser.username}</Username>
              <LogoutButton onClick={handleLogout}>Logout</LogoutButton>
              <CreateButton onClick={handleCreatePin}>Create</CreateButton>
            </>
          ) : (
            <>
              <CreateButton onClick={() => navigate('/login')}>Login</CreateButton>
              <CreateButton onClick={() => navigate('/signup')}>Sign Up</CreateButton>
            </>
          )}
          {/* <SearchButton onClick={() => setIsSearching(!isSearching)}>
            {isSearching ? '✕' : '🔍'}
          </SearchButton>
          <Notifications />
          <IconButton title="Messages">
            💬
          </IconButton>
          <Avatar title="Profile">
            <img
              src="https://picsum.photos/100/100?random=user"
              alt="Profile"
            />
          </Avatar> */}

          <MobileMenuButton>
            ☰
          </MobileMenuButton>
        </Actions>
      </HeaderContent>
    </HeaderContainer>
  );
};

export default Header;
