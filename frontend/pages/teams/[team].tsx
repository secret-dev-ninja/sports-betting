import React from 'react';
import ArchiveDashboard from '@/components/archive_dashboard';
import { Bell } from "lucide-react";
import { GetServerSideProps } from 'next';
import { useRouter } from 'next/router';
import LiveDashboard from '@/components/live_dashboard';
import Link from 'next/link';

interface TeamData {
  event_id: string;
  home_team: string;
  away_team: string;
  league_name: string;
  starts: string;
  updated_at: string;
}

interface TeamPageProps {
  initialData: TeamData[];
  error?: string;
  type: string;
}

const Teams = ({ initialData, error, type }: TeamPageProps) => {
  const router = useRouter();
  const { team } = router.query;

  if (error) {
    return (
      <div className="p-4 max-w-4xl mx-auto">
        <div className="text-red-500">Error loading data: {error}</div>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <nav className="bg-black shadow-md rounded-s">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-start justify-between">
            <div className="text-white font-bold text-xl">
              <div className='flex items-center gap-2'>
                <Bell className="h-5 w-5" />
                Odds Updates
              </div>
            </div>
            <div className="flex-1 flex justify-start ml-10 space-x-6">
              <Link 
                href={`/teams/${team}`}
                className={`font-semibold hover:text-gray-300 ${!type ? 'text-white' : 'text-gray-400'}`}
              >
                Archive
              </Link>
              <Link 
                href={`/teams/${team}?type=live`}
                className={`font-semibold hover:text-gray-300 ${type === 'live' ? 'text-white' : 'text-gray-400'}`}
              >
                Live
              </Link>
            </div>
          </div>
        </div>
      </nav>
      <div>
        {!type ? <ArchiveDashboard data={initialData} /> : <LiveDashboard data={initialData} />}
      </div>
    </div>
  );
};

export const getServerSideProps: GetServerSideProps = async (context) => {
  const { team, type } = context.query as { team: string, type: string };

  try {
    if (!team) {
      throw new Error('Team parameter is required');
    }

    const response = await fetch(
      `${process.env.NEXT_APP_EVENT_API_URL}?team_name=${team}&type=${!type ? 'archive' : 'live'}`,
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      props: {
        initialData: data,
        type: type || null
      },
    };
  } catch (error) {
    return {
      props: {
        initialData: [],
        error: error instanceof Error ? error.message : 'Failed to fetch team data',
        type: type || null
      },
    };
  }
};

export default Teams;
