import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import MoneyLineTable from './ui/money_line';
import Spread from './ui/spread';
import Total from './ui/total';
import { PeriodTitles } from '../utils/period_titles';

// Define the shape of the odds update data
interface LiveOddsUpdate {
  sport_id: number;
  event_id: string;
  home_team: string;
  away_team: string;
  table_updated: string;
  update_time: string;
  id: string;
}

const LiveOddsDashboard = () => {
  const [updates, setUpdates] = useState<LiveOddsUpdate[]>([]);
  const [activeTab, setActiveTab] = useState<Number>(1);
  const [selectedData, setSelectedData] = useState<any | null>(null);
  const [clickedSpreadData, setClickedSpreadData] = useState<any | null>(null);
  const [clickedMoneyLineData, setClickedMoneyLineData] = useState<any | null>(null);
  const [clickedTotalData, setClickedTotalData] = useState<any | null>(null);

  useEffect(() => {
    const ws = new WebSocket(process.env.NEXT_APP_WS_URL);
    
    const handleMessage = (event: MessageEvent) => {
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
    }

    const handleOpen = () => {
      console.log('Connected to WebSocket');
    };

    const handleError = (error: Event) => {
      console.error('WebSocket error:', error);
    };
  
    const handleClose = () => {
      console.log('WebSocket connection closed');
    };

    ws.addEventListener('open', handleOpen);
    ws.addEventListener('message', handleMessage);
    ws.addEventListener('error', handleError);
    ws.addEventListener('close', handleClose);

    return () => {
      ws.removeEventListener('open', handleOpen);
      ws.removeEventListener('message', handleMessage);
      ws.removeEventListener('error', handleError);
      ws.removeEventListener('close', handleClose);
      ws.close();
    };
  }, []);

  const memoizedSelectedData = useMemo(() => {
    return selectedData;
  }, [selectedData?.event_id]);
  
  const memoizedClickedSpreadData = useMemo(() => {
    return clickedSpreadData;
  }, [clickedSpreadData?.period_id, clickedSpreadData?.hdp]);

  const memoizedClickedMoneyLineData = useMemo(() => {
    return clickedMoneyLineData;
  }, [clickedMoneyLineData?.period_id]);

  const memoizedClickedTotalData = useMemo(() => {
    return clickedTotalData;
  }, [clickedTotalData?.period_id, clickedTotalData?.points]);

  const sportsList: string[] = ["Soccer", "Tennis", "Basketball", "Hockey", "Volleyball", "Handball", "American Football", "Mixed Martial Arts", "Baseball"]; 

  const handleGetDetailInfo = async (event_id:string, event: React.MouseEvent) => {
    event.stopPropagation();

    try {
      const response = await fetch(`${process.env.NEXT_APP_API_URL}?event_id=${event_id}`, {
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

  const handleGetMoneyLineChart = async (period_id: string, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();

    try {
      const response = await fetch(
        `${process.env.NEXT_APP_CHART_API_URL}?period_id=${period_id}&type=money_line`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        setClickedMoneyLineData({
          period_id: period_id,
          data: data,
        });
      }
    } catch (error) {
      console.error('Error getting chart info: ', error);
    }
  };

  const handleGetSpreadChart = async(period_id: string, hdp: number, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();

    try {
      const response = await fetch(`${process.env.NEXT_APP_CHART_API_URL}?period_id=${period_id}&hdp=${hdp}&type=spread`, {
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
        setClickedSpreadData({
          period_id: period_id,
          hdp: hdp,
          data: data
        })
      }
    }
    catch (error) {
      console.error('Error getting chart info: ', error)
    }
  };

  const handleGetTotalChart = async (period_id: string, points: number, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();

    try {
      const response = await fetch(
        `${process.env.NEXT_APP_CHART_API_URL}?period_id=${period_id}&points=${points}&type=total`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        setClickedTotalData({
          period_id: period_id,
          points: points,
          data: data,
        });
      }
    } catch (error) {
      console.error('Error getting chart info: ', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <Card className="mb-6 mt-5">
        <CardContent variant='child'>
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
              (update) =>
                activeTab === update.sport_id && (
                  <div 
                    key={update.event_id} 
                    className="bg-gray-50 rounded-lg hover:cursor-pointer"
                    onClick={(event) => handleGetDetailInfo(update.event_id, event)}
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
                    {memoizedSelectedData && memoizedSelectedData.event_id === update.event_id && (
                    <div className="mt-6 p-6 bg-gradient-to-r from-blue-100 via-indigo-100 to-purple-100 rounded-lg shadow-xl w-full max-w-4xl mx-auto">
                      <h4 className="text-2xl font-semibold text-gray-800 mb-4">Detail Info</h4>
                      <div className="text-sm text-gray-700 space-y-6">
                        {
                          memoizedSelectedData?.data?.data.length > 0 &&  memoizedSelectedData.data.data.some((item: any) => 
                            item.money_line.length || item.spread.length || item.total.length
                          ) ? (
                            memoizedSelectedData.data.data.map((item: any, index: any) => (
                              <div key={index} className="border-t border-gray-200 pt-4">
                                {(item.money_line.length !== 0 || item.spread.length !== 0 || item.total.length !== 0) && <ul className="list-disc pl-6 space-y-4">
                                  <h3 className="text-xl font-medium text-gray-800 mb-2">{PeriodTitles(index)}:</h3>
                                  {item.money_line.length !== 0 && <li><MoneyLineTable data={item.money_line} update={update} search={true} period_id={item.period_id} handleGetChart={handleGetMoneyLineChart} memoizedClickedData={memoizedClickedMoneyLineData} /></li>}
                                  {item.spread.length !== 0 && <li><Spread item={item} update={update} handleGetChart={handleGetSpreadChart} memoizedClickedData={memoizedClickedSpreadData} /></li>}
                                  {item.total.length !== 0 && <li><Total item={item.total} period_id={item.period_id} handleGetChart={handleGetTotalChart} memoizedClickedData={memoizedClickedTotalData} /></li>}
                                </ul>}
                              </div>
                            ))
                          ) : (
                            <div className="text-gray-500 text-sm text-center py-4">
                              No data available for this event.
                            </div>
                          ) 
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

  export default LiveOddsDashboard;