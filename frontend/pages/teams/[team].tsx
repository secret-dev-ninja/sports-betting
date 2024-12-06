import React, {useEffect, useState} from 'react';
import ArchiveDashboard from '@/components/archive_dashboard';
import { useRouter } from 'next/router';
import { Bell } from "lucide-react";

const Teams = () => {
  const router = useRouter();
  const [data, setData] = useState<any[]>([]);
  const { team } = router.query;

  const fetchData = async (team_name: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_APP_EVENT_API_URL}?sport_name=&league_name=&team_name=${team_name}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        console.error('Error:', response.status, response.statusText);
      } else {
        const data = await response.json();
        console.log('data:', data);
        setData(data);
      }
    } catch (e) {
      console.log(e);
    }
  };

  useEffect(() => {
    if (team) {
      fetchData(team as string);
    } 
  }, [team]);

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
                {/* <div className="font-semibold text-white mt-[0.7] hover:text-gray-300 hover:cursor-pointer" onClick={() => setNavbar('live')}>
                  Live
                </div> */}
                {/* <div className="font-semibold text-white mt-[0.7] hover:text-gray-300 hover:cursor-pointer" onClick={() => setNavbar('archive')}> */}
                <div className="font-semibold text-white mt-[0.7] hover:text-gray-300 hover:cursor-pointer">
                  Archive
                </div>
              </div>
            </div>
          </div>
        </nav>
        <div>
          <ArchiveDashboard data={data} />
        </div>
      </div>
    </>
  );
};

export default Teams;

