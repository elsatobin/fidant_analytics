import React, { useEffect, useState } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export const UsageStats = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Get token from localStorage
        const token = localStorage.getItem("token");
        if (!token) throw new Error("No token found. Please login.");

        // Fetch usage stats with Authorization header
        const res = await axios.get("http://localhost:5000/api/usage/stats?days=7", {
          headers: { Authorization: `Bearer ${token}` },
        });

        setData(res.data);
      } catch (err) {
        console.error(err);
        setError(err.response?.data?.detail || err.message || "Failed to fetch data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Usage Stats ({data?.plan})</h2>

      {/* Bar Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data?.days}>
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="committed" fill="#4ade80" name="Committed" />
          <Bar dataKey="reserved" fill="#facc15" name="Reserved" />
        </BarChart>
      </ResponsiveContainer>

      {/* Summary */}
      <div style={{ marginTop: "1rem" }}>
        <p>Total committed: {data?.summary?.total_committed}</p>
        <p>Average per day: {data?.summary?.avg_daily}</p>
        <p>
          Peak day: {data?.summary?.peak_day?.date} ({data?.summary?.peak_day?.count})
        </p>
        <p>Current streak: {data?.summary?.current_streak} days</p>
      </div>

      {/* Today's Progress */}
      {data?.days?.length > 0 && (
        <div style={{ marginTop: "1rem" }}>
          <p>Today's Progress:</p>
          <div
            style={{
              background: "#e5e7eb",
              width: "100%",
              height: "20px",
              borderRadius: "5px",
            }}
          >
            <div
              style={{
                width: `${data.days[data.days.length - 1].utilization * 100}%`,
                height: "100%",
                background: "#3b82f6",
                borderRadius: "5px",
              }}
            ></div>
          </div>
          <p>
            {Math.round(data.days[data.days.length - 1].utilization * 100)}% of daily limit
          </p>
        </div>
      )}
    </div>
  );
};