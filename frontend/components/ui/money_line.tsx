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
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">{update.home_team} odds</th>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">{update.home_team} VF</th>
                {data[0]['draw'] ? <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Draw</th> : ''}
                {data[0]['draw'] ? <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Draw VF</th> : ''}
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">{update.away_team} odds</th>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">{update.away_team} VF</th>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Vig</th>
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Max Bet</th>
                { search ? <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Timestamp</th>: '' }
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((ml, mIndex) => (
                <React.Fragment key={mIndex}>
                  <tr 
                    className="bg-white hover:bg-gray-100 transition cursor-pointer" 
                    onClick={(event) => handleGetChart(period_id, event)}
                  >
                    <td className="py-2 px-4 text-sm text-gray-600">{ml['home']}</td>
                    <td className="py-2 px-4 text-sm text-gray-600">{ml['home_vf']}</td>
                    {ml['draw'] ? <td className="py-2 px-4 text-sm text-gray-600">{ml['draw']}</td> : ''}
                    {ml['draw'] ? <td className="py-2 px-4 text-sm text-gray-600">{ml['draw_vf']}</td> : ''}
                    <td className="py-2 px-4 text-sm text-gray-600">{ml['away']}</td>
                    <td className="py-2 px-4 text-sm text-gray-600">{ml['away_vf']}</td>
                    <td className="py-2 px-4 text-sm text-gray-600">{ml['vig']}%</td>
                    <td className="py-2 px-4 text-sm text-gray-600">{ml['max_bet']}</td>
                    { search ? <td className="py-2 px-4 text-sm text-gray-600">{ml['time'].replace('T', ' ')}</td>: '' }
                  </tr>
                  {
                    memoizedClickedData &&
                    memoizedClickedData.period_id === period_id && (
                      <tr>
                        <td colSpan={12}>
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
  