import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import styled, { ThemeProvider, createGlobalStyle } from 'styled-components';
import Header from './components/Header';
import CreatePin from './components/CreatePin';
import Login from './components/Login';
import Signup from './components/Signup';
import Home from './pages/Home';
import Feed from './pages/Feed';
import Search from './pages/Search';
import Profile from './pages/Profile';
import PinDetail from './pages/PinDetail';
import Explore from './pages/Explore';
import { DataProvider } from './context/DataContext';

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Roboto', sans-serif;
    background-color: #ffffff;
    color: #333;
    line-height: 1.6;
  }

  a {
    text-decoration: none;
    color: inherit;
  }

  button {
    border: none;
    background: none;
    cursor: pointer;
    font-family: inherit;
  }

  ul, li {
    list-style: none;
  }
`;

const theme = {
  colors: {
    primary: '#E60023',
    primaryHover: '#AD081B',
    secondary: '#111111',
    textPrimary: '#111111',
    textSecondary: '#767676',
    background: '#ffffff',
    backgroundSecondary: '#EFEFEF',
    border: '#EFEFEF',
    shadow: 'rgba(0, 0, 0, 0.1)',
  },
  breakpoints: {
    mobile: '768px',
    tablet: '1024px',
    desktop: '1200px',
  },
};

const AppContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
`;

const MainContent = styled.main`
  flex: 1;
  padding-top: 60px;
`;

function App() {
  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <DataProvider>
        <Router>
          <AppContainer>
            <Header />
            <MainContent>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/feed" element={<Feed />} />
                <Route path="/search" element={<Search />} />
                <Route path="/explore" element={<Explore />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/pin/:id" element={<PinDetail />} />
                <Route path="/create" element={<CreatePin />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
              </Routes>
            </MainContent>
          </AppContainer>
        </Router>
      </DataProvider>
    </ThemeProvider>
  );
}

export default App;
