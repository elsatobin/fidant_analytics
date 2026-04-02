import React, { useState } from 'react';
import Login from './Login';
import UsageStats from './components/UsageStats';

const App: React.FC = () => {
  const [loggedIn, setLoggedIn] = useState(false);

  return (
    <div>
      {loggedIn ? (
        <UsageStats />
      ) : (
        <Login onLoginSuccess={() => setLoggedIn(true)} />
      )}
    </div>
  );
};

export default App;