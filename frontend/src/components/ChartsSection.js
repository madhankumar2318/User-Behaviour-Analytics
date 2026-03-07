import React from 'react';
import { Line, Pie, Bar } from "react-chartjs-2";

function ChartsSection({
    activeChartTab,
    setActiveChartTab,
    timelineData,
    riskDistribution,
    locationData,
    heatmapData
}) {
    return (
        <div className="chart-section">
            <div className="chart-controls">
                <button
                    className={activeChartTab === 'timeline' ? 'active' : ''}
                    onClick={() => setActiveChartTab('timeline')}
                >Timeline</button>
                <button
                    className={activeChartTab === 'distribution' ? 'active' : ''}
                    onClick={() => setActiveChartTab('distribution')}
                >Risk Distribution</button>
                <button
                    className={activeChartTab === 'locations' ? 'active' : ''}
                    onClick={() => setActiveChartTab('locations')}
                >Locations</button>
                <button
                    className={activeChartTab === 'heatmap' ? 'active' : ''}
                    onClick={() => setActiveChartTab('heatmap')}
                >24h Heatmap</button>
            </div>

            <div className="chart-container">
                {activeChartTab === 'timeline' && <Line data={timelineData} options={{ responsive: true, plugins: { legend: { position: 'top' } } }} />}
                {activeChartTab === 'distribution' && <div style={{ maxWidth: '400px', margin: '0 auto' }}><Pie data={riskDistribution} /></div>}
                {activeChartTab === 'locations' && <Bar data={locationData} />}
                {activeChartTab === 'heatmap' && (
                    <div className="heatmap-container">
                        <div className="heatmap-grid">
                            <div className="heatmap-y-labels">
                                {heatmapData.days.map((day, i) => (
                                    <div key={i} className="heatmap-label">{day}</div>
                                ))}
                            </div>
                            <div className="heatmap-cells">
                                {heatmapData.grid.map((row, dayIdx) => (
                                    <div key={dayIdx} className="heatmap-row">
                                        {row.map((count, hourIdx) => {
                                            const maxCount = Math.max(...heatmapData.grid.flat());
                                            const intensity = maxCount > 0 ? count / maxCount : 0;
                                            const color = `rgba(167, 139, 250, ${intensity})`;
                                            return (
                                                <div
                                                    key={hourIdx}
                                                    className="heatmap-cell"
                                                    style={{ backgroundColor: color }}
                                                    title={`${heatmapData.days[dayIdx]} ${hourIdx}:00 - ${count} activities`}
                                                >
                                                    {count > 0 ? count : ''}
                                                </div>
                                            );
                                        })}
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="heatmap-x-labels">
                            {heatmapData.hours.filter((_, i) => i % 2 === 0).map((hour, i) => (
                                <div key={i} className="heatmap-label">{hour}h</div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default ChartsSection;
