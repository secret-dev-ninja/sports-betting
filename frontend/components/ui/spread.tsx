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
}

const Spread: React.FC<SpreadProps> = ({ item, update, handleGetChart, memoizedClickedData }) => {
  return (
    <div>
      <h4 className="font-semibold text-gray-700 mb-2">Spread:</h4>
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
      </table>
      {
      item.spread.map((sp, sIndex) => (
        <div key={sIndex}>
          <p
            className="flex justify-between items-center p-1 border-b-2 bg-white rounded-sm shadow hover:bg-gray-200 transition"
            onClick={(event) => handleGetChart(item.period_id[0], sp[0], event)} // sp[0] is a string here
          >
            <span className="py-2 px-4 text-sm text-gray-600">{update.home_team}</span>
            <span className="py-2 px-4 text-sm text-gray-600">{sp[0]}</span>
            <span className="py-2 px-4 text-sm text-gray-600">{sp[1]}</span>
            <span className="py-2 px-4 text-sm text-gray-600">{update.away_team}</span>
            <span className="py-2 px-4 text-sm text-gray-600">{-1 * sp[0]}</span>
            <span className="py-2 px-4 text-sm text-gray-600">{sp[2]}</span>
            <span className="py-2 px-4 text-sm text-gray-600">{sp[3]}</span>
          </p>
          {memoizedClickedData && memoizedClickedData.period_id === item.period_id[0] && memoizedClickedData.hdp === sp[0] && (
            <ChartComponent data={memoizedClickedData.data.data} />
          )}
        </div>
        ))
      }
    </div>
  );
};

export default Spread;
