import * as React from "react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Define the type for the data
interface ChartData {
time: string;  // Date-time as string
home: number; // First set of values (e.g., negative values)
away: number; // Second set of values (e.g., positive values)
}

interface ChartComponentProps {
data: ChartData[]; // The data prop must be an array of ChartData objects
}

const ChartComponent: React.FC<ChartComponentProps> = React.memo(({ data }) => {
    return (
        <div>
        <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />

            {/* First line (Graph 1) */}
            <Line type="monotone" dataKey="home" stroke="#8884d8" />

            {/* Second line (Graph 2) */}
            <Line type="monotone" dataKey="away" stroke="#82ca9d" />
            </LineChart>
        </ResponsiveContainer>
        </div>
    );
});

export default ChartComponent;

