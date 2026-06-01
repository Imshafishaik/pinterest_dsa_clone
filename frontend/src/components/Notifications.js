import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { useData } from '../context/DataContext';
import axios from 'axios';

const NotificationsContainer = styled.div`
  position: relative;
`;

const IconButton = styled.button`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: ${({ $isOpen, theme }) => $isOpen ? theme.colors.backgroundSecondary : 'transparent'};
  border: none;
  cursor: pointer;
  transition: background-color 0.2s ease;
  color: ${({ theme }) => theme.colors.textPrimary};
  position: relative;
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.backgroundSecondary};
  }
`;

const Badge = styled.div`
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  background-color: ${({ theme }) => theme.colors.primary};
  border-radius: 50%;
`;

const DropdownMenu = styled.div`
  position: absolute;
  top: 50px;
  right: 0;
  width: 320px;
  max-height: 400px;
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  overflow-y: auto;
  z-index: 1000;
  padding: 8px 0;
`;

const DropdownHeader = styled.div`
  padding: 16px;
  font-weight: 600;
  font-size: 16px;
  border-bottom: 1px solid ${({ theme }) => theme.colors.border};
`;

const NotificationItem = styled.div`
  padding: 12px 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  transition: background-color 0.2s;
  background-color: ${({ $read }) => $read ? 'white' : '#fef2f2'};
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.backgroundSecondary};
  }
`;

const Avatar = styled.img`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
`;

const Content = styled.div`
  flex: 1;
`;

const Message = styled.p`
  margin: 0;
  font-size: 14px;
  color: ${({ theme }) => theme.colors.textPrimary};
`;

const Time = styled.span`
  font-size: 12px;
  color: ${({ theme }) => theme.colors.textSecondary};
  margin-top: 4px;
  display: block;
`;

const EmptyState = styled.div`
  padding: 24px;
  text-align: center;
  color: ${({ theme }) => theme.colors.textSecondary};
`;

const Notifications = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [hasUnread, setHasUnread] = useState(false);
  const dropdownRef = useRef(null);
  const { currentUser } = useData();

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const userId = currentUser?.id || 'alice';
        const response = await axios.get(`http://localhost:5001/api/notifications/${userId}`);
        if (response.data && response.data.length > 0) {
          setNotifications(response.data);
          setHasUnread(response.data.some(n => !n.read));
        }
      } catch (error) {
        console.error('Failed to fetch notifications', error);
      }
    };

    if (isOpen) {
      fetchNotifications();
      setHasUnread(false);
    } else {
      // Periodic fetch when closed
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    }
  }, [isOpen, currentUser]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatTime = (timestamp) => {
    const diff = Math.floor(Date.now() / 1000 - timestamp);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <NotificationsContainer ref={dropdownRef}>
      <IconButton 
        $isOpen={isOpen} 
        onClick={() => setIsOpen(!isOpen)}
        title="Notifications"
      >
        🔔
        {hasUnread && <Badge />}
      </IconButton>

      {isOpen && (
        <DropdownMenu>
          <DropdownHeader>Updates</DropdownHeader>
          {notifications.length === 0 ? (
            <EmptyState>No new notifications</EmptyState>
          ) : (
            notifications.map((notif, idx) => (
              <NotificationItem key={notif.id || idx} $read={notif.read}>
                <Avatar src={`https://picsum.photos/40/40?random=${idx}`} />
                <Content>
                  <Message>{notif.message}</Message>
                  <Time>{formatTime(notif.timestamp)}</Time>
                </Content>
              </NotificationItem>
            ))
          )}
        </DropdownMenu>
      )}
    </NotificationsContainer>
  );
};

export default Notifications;
