import React, { useState, useEffect } from 'react';
import Papa from 'papaparse';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const MyFitnessPalDashboard = () => {
  const [measurementData, setMeasurementData] = useState([]);
  const [nutritionData, setNutritionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
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
            setMeasurementData(results.data.map(item => ({
              ...item,
              Weight: parseFloat(item.Weight)
            })));
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

    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">MyFitnessPal Dashboard</h1>
      
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Weight Measurements</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={measurementData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="Date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="Weight" stroke="#8884d8" />
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
                {nutritionData.map((nutrition, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-gray-100' : ''}>
                    <td className="px-4 py-2">{nutrition.Date}</td>
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