import * as React from 'react';

const Total = ({ item, search }: { item: any[], search?: boolean }) => {
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
              <tr key={tIndex}>
                <td className="py-2 px-4 text-sm text-gray-600">{tt[0]}</td>
                <td className="py-2 px-4 text-sm text-gray-600">{tt[1]}</td>
                <td className="py-2 px-4 text-sm text-gray-600">{tt[2]}</td>
                <td className="py-2 px-4 text-sm text-gray-600">{tt[3]}</td>
                { search ? <td className="py-2 px-4 text-sm text-gray-600">{new Date(tt[4]).toISOString().slice(0, 19).replace('T', ' ')}</td>: '' }
              </tr>
            ))}
          </tbody>
        </table> : 
        <div className="text-gray-500">No data available</div> 
      } 
    </div>
  );
};

export default Total;
