import * as React from 'react';
import ChartComponent from './chart';

interface SpreadItem {
  spread: [number, string, string, string][]; // Each 'spread' element is an array of strings
  period_id: string[];
}

interface SpreadProps {
  item: SpreadItem;
  update: { home_team: string; away_team: string };
  handleGetChart: (periodId: string, hdp: number, event: React.MouseEvent) => void;
  memoizedClickedData: { period_id: string; hdp: number; data: { data: any } } | null;
  isVisibleChild?: boolean;
}

const Spread: React.FC<SpreadProps> = ({ item, update, handleGetChart, memoizedClickedData, isVisibleChild }) => {
  return (
    <div>
      <h4 className="font-semibold text-gray-700 mb-2">Spread:</h4>
      <div className="space-y-2">
        {isVisibleChild && item.spread.map((sp, sIndex) => (
          <div key={sIndex}>
            <p
              className="flex justify-center items-center p-4 mb-3 gap-2 bg-gray-100 rounded-lg shadow hover:bg-gray-200 transition"
              onClick={(event) => handleGetChart(item.period_id[0], sp[0], event)} // sp[0] is a string here
            >
              <span className="font-semibold text-blue-600">{update.home_team}</span>
              <span className="text-gray-700 text-base">{sp[0]}</span>
              <span className="text-gray-600 text-base"> @ </span>
              <span className="text-gray-500 text-base">{sp[1]}</span>
              <span className="text-gray-700 text-lg">vs</span>
              <span className="text-gray-500 text-base">{update.away_team}</span>
              <span className="text-gray-500 text-base"> @ </span>
              <span className="text-gray-700 text-base">{sp[2]}</span>
              <span className="font-semibold text-blue-600">{sp[3]}</span>
            </p>
            {memoizedClickedData && memoizedClickedData.period_id === item.period_id[0] && memoizedClickedData.hdp === sp[0] && (
              <ChartComponent data={memoizedClickedData.data.data} />
            )}
          </div>
        ))}
      </div>
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
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {item.spread.map((sp, spIndex) => (
            <tr key={spIndex}>
              <td className="py-2 px-4 text-sm text-gray-600">{update.home_team}</td>
              <td className="py-2 px-4 text-sm text-gray-600">{sp[0]}</td>
              <td className="py-2 px-4 text-sm text-gray-600">{sp[1]}</td>
              <td className="py-2 px-4 text-sm text-gray-600">{update.away_team}</td>
              <td className="py-2 px-4 text-sm text-gray-600">{-1 * sp[0]}</td>
              <td className="py-2 px-4 text-sm text-gray-600">{sp[2]}</td>
              <td className="py-2 px-4 text-sm text-gray-600">{sp[3]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Spread;
