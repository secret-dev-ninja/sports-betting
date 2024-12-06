import ArchiveDashboard from '../../../../../components/archive_dashboard';
import { NextPage } from 'next';
import { Bell } from "lucide-react";

const EventPage: NextPage = () => {
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
                <div className="font-semibold text-white mt-[0.7] hover:text-gray-300 hover:cursor-pointer">
                  Archive
                </div>
              </div>
            </div>
          </div>
        </nav>
        <div>
          <ArchiveDashboard />
        </div>
      </div>
    </>
  );
};

export default EventPage;