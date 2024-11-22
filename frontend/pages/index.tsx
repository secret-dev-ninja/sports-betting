import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bell } from "lucide-react";

// Define the shape of the odds update data
interface OddsUpdate {
  event_id: string;
  home_team: string;
  away_team: string;
  table_updated: string;
  update_time: string;
  id: string;
}

const OddsDashboard = () => {
  const [updates, setUpdates] = useState<OddsUpdate[]>([]);

  // useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws');
  console.log('websocket:', ws);

  ws.onopen = () => {
    console.log('Connected to WebSocket');
    ws.send('Hello, server. I am a client.');
    // setWs(websocket);
  };

  ws.onmessage = (event) => {
    // console.log('Received message...', event.data);
    const data = JSON.parse(event.data);
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

  //   return () => {
  //     websocket.close();
  //   };
  // }, []);

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
            {updates.map((update, index) => (
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
            ))}
            
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
