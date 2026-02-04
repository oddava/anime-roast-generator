import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer
} from 'recharts';

function MiniStatsChart({ stats }) {
  // Transform stats object into array format for Recharts
  const data = [
    { metric: 'Horniness', value: stats.horniness_level },
    { metric: 'Plot Armor', value: stats.plot_armor_thickness },
    { metric: 'Filler', value: stats.filler_hell },
    { metric: 'Power Creep', value: stats.power_creep },
    { metric: 'Cringe', value: stats.cringe_factor },
    { metric: 'Toxicity', value: stats.fan_toxicity }
  ];

  return (
    <div className="w-full h-24">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid stroke="#333" radialLines={false} />
          <PolarAngleAxis dataKey="metric" tick={false} />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          <Radar
            name="Stats"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={1.5}
            fill="#3b82f6"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default MiniStatsChart;
