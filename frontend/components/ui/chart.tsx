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
    const parseCustomTime = (timeStr: string): Date => {
        const currentYear = new Date().getFullYear();
        const [datePart, timePart] = timeStr.split(' ');
        const [month, day] = datePart.split('-').map(Number);
        const [hours, minutes] = timePart.split(':').map(Number);
        
        return new Date(currentYear, month - 1, day, hours, minutes);
    };

    const interpolateValue = (
        value1: number | undefined,
        value2: number | undefined,
        ratio: number,
        decimals: number = 2
    ): number | undefined => {
        if (value1 === undefined || value2 === undefined) return value1;
        const interpolated = value1 + (value2 - value1) * ratio;
        return parseFloat(interpolated.toFixed(decimals));
    };

    const normalizeTimeIntervals = (rawData: ChartData[]): ChartData[] => {
        if (rawData.length < 2) return rawData;

        // Convert and sort data by timestamp
        const sortedData = [...rawData].sort((a, b) => 
            parseCustomTime(a.time).getTime() - parseCustomTime(b.time).getTime()
        );

        const minTime = parseCustomTime(sortedData[0].time).getTime();
        const maxTime = parseCustomTime(sortedData[sortedData.length - 1].time).getTime();
        
        const ONE_MINUTE = 60 * Number(process.env.CHART_TIME_INTERVAL) * 1000;
        const normalizedData: ChartData[] = [];
        
        let currentTime = minTime;
        while (currentTime <= maxTime) {
            // Find the surrounding data points
            const currentTimeObj = new Date(currentTime);
            
            // Find the two closest points
            let beforeIndex = -1;
            for (let i = 0; i < sortedData.length - 1; i++) {
                const time1 = parseCustomTime(sortedData[i].time).getTime();
                const time2 = parseCustomTime(sortedData[i + 1].time).getTime();
                
                if (time1 <= currentTime && currentTime <= time2) {
                    beforeIndex = i;
                    break;
                }
            }

            let interpolatedPoint: ChartData;
            
            if (beforeIndex === -1) {
                // Use nearest point if outside range
                interpolatedPoint = { ...sortedData[0] };
            } else if (beforeIndex === sortedData.length - 1) {
                interpolatedPoint = { ...sortedData[sortedData.length - 1] };
            } else {
                const before = sortedData[beforeIndex];
                const after = sortedData[beforeIndex + 1];
                
                const beforeTime = parseCustomTime(before.time).getTime();
                const afterTime = parseCustomTime(after.time).getTime();
                
                // Calculate interpolation ratio
                const ratio = (currentTime - beforeTime) / (afterTime - beforeTime);
                
                // Interpolate all possible values
                interpolatedPoint = {
                    time: `${(currentTimeObj.getMonth() + 1).toString().padStart(2, '0')}-${currentTimeObj.getDate().toString().padStart(2, '0')} ${currentTimeObj.getHours().toString().padStart(2, '0')}:${currentTimeObj.getMinutes().toString().padStart(2, '0')}`,
                    home: interpolateValue(before.home, after.home, ratio, 2),
                    away: interpolateValue(before.away, after.away, ratio, 2),
                    over: interpolateValue(before.over, after.over, ratio, 2),
                    under: interpolateValue(before.under, after.under, ratio, 2),
                    limit: interpolateValue(before.limit, after.limit, ratio, 2)
                };
            }

            normalizedData.push(interpolatedPoint);
            currentTime += ONE_MINUTE;
        }

        return normalizedData;
    };

    const normalizedData = normalizeTimeIntervals(data);

    return (
        <div className="mt-3">
            <ResponsiveContainer width="100%" height={400}>
                <LineChart data={normalizedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                        dataKey="time" 
                    />
                    <YAxis 
                        domain={[1, 'auto']}
                    />
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

