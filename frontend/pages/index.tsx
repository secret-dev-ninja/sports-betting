import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bell } from "lucide-react";
import dotenv from "dotenv";

dotenv.config();

// Define the shape of the odds update data
interface OddsUpdate {
  sport_id: number;
  event_id: string;
  home_team: string;
  away_team: string;
  table_updated: string;
  update_time: string;
  id: string;
}

const OddsDashboard = () => {
      const [updates, setUpdates] = useState<OddsUpdate[]>([]);
      const [activeTab, setActiveTab] = useState<Number>(1);
      const [selectedData, setSelectedData] = useState<any | null>(null);

      useEffect(() => {
        const ws = new WebSocket(process.env.REACT_APP_WS_URL);
        
        ws.onopen = () => {
          console.log('Connected to WebSocket');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
    
            if (data && data.sport_id && data.event_id) {
              setUpdates(prevUpdates => {
                // Find the index of the existing update, if any
                const existingUpdateIndex = prevUpdates.findIndex(
                  (update) =>
                    update.sport_id === data.sport_id &&
                    update.event_id === data.event_id &&
                    update.home_team === data.home_team &&
                    update.away_team === data.away_team
                );
    
                let updatedUpdates = [...prevUpdates];
    
                if (existingUpdateIndex !== -1) {
                  // Merge the updates for the existing entry
                  updatedUpdates[existingUpdateIndex] = {
                    ...updatedUpdates[existingUpdateIndex],
                    table_updated: data.table_updated,
                    update_time: data.update_time,
                  };
                } else {
                  // If no existing entry, add the new data
                  updatedUpdates = [
                    {
                      ...data,
                      id: `${data.event_id}-${Date.now()}-${data.table_updated}`,
                      table_updated: data.table_updated,
                      update_time: data.update_time,
                    },
                    ...updatedUpdates,
                  ];
                }
    
                // Keep only the last 50 updates
                return updatedUpdates.slice(0, 50);
              });
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('WebSocket connection closed');
        };

        return () => {
          ws.close();
        };
      }, []);

  const sportsList: string[] = ["Soccer", "Tennis", "Basketball", "Hockey", "Volleyball", "Handball", "American Football", "Mixed Martial Arts", "Baseball"]; 

  const handleClick = async (event_id:string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}?event_id=${event_id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
  
      // Check if the response status is OK (200-299)
      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        setSelectedData({
          event_id: event_id,
          data: data
        })
      }
    } catch (error) {
      console.error('Error sending event_id:', error);
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Live Odds Updates
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex border-b border-gray-200 mb-4">
              {sportsList.map((sports, index) => (
                <button
                  key={index}
                  className={`px-4 py-2 text-sm font-medium text-gray-700 ${
                    activeTab === (index + 1)
                      ? 'border-b-2 border-blue-500 text-blue-500'
                      : 'hover:text-blue-500'
                  }`}
                  onClick={() => setActiveTab(index + 1)}
                >
                  {sports}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            {updates.map(
              (update, index) =>
                activeTab === update.sport_id && (
                  <div 
                    key={index} 
                    className="bg-gray-50 rounded-lg hover:cursor-pointer"
                    onClick={() => handleClick(update.event_id)}
                  >
                    <div className='flex items-center justify-between p-3'>
                      <div className="flex-1 w-[70%]">
                        <div className="font-medium">
                          {update.home_team} vs {update.away_team}
                        </div>
                        <div className="text-sm text-gray-500">
                          Event ID: {update.event_id}
                        </div>
                      </div>
                      <div className="flex w-[30%] items-center gap-3">
                        <Badge variant='secondary'>{update.table_updated}</Badge>
                        <div className="text-sm text-gray-500">
                          {new Date(update.update_time).toISOString().slice(0, 19)}
                        </div>
                      </div>
                    </div>
                    {selectedData && selectedData.event_id === update.event_id && (
                    <div className="mt-6 p-6 bg-gradient-to-r from-blue-100 via-indigo-100 to-purple-100 rounded-lg shadow-xl w-full max-w-4xl mx-auto">
                      <h4 className="text-2xl font-semibold text-gray-800 mb-4">Detail Info</h4>
                      <div className="text-sm text-gray-700 space-y-6">
                        {
                          selectedData.data.data.map((item: any, index: any) => (
                            <div key={index} className="border-t border-gray-200 pt-4">
                              <h3 className="text-xl font-medium text-gray-800 mb-2">Period {index + 1}:</h3>
                              <ul className="list-disc pl-6 space-y-4">
                                <li>
                                  <h4 className="font-semibold text-gray-700 mb-2">Money Line:</h4>
                                  <table className='min-w-full border-collapse border border-gray-300 rounded-lg overflow-hidden'>
                                    <thead className='bg-blue-200'>
                                      <tr>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Home Odds</th>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Draw Odds</th>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Away Odds</th>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Max Bet</th>
                                      </tr>
                                    </thead>
                                    <tbody className='bg-white divide-y divide-gray-200'>
                                    {
                                      item.money_line.map((ml: any, index: any) => (
                                        <tr key={index}>
                                            <td className='py-2 px-4 text-sm text-gray-600'>{ml[0]}</td>
                                            <td className='py-2 px-4 text-sm text-gray-600'>{ml[1]}</td>
                                            <td className='py-2 px-4 text-sm text-gray-600'>{ml[2]}</td>
                                            <td className='py-2 px-4 text-sm text-gray-600'>{ml[3]}</td>
                                        </tr>
                                      ))
                                    }
                                    </tbody>
                                  </table>
                                </li>
                                <li>
                                  <h4 className="font-semibold text-gray-700 mb-2">Spread:</h4>
                                  <div className="space-y-2">
                                    {item.spread.map((sp: any, index: any) => (
                                      <p 
                                        key={index}
                                        className="flex justify-between items-center p-4 bg-gray-100 rounded-lg shadow hover:bg-gray-200 transition"
                                      >
                                        <span className="font-semibold text-blue-600">{update.home_team}</span>
                                        <span className="text-gray-700 text-base">{sp[0]}</span>
                                        <span className="text-gray-500 text-base">{sp[1]}</span>
                                        <span className="text-gray-700 text-lg">vs</span>
                                        <span className="text-gray-500 text-base">{sp[2]}</span>
                                        <span className="text-gray-700 text-base">{-1 * sp[0]}</span>
                                        <span className="font-semibold text-blue-600">{update.away_team}</span>
                                      </p>
                                    ))}
                                  </div>
                                  <table className='min-w-full mt-3 border-collapse border border-gray-300 rounded-lg overflow-hidden'>
                                    <thead className='bg-green-200'>
                                      <tr>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Handicap</th>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Home Odds</th>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Draw Odds</th>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Away Odds</th>
                                      </tr>
                                    </thead>
                                    <tbody className='bg-white divide-y divide-gray-200'>
                                    {
                                      item.spread.map((sp: any, index: any) => (
                                        <tr key={index}>
                                          <td className='py-2 px-4 text-sm text-gray-600'>{sp[0]}</td>
                                          <td className='py-2 px-4 text-sm text-gray-600'>{sp[1]}</td>
                                          <td className='py-2 px-4 text-sm text-gray-600'>{sp[2]}</td>
                                          <td className='py-2 px-4 text-sm text-gray-600'>{sp[3]}</td>
                                        </tr>
                                      ))
                                    }
                                    </tbody>
                                  </table>
                                </li>
                                <li>
                                  <h4 className="font-semibold text-gray-700 mb-2">Total:</h4>
                                  <table className='min-w-full border-collapse border border-gray-300 rounded-lg overflow-hidden'>
                                    <thead className='bg-purple-200'>
                                      <tr>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Points</th>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Over Odds</th>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Under Odds</th>
                                        <th className='py-2 px-4 text-left text-sm font-semibold text-gray-700'>Max Bet</th>
                                      </tr>
                                    </thead>
                                    <tbody className='bg-white divide-y divide-gray-200'>
                                    {
                                      item.total.map((tt: any, index: any) => (
                                        <tr key={index}>
                                          <td className='py-2 px-4 text-sm text-gray-600'>{tt[0]}</td>
                                          <td className='py-2 px-4 text-sm text-gray-600'>{tt[1]}</td>
                                          <td className='py-2 px-4 text-sm text-gray-600'>{tt[2]}</td>
                                          <td className='py-2 px-4 text-sm text-gray-600'>{tt[3]}</td>
                                        </tr>
                                      ))
                                    }
                                    </tbody>
                                  </table>
                                </li>
                              </ul>
                            </div>
                          ))
                        }
                      </div>
                    </div>
                  )}

                  </div>
                )
            )}  
            {updates.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                Waiting for updates...
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OddsDashboard;
