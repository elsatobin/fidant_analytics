// App.js
import React, { useState } from "react";
import { Login } from "./Login";
import { UsageStats } from "./components/UsageStats";

function App() {
  const [loggedIn, setLoggedIn] = useState(false);

  return (
    <div>
      {!loggedIn ? (
        <Login onLoginSuccess={() => setLoggedIn(true)} />
      ) : (
        <UsageStats />
      )}
    </div>
  );
}

// ✅ default export
export default App;