import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bell } from "lucide-react";

// Define the shape of the odds update data
interface OddsUpdate {
  sport_id: number;
  event_id: string;
  home_team: string;
  away_team: string;
  table_updated: string;
  update_time: string;
  id: string;
}

const OddsDashboard = () => {
      const [updates, setUpdates] = useState<OddsUpdate[]>([]);
      const [activeTab, setActiveTab] = useState<Number>(1);

      useEffect(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        console.log('Connected to WebSocket');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('data:', data);
        
        setUpdates(prev => [{
          ...data,
          id: `${data.event_id}-${Date.now()}-${data.table_updated}`
        }, ...prev].slice(0, 50)); // Keep last 50 updates
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed');
      };

      return () => {
        ws.close();
      };
  }, []);

  const sportsList: string[] = ["Soccer", "Tennis", "Basketball", "Hockey", "Volleyball", "Handball", "American Football", "Mixed Martial Arts", "Baseball"]; 

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Live Odds Updates
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex border-b border-gray-200 mb-4">
              {sportsList.map((sports, index) => (
                <button
                  key={index}
                  className={`px-4 py-2 text-sm font-medium text-gray-700 ${
                    activeTab === (index + 1)
                      ? 'border-b-2 border-blue-500 text-blue-500'
                      : 'hover:text-blue-500'
                  }`}
                  onClick={() => setActiveTab(index + 1)}
                >
                  {sports}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            {updates.map(
              (update, index) =>
                activeTab === update.sport_id && (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium">
                        {update.home_team} vs {update.away_team}
                      </div>
                      <div className="text-sm text-gray-500">
                        Event ID: {update.event_id}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary">
                        {update.table_updated}
                      </Badge>
                      <div className="text-sm text-gray-500">
                        {new Date(update.update_time).toLocaleTimeString() || 'Invalid time'}
                      </div>
                    </div>
                  </div>
                )
            )}  
            {updates.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                Waiting for updates...
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OddsDashboard;
