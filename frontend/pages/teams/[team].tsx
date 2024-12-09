import React from 'react';
import ArchiveDashboard from '@/components/archive_dashboard';
import { useRouter } from 'next/router';
import { Bell } from "lucide-react";
import { GetServerSideProps } from 'next';

// Define TypeScript interface for the data
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
}

const Teams = ({ initialData, error }: TeamPageProps) => {
  const router = useRouter();

  // If there's an error, show error state
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
              <div className='flex items-center gap-2 hover:cursor-pointer'>
                <Bell className="h-5 w-5" />
                Live Odds Updates
              </div>
            </div>
            <div className="flex-1 flex justify-start ml-10 space-x-6">
              <div className="font-semibold text-white mt-[0.7] hover:text-gray-300 hover:cursor-pointer">
                Archive
              </div>
            </div>
          </div>
        </div>
      </nav>
      <div>
        <ArchiveDashboard data={initialData as TeamData[]} />
      </div>
    </div>
  );
};

export const getServerSideProps: GetServerSideProps = async (context) => {
  const { team } = context.params as { team: string };

  try {
    // Validate team parameter
    if (!team) {
      throw new Error('Team parameter is required');
    }

    // Fetch data server-side
    const response = await fetch(
      `${process.env.NEXT_APP_EVENT_API_URL}?sport_name=&league_name=&team_name=${team}&type=archive`,
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Return the data as props
    return {
      props: {
        initialData: data,
      },
    };
  } catch (error) {
    console.error('Error fetching team data:', error);
    
    // Return error state as props
    return {
      props: {
        initialData: [],
        error: error instanceof Error ? error.message : 'Failed to fetch team data',
      },
    };
  }
};

export default Teams;

