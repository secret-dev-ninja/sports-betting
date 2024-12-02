import * as React from 'react';
import ChartComponent from "./chart";

const Total = ({ item, search, period_id, handleGetChart, memoizedClickedData }: { item: any[], search?: boolean, period_id: string, handleGetChart: (period_id: string, points: number, event: React.MouseEvent) => void, memoizedClickedData: any }) => {
  return (
    <div>
      <h4 className="font-semibold text-gray-700 mb-2">Total:</h4>
      {
        item.length ? 
        <table className="min-w-full border-collapse border border-gray-300 rounded-lg overflow-hidden">
          <thead className="bg-purple-200">
            <tr>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Points</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Over Odds</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Under Odds</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Max Bet</th>
              {search && (
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">
                  Timestamp
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {item.map((tt, tIndex) => (
              <React.Fragment key={tIndex}>
                <tr className="bg-white hover:bg-gray-100 transition cursor-pointer" onClick={(event) => handleGetChart(period_id, tt[0], event)}>
                  <td className="py-2 px-4 text-sm text-gray-600">{tt[0]}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{tt[1]}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{tt[2]}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{tt[3]}</td>
                  { search ? <td className="py-2 px-4 text-sm text-gray-600">{tt[4].replace('T', ' ')}</td>: '' }
                </tr>
                {
                    memoizedClickedData &&
                    memoizedClickedData.period_id === period_id && memoizedClickedData.points === tt[0] && (
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
    </div>
  );
};

export default Total;
