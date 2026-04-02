import React, { useState } from "react";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function UsageChart() {
    const [token, setToken] = useState("");
    const [chartData, setChartData] = useState(null);

    const loadData = async () => {
        const res = await fetch("http://localhost:5000/api/usage/stats?days=7", {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!res.ok) {
            alert("Failed to load data");
            return;
        }

        const data = await res.json();

        setChartData({
            labels: data.days.map(d => d.date),
            datasets: [
                {
                    label: "Committed",
                    data: data.days.map(d => d.committed),
                    borderColor: "green",
                    backgroundColor: "rgba(0,255,0,0.2)"
                },
                {
                    label: "Reserved",
                    data: data.days.map(d => d.reserved),
                    borderColor: "orange",
                    backgroundColor: "rgba(255,165,0,0.2)"
                }
            ]
        });
    };

    return (
        <div>
            <h2>Usage Dashboard</h2>
            <input
                placeholder="JWT token"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                style={{ width: 400 }}
            />
            <button onClick={loadData}>Load Data</button>

            {chartData && <Line data={chartData} />}
        </div>
    );
}