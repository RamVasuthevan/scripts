import React, { useState, useEffect } from 'react';
import Papa from 'papaparse';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const formatDate = (date) => {
  return date.toISOString().split('T')[0];
};

const DateRangeSelector = ({ onUpdate, initialStartDate, initialEndDate }) => {
  const [startDate, setStartDate] = useState(formatDate(initialStartDate));
  const [endDate, setEndDate] = useState(formatDate(initialEndDate));

  const handleUpdate = () => {
    onUpdate(new Date(startDate), new Date(endDate));
  };

  useEffect(() => {
    handleUpdate();
  }, []);

  return (
    <div className="mb-4">
      <input
        type="date"
        value={startDate}
        onChange={(e) => setStartDate(e.target.value)}
        className="mr-2 p-2 border rounded"
      />
      <input
        type="date"
        value={endDate}
        onChange={(e) => setEndDate(e.target.value)}
        className="mr-2 p-2 border rounded"
      />
      <button
        onClick={handleUpdate}
        className="p-2 bg-blue-500 text-white rounded"
      >
        Update Chart
      </button>
    </div>
  );
};

const MyFitnessPalDashboard = () => {
  const [measurementData, setMeasurementData] = useState([]);
  const [filteredMeasurementData, setFilteredMeasurementData] = useState([]);
  const [nutritionData, setNutritionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [yAxisDomain, setYAxisDomain] = useState([0, 'auto']);

  const today = new Date();
  const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [measurementResponse, nutritionResponse] = await Promise.all([
        fetch('/Measurement-Summary-2020-12-29-to-2024-08-17.csv'),
        fetch('/Nutrition-Summary-2020-12-29-to-2024-08-17.csv')
      ]);

      const measurementText = await measurementResponse.text();
      const nutritionText = await nutritionResponse.text();

      Papa.parse(measurementText, {
        header: true,
        complete: (results) => {
          const parsedData = results.data
            .filter(item => item.Date && item.Weight)
            .map(item => ({
              ...item,
              Weight: parseFloat(item.Weight),
              Date: new Date(item.Date)
            }))
            .sort((a, b) => a.Date - b.Date);
          setMeasurementData(parsedData);
          updateChart(thirtyDaysAgo, today);
        },
        error: (error) => {
          setError('Error parsing Measurement CSV: ' + error.message);
        }
      });

      Papa.parse(nutritionText, {
        header: true,
        complete: (results) => {
          setNutritionData(results.data);
        },
        error: (error) => {
          setError('Error parsing Nutrition CSV: ' + error.message);
        }
      });

      setLoading(false);
    } catch (error) {
      setError('Error fetching data: ' + error.message);
      setLoading(false);
    }
  };

  const updateChart = (startDate, endDate) => {
    if (startDate > endDate) {
      setError('Start date must be before end date');
      return;
    }

    const filteredData = measurementData.filter(item => 
      item.Date >= startDate && item.Date <= endDate
    );

    if (filteredData.length === 0) {
      setError('No data available for the selected date range');
      return;
    }

    setFilteredMeasurementData(filteredData);

    // Calculate the new Y-axis domain
    const weights = filteredData.map(item => item.Weight);
    const minWeight = Math.min(...weights);
    const maxWeight = Math.max(...weights);
    const yMin = Math.floor(minWeight / 5) * 5; // Round down to nearest 5
    const yMax = Math.ceil(maxWeight / 5) * 5; // Round up to nearest 5
    setYAxisDomain([yMin, yMax]);

    setError(null);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">MyFitnessPal Dashboard</h1>
      
      <DateRangeSelector 
        onUpdate={updateChart} 
        initialStartDate={thirtyDaysAgo}
        initialEndDate={today}
      />
      
      {error && <div className="text-red-500 mb-4">{error}</div>}

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Weight Measurements</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={filteredMeasurementData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="Date" 
                tickFormatter={(date) => formatDate(date)}
                angle={-45}
                textAnchor="end"
                height={70}
              />
              <YAxis 
                domain={yAxisDomain}
                tickCount={10}
                tickFormatter={(value) => `${value.toFixed(1)}`}
              />
              <Tooltip 
                labelFormatter={(label) => formatDate(new Date(label))}
                formatter={(value) => [`${value.toFixed(1)} lbs`, 'Weight']}
              />
              <Line 
                type="monotone" 
                dataKey="Weight" 
                stroke="#8884d8" 
                dot={false}
                activeDot={{ r: 8 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Nutrition Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="px-4 py-2 text-left">Date</th>
                  <th className="px-4 py-2 text-left">Meal</th>
                  <th className="px-4 py-2 text-left">Calories</th>
                  <th className="px-4 py-2 text-left">Fat (g)</th>
                  <th className="px-4 py-2 text-left">Carbohydrates (g)</th>
                  <th className="px-4 py-2 text-left">Protein (g)</th>
                </tr>
              </thead>
              <tbody>
                {nutritionData.slice(0, 10).map((nutrition, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-gray-100' : ''}>
                    <td className="px-4 py-2">{formatDate(new Date(nutrition.Date))}</td>
                    <td className="px-4 py-2">{nutrition.Meal}</td>
                    <td className="px-4 py-2">{nutrition.Calories}</td>
                    <td className="px-4 py-2">{nutrition['Fat (g)']}</td>
                    <td className="px-4 py-2">{nutrition['Carbohydrates (g)']}</td>
                    <td className="px-4 py-2">{nutrition['Protein (g)']}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MyFitnessPalDashboard;