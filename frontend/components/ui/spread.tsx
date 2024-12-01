import * as React from 'react';
import ChartComponent from './chart';

interface SpreadItem {
  spread: [number, string, string, string, string][];
  period_id: string[];
}

interface SpreadProps {
  item: SpreadItem;
  update: { home_team: string; away_team: string };
  handleGetChart: (periodId: string, hdp: number, event: React.MouseEvent) => void;
  memoizedClickedData: { period_id: string; hdp: number; data: { data: any } } | null;
  search?: boolean;
}

const Spread: React.FC<SpreadProps> = ({ item, update, handleGetChart, memoizedClickedData, search }) => {
  return (
    <div>
      <h4 className="font-semibold text-gray-700 mb-2">Spread:</h4>
      { 
        item.spread.length ? 
        <table className="min-w-full mt-3 border-collapse border border-gray-300 rounded-lg overflow-hidden">
          <thead className="bg-green-200">
            <tr>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Home Team</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Home Handicap</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Home Odds</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Away Team</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Away Handicap</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Away Odds</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Limit</th>
              {search && (
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">
                  Timestamp
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {item.spread.map((sp, sIndex) => (
              <React.Fragment key={sIndex}>
                <tr
                  className="bg-white hover:bg-gray-100 transition cursor-pointer"
                  onClick={(event) => handleGetChart(item.period_id[0], sp[0], event)}
                >
                  <td className="py-2 px-4 text-sm text-gray-600">{update.home_team}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp[0]}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp[1]}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{update.away_team}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{-1 * sp[0]}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp[2]}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp[3]}</td>
                  {search && (
                    <td className="py-2 px-4 text-sm text-gray-600">
                      {sp[4].replace('T', ' ')}
                    </td>
                  )}
                </tr>
                {
                  memoizedClickedData &&
                  memoizedClickedData.period_id === item.period_id[0] &&
                  memoizedClickedData.hdp === sp[0] && (
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

export default Spread;
