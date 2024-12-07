import * as React from 'react';
import ChartComponent from './chart';

interface SpreadItem {
  spread: { handicap: number, home_odds: string, home_vf: string, away_odds: string, away_vf: string, vig: string, max_bet: string, time: string }[];
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
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">{ update.home_team } Handicap</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Home Odds</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Home VF</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">{ update.away_team } Handicap</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Away Odds</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Away VF</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Vig</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Limit</th>
              {search && (
                <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">
                  Timestamp
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {item.spread.map((sp, sIndex) => (
              <React.Fragment key={sIndex}>
                <tr
                  className="bg-white hover:bg-gray-100 transition cursor-pointer"
                  onClick={(event) => handleGetChart(item.period_id[0], sp['handicap'], event)}
                >
                  <td className="py-2 px-4 text-sm text-gray-600">{sp['handicap']}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp['home_odds']}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp['home_vf']}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{-1 * sp['handicap']}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp['away_odds']}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp['away_vf']}</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp['vig']} %</td>
                  <td className="py-2 px-4 text-sm text-gray-600">{sp['max_bet']}</td>
                  {search && (
                    <td className="py-2 px-4 text-sm text-gray-600">
                      {sp['time'].replace('T', ' ')}
                    </td>
                  )}
                </tr>
                {
                  memoizedClickedData &&
                  memoizedClickedData.period_id === item.period_id[0] &&
                  memoizedClickedData.hdp === sp['handicap'] && (
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
    </div>
  );
};

export default Spread;
