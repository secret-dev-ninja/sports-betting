import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent } from './ui/card';
import SearchableDropdown from './ui/search_dropdown';
import SearchableInput from './ui/search_input';
import MoneyLine from './ui/money_line';
import Spread from './ui/spread';
import Total from './ui/total';
import { PeriodTitles } from '../utils/period_titles';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaSync } from 'react-icons/fa';

interface DropdownOption {
  value: string;
  label: string;
}

interface Update {
  event_id: string;
  home_team: string;
  away_team: string;
  league_name: string;
  starts: string;
  updated_at: string;
}

const SearchOdds = () => {
  const [sportsOpts, setSportsOpts] = useState<DropdownOption[]>([]);
  const [sports, setSports] = useState<string>();
  const [leagueOpts, setLeaguesOps] = useState<DropdownOption[]>([]);
  const [league, setLeague] = useState<string>();
  const [teamOpts, setTeamOpts] = useState<DropdownOption[]>([]);
  const [updates, setUpdates] = useState<Update[]>([]);
  const [selectedData, setSelectedData] = useState<any | null>(null);
  const [clickedSpreadData, setClickedSpreadData] = useState<any | null>(null);
  const [clickedMoneyLineData, setClickedMoneyLineData] = useState<any | null>(null);
  const [clickedTotalData, setClickedTotalData] = useState<any | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const fetchOpts = async (sport_name?: string, league_name?: string) => {
    try {
      const url = sport_name && league_name
        ? `${process.env.NEXT_APP_OPTS_API_URL}?sport_name=${sport_name}&league_name=${league_name}`
        : sport_name
        ? `${process.env.NEXT_APP_OPTS_API_URL}?sport_name=${sport_name}`
        : `${process.env.NEXT_APP_OPTS_API_URL}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        if (sport_name && league_name) {
          setTeamOpts(data);
        }
        else if (sport_name) {
          setLeaguesOps(data.leagues);
          setTeamOpts(data.teams);
        }
        else {
          setSportsOpts(data);
        }
      }
    } catch (e) {
      console.log(e);
    }
  };

  useEffect(() => {
    if (!sportsOpts.length) {
      fetchOpts();
    }
  }, [sportsOpts]);

  useEffect(() => {
    if (updates.length > 0) {
      handleGetDetailInfo(updates[0].event_id, {
        stopPropagation: () => {},
        preventDefault: () => {},
      } as React.MouseEvent);
    }
  }, [updates]);

  const handleDropdownSportsSelect = (value: string) => {
    setSports(value);
    fetchOpts(value);
    setUpdates([]);
    handlePageChange(1);
    setLeague('');
  };

  const handleDropdownLeagueSelect = async (value: DropdownOption) => {
    setLeague(value.value); 
    fetchOpts(sports, value.value);
    console.log(sports, value.value);
    handlePageChange(1);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_APP_EVENT_API_URL}?sport_id=${sports}&league_id=${value.value}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        console.log('data:', data);
        setUpdates(data);
      }
    } catch (e) {
      console.log(e);
    }
  };

  const handleDropdownTeamSelect = async (value: DropdownOption) => {
    handlePageChange(1);

    const url = league ? 
                `${process.env.NEXT_APP_EVENT_API_URL}?sport_name=${sports}&league_name=${league}&team_name=${value.value}` : 
                `${process.env.NEXT_APP_EVENT_API_URL}?sport_name=${sports}&team_name=${value.value}`;
    try {
      const response = await fetch(
        url,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        }
      );
      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        console.log('data:', data);
        setUpdates(data);
      }
    } catch (e) {
      console.log(e);
    }
  };

  const handleGetDetailInfo = async (event_id: string, event: React.MouseEvent, reload: boolean = false) => {
    event.stopPropagation();

    if (!reload && selectedData && selectedData.event_id === event_id) {
      setSelectedData(null);
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_APP_API_URL}?event_id=${event_id}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        setSelectedData({
          event_id: event_id,
          data: data,
        });
        reload && toast.success('Data reloaded successfully!');
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

  const handleGetSpreadChart = async (period_id: string, hdp: number, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();

    try {
      const response = await fetch(
        `${process.env.NEXT_APP_CHART_API_URL}?period_id=${period_id}&hdp=${hdp}&type=spread`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        setClickedSpreadData({
          period_id: period_id,
          hdp: hdp,
          data: data,
        });
      }
    } catch (error) {
      console.error('Error getting chart info: ', error);
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

  // Paginate updates
  const paginatedUpdates = useMemo(() => {
    const startIdx = (currentPage - 1) * pageSize;
    return updates.slice(startIdx, startIdx + pageSize);
  }, [updates, currentPage]);

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  // Generate page numbers for pagination
  const totalPages = Math.ceil(updates.length / pageSize);
  const pageNumbers = Array.from({ length: totalPages }, (_, index) => index + 1);

  return (
    <div className="max-w-6xl mx-auto">
      <ToastContainer />
      <Card className="mb-6 mt-5">
        <CardContent variant="child">
          <div className="space-y-4">
            <div className="flex items-center justify-start mb-4 gap-4">
              <SearchableDropdown
                options={sportsOpts}
                placeholder="Select Sports option"
                onSelect={handleDropdownSportsSelect}
                viewCount={10}
              />
              <SearchableInput
                options={leagueOpts}
                placeholder="Select League option"
                onSelect={handleDropdownLeagueSelect}
                viewCount={10}
              />
              <SearchableInput
                options={teamOpts}
                placeholder="Select Team option"
                onSelect={handleDropdownTeamSelect}
                viewCount={10}
              />
            </div>

            <div className="rounded-lg">
              {paginatedUpdates.map((update) => (
                <div
                  key={update.event_id}
                  className="bg-gray-50 mt-3 rounded-lg hover:cursor-pointer"
                  onClick={(event) => handleGetDetailInfo(update.event_id, event)}
                >
                  <div className="flex items-center justify-between p-3">
                    <div className="flex-1">
                      <div className="font-medium">
                        {update.home_team} vs {update.away_team}
                      </div>
                      <div className="text-sm text-gray-500">
                        Event ID: {update.event_id}
                      </div>
                    </div>
                    <div className="flex-1 text-sm">
                      {update.league_name}
                    </div>
                    <div className="flex-1">
                      <div className="font-sm  text-gray-600">
                        Match Date:
                      </div>
                      <div className="text-sm">
                        {update.starts.replace('T', ' ')}
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="font-sm text-gray-600">
                        Last updated log time:
                      </div>
                      <div className="text-sm">
                        {update.updated_at.replace('T', ' ')}
                      </div>
                    </div>
                  </div>

                  {memoizedSelectedData && memoizedSelectedData.event_id === update.event_id && (
                    <div className="mt-6 p-6 bg-gradient-to-r from-blue-100 via-indigo-100 to-purple-100 rounded-lg shadow-xl w-full max-w-4xl mx-auto">
                      <div className="flex items-center justify-between">
                        <h4 className="text-2xl font-semibold text-gray-800 mb-4">Detailed Information</h4>
                        <button
                          onClick={(event) => handleGetDetailInfo(update.event_id, event, true)}
                          className="text-blue-500 hover:text-blue-700"
                        >
                          <FaSync className="inline-block text-xl text-black" />
                        </button>
                      </div>
                      <div className="text-sm text-gray-700 space-y-6">
                        {memoizedSelectedData?.data?.data.length > 0 &&
                        memoizedSelectedData.data.data.some(
                          (item: any) =>
                            item.money_line.length || item.spread.length || item.total.length
                        ) ? (
                          memoizedSelectedData.data.data.map((item: any, index: any) => (
                            <div key={index} className="border-t border-gray-200">
                              {(item.money_line.length !== 0 || item.spread.length !== 0 || item.total.length !== 0) && <ul className="list-disc pl-6 pt-4 space-y-4">
                                <h3 className="text-xl font-medium text-gray-800 mb-2">
                                  {
                                    PeriodTitles(index)
                                  }
                                </h3>
                                {item.money_line.length !== 0 && <li><MoneyLine data={item.money_line} period_id={item.period_id} update={update} search={true} handleGetChart={handleGetMoneyLineChart} memoizedClickedData={memoizedClickedMoneyLineData} /></li>}
                                {item.spread.length !== 0 && <li><Spread item={item} update={update} handleGetChart={handleGetSpreadChart} memoizedClickedData={memoizedClickedSpreadData} search={true} /></li>}
                                {item.total.length !== 0 && <li><Total item={item.total} search={true} period_id={item.period_id} handleGetChart={handleGetTotalChart} memoizedClickedData={memoizedClickedTotalData} /></li>}
                              </ul>}
                            </div>
                          ))
                        ) : (
                          <div className="text-gray-500">No data available</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Pagination Controls */}
            <div className="flex justify-center space-x-4 mt-6">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:bg-gray-300"
              >
                Previous
              </button>
              {pageNumbers.map((pageNum) => (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`px-4 py-2 rounded-full ${currentPage === pageNum ? 'bg-blue-500 text-white' : 'bg-white text-blue-500'}`}
                >
                  {pageNum}
                </button>
              ))}
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:bg-gray-300"
              >
                Next
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SearchOdds;
