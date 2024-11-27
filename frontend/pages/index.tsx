import React, { useState } from 'react';
import SearchOdds from '@/components/search_odds';
import LiveOddsDashboard from '@/components/live_odds';
import { Bell } from "lucide-react";
import dotenv from "dotenv";

dotenv.config();

const OddsDashboard = () => {
  const [navbar, setNavbar] = useState<String>('live');

  return (
    <>
      <div className="p-4 max-w-4xl mx-auto">
        <nav className="bg-black shadow-md rounded-s">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-start justify-between">
              <div className="text-white font-bold text-xl">
                <div className='flex items-center gap-2 hover:cursor-pointer'>
                  <Bell className="h-5 w-5" />
                  Live Odds Updates
                </div>
              </div>
              <div className="flex-1 flex justify-start ml-10 space-x-6">
                <div className="font-semibold text-white mt-[0.7] hover:text-gray-300 hover:cursor-pointer" onClick={() => setNavbar('live')}>
                  Live
                </div>
                <div className="font-semibold text-white mt-[0.7] hover:text-gray-300 hover:cursor-pointer" onClick={() => setNavbar('search')}>
                  Search
                </div>
              </div>
            </div>
          </div>
        </nav>
        <div>
          { navbar === 'live' ? <LiveOddsDashboard /> : <SearchOdds /> }
        </div>
      </div>
    </>
  )
}

export default OddsDashboard;
