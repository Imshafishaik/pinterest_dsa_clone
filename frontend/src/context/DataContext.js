import React, { createContext, useContext, useReducer, useEffect } from 'react';
import axios from 'axios';

const initialState = {
  pins: [],
  boards: [],
  users: [],
  feed: [],
  searchResults: [],
  recommendations: [],
  trending: [],
  loading: false,
  error: null,
  currentUser: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null,
  notifications: [],
};

const actionTypes = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_PINS: 'SET_PINS',
  SET_BOARDS: 'SET_BOARDS',
  SET_USERS: 'SET_USERS',
  SET_FEED: 'SET_FEED',
  SET_SEARCH_RESULTS: 'SET_SEARCH_RESULTS',
  SET_RECOMMENDATIONS: 'SET_RECOMMENDATIONS',
  SET_TRENDING: 'SET_TRENDING',
  ADD_PIN: 'ADD_PIN',
  FOLLOW_USER: 'FOLLOW_USER',
  LIKE_PIN: 'LIKE_PIN',
  SAVE_PIN: 'SAVE_PIN',
  UNLIKE_PIN: 'UNLIKE_PIN',
  UNSAVE_PIN: 'UNSAVE_PIN',
  SET_CURRENT_USER: 'SET_CURRENT_USER',
};

const dataReducer = (state, action) => {
  switch (action.type) {
    case actionTypes.SET_LOADING:
      return { ...state, loading: action.payload };
    case actionTypes.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    case actionTypes.SET_PINS:
      return { ...state, pins: action.payload, loading: false };
    case actionTypes.SET_BOARDS:
      return { ...state, boards: action.payload, loading: false };
    case actionTypes.SET_USERS:
      return { ...state, users: action.payload, loading: false };
    case actionTypes.SET_FEED:
      return { ...state, feed: action.payload, loading: false };
    case actionTypes.SET_SEARCH_RESULTS:
      return { ...state, searchResults: action.payload, loading: false };
    case actionTypes.SET_RECOMMENDATIONS:
      return { ...state, recommendations: action.payload, loading: false };
    case actionTypes.SET_TRENDING:
      return { ...state, trending: action.payload, loading: false };
    case actionTypes.SET_CURRENT_USER:
      return { ...state, currentUser: action.payload, loading: false };
    case actionTypes.SET_NOTIFICATIONS:
      return { ...state, notifications: action.payload };
    case actionTypes.ADD_PIN:
      return { ...state, pins: [...state.pins, action.payload] };
    case actionTypes.LIKE_PIN:
      return {
        ...state,
        pins: state.pins.map(pin =>
          pin.id === action.payload
            ? { ...pin, likes: pin.likes + 1, isLiked: true }
            : pin
        ),
      };
    case actionTypes.SAVE_PIN:
      return {
        ...state,
        pins: state.pins.map(pin =>
          pin.id === action.payload
            ? { ...pin, saves: pin.saves + 1, isSaved: true }
            : pin
        ),
      };
    case actionTypes.FOLLOW_USER:
      return {
        ...state,
        users: state.users.map(user =>
          user.id === action.payload
            ? { ...user, isFollowing: true, followers: user.followers + 1 }
            : user
        ),
      };
    default:
      return state;
  }
};

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5001',
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const DataContext = createContext();

export const DataProvider = ({ children }) => {
  const [state, dispatch] = useReducer(dataReducer, initialState);

  const setLoading = (loading) => {
    dispatch({ type: actionTypes.SET_LOADING, payload: loading });
  };

  const setError = (error) => {
    dispatch({ type: actionTypes.SET_ERROR, payload: error });
  };

  const fetchPins = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/pins');
      const pins = response.data.map(pin => ({
        ...pin,
        id: pin.pin_id ? parseInt(pin.pin_id.replace('pin', '')) : pin.id,
        isLiked: pin.isLiked || false,
        isSaved: pin.isSaved || false,
      }));
      dispatch({ type: actionTypes.SET_PINS, payload: pins });
    } catch (error) {
      setError(error.message);
    }
  };

  const fetchFeed = async (userId = 'alice') => {
    try {
      setLoading(true);
      const response = await api.get(`/api/feed/${userId}`);
      const feed = response.data.map(item => ({
        ...item.pin_data,
        id: item.pin_data.pin_id ? parseInt(item.pin_data.pin_id.replace('pin', '')) : item.pin_data.id,
        rankingScore: item.ranking_score || 0.8,
        isLiked: item.pin_data.isLiked || false,
        isSaved: item.pin_data.isSaved || false,
      }));
      dispatch({ type: actionTypes.SET_FEED, payload: feed });
    } catch (error) {
      setError(error.message);
    }
  };

  const searchPins = async (query) => {
    try {
      setLoading(true);
      const response = await api.get('/api/search', { params: { q: query } });
      const results = response.data.map(item => ({
        ...item,
        id: item.pin_id ? parseInt(item.pin_id.replace('pin', '')) : item.id,
        isLiked: item.isLiked || false,
        isSaved: item.isSaved || false,
      }));
      dispatch({ type: actionTypes.SET_SEARCH_RESULTS, payload: results });
    } catch (error) {
      setError(error.message);
    }
  };

  const fetchRecommendations = async (userId = 'alice') => {
    try {
      setLoading(true);
      const response = await api.get(`/api/recommendations/${userId}`);
      const recommendations = response.data.map(item => ({
        ...item,
        id: item.pin_id ? parseInt(item.pin_id.replace('pin', '')) : item.id,
        isLiked: item.isLiked || false,
        isSaved: item.isSaved || false,
      }));
      dispatch({ type: actionTypes.SET_RECOMMENDATIONS, payload: recommendations });
    } catch (error) {
      setError(error.message);
    }
  };

  const fetchTrending = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/trending');
      const trending = response.data.map(item => ({
        ...item,
        id: item.pin_id ? parseInt(item.pin_id.replace('pin', '')) : item.id,
        isLiked: item.isLiked || false,
        isSaved: item.isSaved || false,
      }));
      dispatch({ type: actionTypes.SET_TRENDING, payload: trending });
    } catch (error) {
      setError(error.message);
    }
  };

  const likePin = async (pinId) => {
    try {
      await api.post(`/api/pin/pin${pinId}/like`);
      dispatch({ type: actionTypes.LIKE_PIN, payload: pinId });
    } catch (error) {
      console.error('Error liking pin:', error);
    }
  };

  const savePin = async (pinId) => {
    try {
      await api.post(`/api/pin/pin${pinId}/save`);
      dispatch({ type: actionTypes.SAVE_PIN, payload: pinId });
    } catch (error) {
      console.error('Error saving pin:', error);
    }
  };

  const createPin = async (pinData) => {
    try {
      setLoading(true);
      const response = await api.post('/api/pins', pinData);
      const newPin = {
        ...response.data,
        id: response.data.pin_id ? parseInt(response.data.pin_id.replace('pin', '')) : response.data.id,
        isLiked: false,
        isSaved: false,
      };
      dispatch({ type: actionTypes.ADD_PIN, payload: newPin });
      return newPin;
    } catch (error) {
      setError(error.message);
      throw error;
    }
  };

  const login = async (credentials) => {
    try {
      setLoading(true);
      const response = await api.post('/api/auth/login', credentials);
      
      // Store token in localStorage
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      dispatch({ type: actionTypes.SET_CURRENT_USER, payload: response.data.user });
      return response.data;
    } catch (error) {
      setError(error.response?.data?.error || error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      setLoading(true);
      const response = await api.post('/api/auth/register', userData);
      
      // Store token in localStorage
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      dispatch({ type: actionTypes.SET_CURRENT_USER, payload: response.data.user });
      return response.data;
    } catch (error) {
      setError(error.response?.data?.error || error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await api.post('/api/auth/logout', {}, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
      
      // Clear localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      dispatch({ type: actionTypes.SET_CURRENT_USER, payload: null });
    } catch (error) {
      setError(error.message);
    }
  };

  const getCurrentUser = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        return null;
      }
      
      const response = await api.get('/api/auth/current', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      dispatch({ type: actionTypes.SET_CURRENT_USER, payload: response.data.user });
      return response.data.user;
    } catch (error) {
      // If token is invalid, clear localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      dispatch({ type: actionTypes.SET_CURRENT_USER, payload: null });
      return null;
    }
  };

  const followUser = async (userId) => {
    try {
      await api.post(`/api/user/${userId}/follow`);
      dispatch({ type: actionTypes.FOLLOW_USER, payload: userId });
    } catch (error) {
      console.error('Error following user:', error);
    }
  };

  useEffect(() => {
    fetchPins();
    fetchFeed();
    fetchRecommendations();
    fetchTrending();
    // Restore session on mount
    getCurrentUser();
  }, []);

  const value = {
    ...state,
    fetchPins,
    fetchFeed,
    searchPins,
    fetchRecommendations,
    fetchTrending,
    likePin,
    savePin,
    createPin,
    followUser,
    login,
    register,
    logout,
    getCurrentUser,
    setLoading,
    setError,
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};

export default DataContext;
