import React, { useEffect, useState } from 'react';
import ArchiveDashboard from '@/components/archive_dashboard';
import LiveDashboard from '@/components/live_dashboard';
import Link from 'next/link';
import { Bell } from "lucide-react";
import dotenv from "dotenv";

dotenv.config();

const OddsDashboard = () => {
  const [navbar, setNavbar] = useState<String>('archive');

  return (
    <>
      <div className="p-4 max-w-6xl mx-auto">
        <nav className="bg-black shadow-md rounded-s">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-start justify-between">
              <div className="text-white font-bold text-xl">
                <div className='flex items-center gap-2 hover:cursor-pointer'>
                  <Bell className="h-5 w-5" />
                  Odds Updates
                </div>
              </div>
              <div className="flex-1 flex justify-start ml-10 space-x-6">
                <Link 
                  href={`/`}
                  className={`font-semibold hover:text-gray-300 ${navbar === 'archive' ? 'text-blue-500' : 'text-white'}`}
                  onClick={() => setNavbar('archive')}
                >
                    Archive
                </Link>
                <Link 
                  href={`/`}
                  className={`font-semibold hover:text-gray-300 ${navbar === 'live' ? 'text-blue-500' : 'text-white'}`}
                  onClick={() => setNavbar('live')}
                >
                    Live
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <div>
          {navbar === 'archive' ? <ArchiveDashboard data={[]} /> : <LiveDashboard data={[]} />}
        </div>
      </div>
    </>
  )
}

export default OddsDashboard;
