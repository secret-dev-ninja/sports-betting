import * as React from "react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Define the type for the data
interface ChartData {
    time: string;  // Date-time as string
    home?: number; // First set of values (e.g., negative values)
    away?: number; // Second set of values (e.g., positive values)
    over?: number;
    under?: number;
    limit?: number;
}

interface ChartComponentProps {
    data: ChartData[]; // The data prop must be an array of ChartData objects
}

const ChartComponent: React.FC<ChartComponentProps> = React.memo(({ data }) => {
    return (
        <div className="mt-3">
            <ResponsiveContainer width="100%" height={400}>
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[1, 'auto']}/>
                    <Tooltip />
                    <Legend />

                    {data.some(item => item.limit !== undefined) && (
                        <>
                            <YAxis yAxisId="right" orientation="right" />
                            <Line yAxisId="right" type="monotone" dataKey="limit" stroke="#FF6347" />
                        </>
                    )}

                    {data.some(item => item.home !== undefined) && <Line type="monotone" dataKey="home" stroke="#4682B4" />}
                    {data.some(item => item.away !== undefined) && <Line type="monotone" dataKey="away" stroke="#32CD32" />}
                    {data.some(item => item.over !== undefined) && <Line type="monotone" dataKey="over" stroke="#FFD700" />}
                    {data.some(item => item.under !== undefined) && <Line type="monotone" dataKey="under" stroke="#FF69B4" />}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
});

export default ChartComponent;

