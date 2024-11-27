import React from 'react';
import { Card, CardContent } from './ui/card';
import SearchableDropdown from './ui/dropdown';

const SearchOdds = () => {
  const sportsOpts = [
    { value: 'opt1', label: 'Option 1' },
    { value: 'opt2', label: 'Option 2' },
    { value: 'opt3', label: 'Option 3' },
    { value: 'opt4', label: 'Option 4' },
    { value: 'opt5', label: 'Option 5' },
    { value: 'opt6', label: 'Option 6' },
    { value: 'opt7', label: 'Option 7' },
    { value: 'opt8', label: 'Option 8' },
  ];

  const leagueOpts = [
    { value: 'choiceA', label: 'Choice A' },
    { value: 'choiceB', label: 'Choice B' },
    { value: 'choiceC', label: 'Choice C' },
    { value: 'choiceD', label: 'Choice D' },
    { value: 'choiceE', label: 'Choice E' },
    { value: 'choiceF', label: 'Choice F' },
    { value: 'choiceG', label: 'Choice G' },
    { value: 'choiceH', label: 'Choice H' },
  ];

  const handleDropdownSportsSelect = (value: string) => {
    console.log('Dropdown sports selected value:', value);
  };

  const handleDropdownLeagueSelect = (value: string) => {
    console.log('Dropdown league selected value:', value);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <Card className="mb-6 mt-5">
        <CardContent variant="child">
          <div className="space-y-4">
            <div className="flex items-center justify-start mb-4 gap-4">
              {/* Modern Dropdown 1 */}
              <SearchableDropdown
                options={sportsOpts}
                placeholder="Select Sports option"
                onSelect={handleDropdownSportsSelect}
                viewCount={10}
              />

              {/* Modern Dropdown 2 */}
              <SearchableDropdown
                options={leagueOpts}
                placeholder="Select League option"
                onSelect={handleDropdownLeagueSelect}
                viewCount={5}
              />
            </div>

            {/* Additional Content */}
            <div className="bg-gray-50 rounded-lg hover:cursor-pointer">
              {/* Content goes here */}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SearchOdds;
