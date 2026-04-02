import React, { useState } from "react";
import axios from "axios";

export const Login = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState("");

  const login = async () => {
    try {
      const res = await axios.post("http://127.0.0.1:5000/login", { email });
      const token = res.data.access_token;

      // Save token to localStorage
      localStorage.setItem("token", token);

      alert("Login successful!");
      onLoginSuccess(); // optional: 부모 컴포넌트에 로그인 완료 알림
    } catch (err) {
      console.error(err);
      alert("Login failed");
    }
  };

  return (
    <div>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter email"
      />
      <button onClick={login}>Login</button>
    </div>
  );
};