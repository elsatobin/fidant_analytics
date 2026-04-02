import React, { useState } from 'react';
import Login from './Login';
import UsageStats from './components/UsageStats';

const App: React.FC = () => {
  const [loggedIn, setLoggedIn] = useState(
    // Restore session if token already exists
    () => Boolean(localStorage.getItem('access_token'))
  );

  const handleLoginSuccess = (token: string) => {
    localStorage.setItem('access_token', token);
    setLoggedIn(true);
  };

  return (
    <div>
      {loggedIn ? (
        <UsageStats />
      ) : (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}
    </div>
  );
};

export default App;
