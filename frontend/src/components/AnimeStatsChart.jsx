import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';

const metricJokes = {
  'Horniness Level': 'The camera angles don\'t lie',
  'Plot Armor Thickness': 'MC could survive a nuke to the face',
  'Filler Hell': 'Beach episodes count as character development, right?',
  'Power Creep': 'Started with fireball, now destroys planets',
  'Cringe Factor': 'Secondhand embarrassment is real',
  'Fan Toxicity': 'Don\'t check the Twitter replies'
};

function AnimeStatsChart({ stats }) {
  // Transform stats object into array format for Recharts
  const data = [
    { metric: 'Horniness Level', value: stats.horniness_level, fullMark: 100 },
    { metric: 'Plot Armor Thickness', value: stats.plot_armor_thickness, fullMark: 100 },
    { metric: 'Filler Hell', value: stats.filler_hell, fullMark: 100 },
    { metric: 'Power Creep', value: stats.power_creep, fullMark: 100 },
    { metric: 'Cringe Factor', value: stats.cringe_factor, fullMark: 100 },
    { metric: 'Fan Toxicity', value: stats.fan_toxicity, fullMark: 100 }
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const metric = payload[0].payload.metric;
      const value = payload[0].value;
      const joke = metricJokes[metric];
      
      return (
        <div className="bg-[#1f1f1f] border border-[#262626] rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold mb-1">{metric}: {value}/100</p>
          <p className="text-[#a3a3a3] text-sm italic">"{joke}"</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-[280px] md:h-[320px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="65%" data={data}>
          <PolarGrid 
            stroke="#262626" 
            radialLines={true}
          />
          <PolarAngleAxis 
            dataKey="metric" 
            tick={{ 
              fill: '#ffffff', 
              fontSize: 10,
              fontWeight: 500
            }}
          />
          <PolarRadiusAxis 
            angle={90} 
            domain={[0, 100]} 
            tick={{ fill: '#737373', fontSize: 9 }}
            tickCount={5}
            stroke="#262626"
          />
          <Radar
            name="Anime Stats"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="#3b82f6"
            fillOpacity={0.15}
          />
          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default AnimeStatsChart;