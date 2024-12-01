import * as React from "react"
import ChartComponent from "./chart";

const MoneyLine = ({ data, period_id, update, search, handleGetChart, memoizedClickedData }: { data: any[], period_id: string, update: any, search?: boolean, handleGetChart: (period_id: string, event: React.MouseEvent<HTMLTableRowElement>) => void, memoizedClickedData: any }) => {
    return (
      <>
        <h4 className="font-semibold text-gray-700 mb-2">Money Line:</h4>
        {
          data.length ?
          <table className="min-w-full border-collapse border border-gray-300 rounded-lg overflow-hidden">
          <thead className="bg-blue-200">
              <tr>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Home Team</th>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Home Odds</th>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Draw Odds</th>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Away Team</th>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Away Odds</th>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Max Bet</th>
                { search ? <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Timestamp</th>: '' }
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((ml, mIndex) => (
                <React.Fragment key={mIndex}>
                  <tr className="bg-white hover:bg-gray-100 transition cursor-pointer" onClick={(event) => handleGetChart(period_id, event)}>
                    <td className="py-2 px-4 text-sm text-gray-600">{update.home_team}</td>
                    <td className="py-2 px-4 text-sm text-gray-600">{ml[0]}</td>
                    <td className="py-2 px-4 text-sm text-gray-600">{ml[1]}</td>
                    <td className="py-2 px-4 text-sm text-gray-600">{update.away_team}</td>
                    <td className="py-2 px-4 text-sm text-gray-600">{ml[2]}</td>
                    <td className="py-2 px-4 text-sm text-gray-600">{ml[3]}</td>
                    { search ? <td className="py-2 px-4 text-sm text-gray-600">{ml[4].replace('T', ' ')}</td>: '' }
                  </tr>
                  {
                    memoizedClickedData &&
                    memoizedClickedData.period_id === period_id && (
                      <tr>
                        <td colSpan={8}>
                          <ChartComponent data={memoizedClickedData.data.data} />
                        </td>
                      </tr>
                    )
                }
                </React.Fragment>
              ))}
            </tbody>
          </table> : 
          <div className="text-gray-500">No data available</div>
        }
      </>
    );
  };
  

export default MoneyLine;
  