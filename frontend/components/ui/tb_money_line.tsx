import * as React from "react"

const MoneyLineTable = ({ data }: { data: any[] }) => {
    return (
      <>
        <h4 className="font-semibold text-gray-700 mb-2">Money Line:</h4>
        <table className="min-w-full border-collapse border border-gray-300 rounded-lg overflow-hidden">
          <thead className="bg-blue-200">
            <tr>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Home Odds</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Draw Odds</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Away Odds</th>
              <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Max Bet</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((ml, mIndex) => (
              <tr key={mIndex}>
                <td className="py-2 px-4 text-sm text-gray-600">{ml[0]}</td>
                <td className="py-2 px-4 text-sm text-gray-600">{ml[1]}</td>
                <td className="py-2 px-4 text-sm text-gray-600">{ml[2]}</td>
                <td className="py-2 px-4 text-sm text-gray-600">{ml[3]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </>
    );
  };
  

export default MoneyLineTable;
  