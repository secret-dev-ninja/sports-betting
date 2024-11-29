import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent } from './ui/card';
import SearchableDropdown from './ui/dropdown';
import MoneyLineTable from './ui/tb_money_line';
import Spread from './ui/spread';
import Total from './ui/total';

interface DropdownOption {
  value: number, 
  label: string
};

interface Update {
  event_id: string;
  home_team: string;
  away_team: string;
  updated_at: string;
}

const SearchOdds = () => {
  const [sportsOpts, setSportsOpts] = useState<DropdownOption[]>([]);
  const [sports, setSports] = useState<number>();
  const [leagueOpts, setLeaguesOps] = useState<DropdownOption[]>([]);
  const [league, setLeague] = useState<number>();
  const [teamOpts, setTeamOpts] = useState<DropdownOption[]>([]);
  const [updates, setUpdates] = useState<Update[]>([]);
  const [selectedData, setSelectedData] = useState<any | null>(null);
  const [clickedData, setClickedData] = useState<any | null>(null);

  const fetchOpts = async (sport_id?: number, league_id?: number) => {
    try {
      const url = sport_id && league_id ? `${process.env.NEXT_APP_OPTS_API_URL}?sport_id=${sport_id}&league_id=${league_id}` : 
                  (sport_id ? `${process.env.NEXT_APP_OPTS_API_URL}?sport_id=${sport_id}` : `${process.env.NEXT_APP_OPTS_API_URL}`);

      const response = await fetch(url, {
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
        sport_id && league_id ? setTeamOpts(data) : (sport_id ? setLeaguesOps(data) : setSportsOpts(data));
      }
    }
    catch(e) {
      console.log(e);
    }
  }

  useEffect(() => {
    fetchOpts();
  }, []);

  const handleDropdownSportsSelect = (value: number) => {
    setSports(value);
    fetchOpts(value);
    setUpdates([]);
  };

  const handleDropdownLeagueSelect = async (value: number) => {
    setLeague(value);
    fetchOpts(sports, value);
    try {
      const response = await fetch(`${process.env.NEXT_APP_EVENT_API_URL}?sport_id=${sports}&league_id=${value}`, {
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
        console.log('data:', data);
        setUpdates(data);
      }
    }
    catch(e) {
      console.log(e);
    }
  };

  const handleDropdownTeamSelect = async (team: number) => {
    try {
      const response = await fetch(`${process.env.NEXT_APP_EVENT_API_URL}?sport_id=${sports}&league_id=${league}&team_name=${team}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        console.log('data:', data);
        setUpdates(data);
      }
    }
    catch(e) {
      console.log(e);
    }
  };

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

  const handleGetChart = async(period_id: string, hdp: number, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();

    try {
      const response = await fetch(`${process.env.NEXT_APP_CHART_API_URL}?period_id=${period_id}&hdp=${hdp}`, {
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
        setClickedData({
          period_id: period_id,
          hdp: hdp,
          data: data
        })
      }
    }
    catch (error) {
      console.error('Error getting chart info: ', error)
    }
  }

  const memoizedSelectedData = useMemo(() => {
    return selectedData;
  }, [selectedData?.event_id]);
  
  const memoizedClickedData = useMemo(() => {
    return clickedData;
  }, [clickedData?.period_id, clickedData?.hdp]);

  return (
    <div className="max-w-6xl mx-auto">
      <Card className="mb-6 mt-5">
        <CardContent variant="child">
          <div className="space-y-4">
            <div className="flex items-center justify-start mb-4 gap-4">
              {/* Modern Dropdown Sports */}
              <SearchableDropdown
                options={sportsOpts}
                placeholder="Select Sports option"
                onSelect={handleDropdownSportsSelect}
                viewCount={10}
              />

              {/* Modern Dropdown Leagues */}
              <SearchableDropdown
                options={leagueOpts}
                placeholder="Select League option"
                onSelect={handleDropdownLeagueSelect}
                viewCount={10}
              />

              <SearchableDropdown
                options={teamOpts}
                placeholder="Select Team option"
                onSelect={handleDropdownTeamSelect}
                viewCount={10}
              />
            </div>

            {/* Additional Content */}
            <div className="rounded-lg hover:cursor-pointer">
            {
              updates.map((update) => (
                <div 
                    key={update.event_id} 
                    className="bg-gray-50 mt-3 rounded-lg hover:cursor-pointer"
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
                        <div className="text-sm text-gray-500">
                          {new Date(update.updated_at).toISOString().slice(0, 19)}
                        </div>
                      </div>
                    </div>
                    {memoizedSelectedData && memoizedSelectedData.event_id === update.event_id && (
                    <div className="mt-6 p-6 bg-gradient-to-r from-blue-100 via-indigo-100 to-purple-100 rounded-lg shadow-xl w-full max-w-4xl mx-auto">
                      <h4 className="text-2xl font-semibold text-gray-800 mb-4">Detailed Information</h4>
                      <div className="text-sm text-gray-700 space-y-6">
                        { memoizedSelectedData?.data?.data.length > 0 &&  memoizedSelectedData.data.data.some((item: any) => 
                            item.money_line.length || item.spread.length || item.total.length
                          ) ? (
                            memoizedSelectedData.data.data.map((item: any, index: any) => (
                              <div key={index} className="border-t border-gray-200">
                                {(item.money_line.length !== 0 || item.spread.length !== 0 || item.total.length !== 0) && <ul className="list-disc pl-6 pt-4 space-y-4">
                                  <h3 className="text-xl font-medium text-gray-800 mb-2">
                                    {
                                      index === 0 ? 'Full Game' : index === 1 ? '1st Half' : `Period ${index + 1}` 
                                    }:
                                  </h3>
                                  {item.money_line.length !== 0 && <li><MoneyLineTable data={item.money_line} search={true} /></li>}
                                  {item.spread.length !== 0 && <li><Spread item={item} update={update} handleGetChart={handleGetChart} memoizedClickedData={memoizedClickedData} search={true} /></li>}
                                  {item.total.length !== 0 && <li><Total item={item.total} search={true} /></li>}
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
              ))
            }
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SearchOdds;
