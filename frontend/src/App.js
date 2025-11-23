import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Plot from 'react-plotly.js';
import './App.css';

const API_BASE_URL = 'http://localhost:5000';


function Navigation() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/">
          
          <span className="brand-name">SonarSense</span>
        </Link>
      </div>
      <div className="nav-links">
        <Link to="/" className="nav-link">Analyze</Link>
        <Link to="/history" className="nav-link">History</Link>
        <Link to="/admin" className="nav-link">Admin</Link>
        {stats && (
          <div className="nav-stat">
            <span className="stat-label">Total:</span>
            <span className="stat-value">{stats.total_predictions}</span>
          </div>
        )}
      </div>
    </nav>
  );
}


function AnalyzePage() {
  const [file, setFile] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
    setPrediction(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);
    setPrediction(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/predict`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setPrediction(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Error making prediction');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async (resultId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/report/${resultId}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sonar_report_${resultId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error downloading report:', err);
      alert('Failed to download report');
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.8) return '#10b981';
    if (confidence > 0.6) return '#f59e0b';
    return '#ef4444';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence > 0.8) return 'High Confidence';
    if (confidence > 0.6) return 'Medium Confidence';
    return 'Low Confidence';
  };

  return (
    <div className="analyze-page">
      <div className="page-header">
        <h1> Sonar Signal Analysis</h1>
        <p>Upload a sonar audio file (.wav, .mp3, .flac)</p>
      </div>

      <div className="upload-section">
        <form onSubmit={handleSubmit} className="upload-form">
          <div className="file-input-wrapper">
            <input
              type="file"
              id="file-input"
              accept=".wav,.mp3,.flac"
              onChange={handleFileChange}
              disabled={loading}
              className="file-input"
            />
            <label htmlFor="file-input" className="file-label">
              <span className="file-icon">📁</span>
              <span className="file-text">
                {file ? file.name : 'Choose sonar audio file'}
              </span>
            </label>
          </div>
          <button type="submit" disabled={loading || !file} className="analyze-btn">
            {loading ? (
              <>
                <span className="spinner"></span>
                Analyzing...
              </>
            ) : (
              <>
                <span></span>
                Classify Signal
              </>
            )}
          </button>
        </form>
        
        {error && (
          <div className="error-message">
            <span></span>
            {error}
          </div>
        )}
      </div>

      {prediction && (
        <div className="results-container">
          {}
          <div className="result-card main-result">
            <div className="result-header">
              <h2>Classification Result</h2>
              <span className="result-id">ID: #{prediction.result_id}</span>
            </div>
            
            <div className="prediction-display">
              <div className="prediction-icon">
                {prediction.prediction === 'Torpedo'}
                {prediction.prediction === 'Submarine'}
                {prediction.prediction === 'Fish'}
                {prediction.prediction === 'Rock'}
                {prediction.prediction === 'Unknown'}
              </div>
              <div className="prediction-details">
                <h3 className="prediction-label">{prediction.prediction}</h3>
                <div className="confidence-bar-container">
                  <div 
                    className="confidence-bar" 
                    style={{
                      width: `${prediction.confidence * 100}%`,
                      backgroundColor: getConfidenceColor(prediction.confidence)
                    }}
                  ></div>
                </div>
                <div className="confidence-info">
                  <span className="confidence-value">{(prediction.confidence * 100).toFixed(2)}%</span>
                  <span 
                    className="confidence-label"
                    style={{ color: getConfidenceColor(prediction.confidence) }}
                  >
                    {getConfidenceLabel(prediction.confidence)}
                  </span>
                </div>
              </div>
            </div>

            <div className="probabilities-grid">
              {Object.entries(prediction.probabilities).map(([label, prob]) => (
                <div key={label} className="probability-item">
                  <span className="prob-label">{label}</span>
                  <div className="prob-bar-bg">
                    <div 
                      className="prob-bar" 
                      style={{ width: `${prob * 100}%` }}
                    ></div>
                  </div>
                  <span className="prob-value">{(prob * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>

            <div className="result-actions">
              <button 
                onClick={() => downloadReport(prediction.result_id)}
                className="download-btn"
              >
                <span>📄</span>
                Download PDF Report
              </button>
              <span className="timestamp">
                Analyzed: {new Date(prediction.timestamp).toLocaleString()}
              </span>
            </div>
          </div>

          {}
          {prediction.waveform_data && prediction.waveform_data.time && (
            <div className="result-card">
              <h3>Signal Waveform</h3>
              <Plot
                data={[
                  {
                    x: prediction.waveform_data.time,
                    y: prediction.waveform_data.amplitude,
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#2563eb', width: 1 },
                    name: 'Amplitude'
                  }
                ]}
                layout={{
                  autosize: true,
                  title: 'Sonar Signal Waveform',
                  xaxis: { title: 'Time (s)' },
                  yaxis: { title: 'Amplitude' },
                  plot_bgcolor: '#f8fafc',
                  paper_bgcolor: '#ffffff',
                  margin: { l: 60, r: 40, t: 60, b: 60 }
                }}
                style={{ width: '100%', height: '400px' }}
                config={{ responsive: true }}
              />
            </div>
          )}

          {}
          {prediction.frequency_data && prediction.frequency_data.frequency && (
            <div className="result-card">
              <h3>Frequency Spectrum</h3>
              <Plot
                data={[
                  {
                    x: prediction.frequency_data.frequency,
                    y: prediction.frequency_data.magnitude,
                    type: 'scatter',
                    mode: 'lines',
                    fill: 'tozeroy',
                    line: { color: '#7c3aed', width: 1 },
                    name: 'Magnitude'
                  }
                ]}
                layout={{
                  autosize: true,
                  title: 'Frequency Spectrum Analysis',
                  xaxis: { title: 'Frequency (Hz)', range: [0, 8000] },
                  yaxis: { title: 'Magnitude' },
                  plot_bgcolor: '#f8fafc',
                  paper_bgcolor: '#ffffff',
                  margin: { l: 60, r: 40, t: 60, b: 60 }
                }}
                style={{ width: '100%', height: '400px' }}
                config={{ responsive: true }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}


function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchHistory();
    fetchStats();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/history?limit=50`);
      setHistory(response.data.history);
    } catch (err) {
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const downloadReport = async (resultId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/report/${resultId}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sonar_report_${resultId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error downloading report:', err);
    }
  };

  const exportCSV = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/report/csv`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sonar_results_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error exporting CSV:', err);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner large"></div>
        <p>Loading history...</p>
      </div>
    );
  }

  return (
    <div className="history-page">
      <div className="page-header">
        <h1> Prediction History</h1>
        <button onClick={exportCSV} className="export-btn">
          <span></span>
          Export CSV
        </button>
      </div>

      {stats && (
        <div className="stats-overview">
          <div className="stat-box">
            <div className="stat-icon"></div>
            <div className="stat-content">
              <div className="stat-label">Total Predictions</div>
              <div className="stat-value">{stats.total_predictions}</div>
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-icon"></div>
            <div className="stat-content">
              <div className="stat-label">Average Confidence</div>
              <div className="stat-value">{(stats.average_confidence * 100).toFixed(1)}%</div>
            </div>
          </div>
          {stats.prediction_distribution && Object.keys(stats.prediction_distribution).length > 0 && (
            <div className="stat-box wide">
              <div className="stat-icon"></div>
              <div className="stat-content">
                <div className="stat-label">Distribution</div>
                <div className="distribution-bars">
                  {Object.entries(stats.prediction_distribution).map(([label, count]) => (
                    <div key={label} className="distribution-item">
                      <span className="dist-label">{label}</span>
                      <div className="dist-bar-bg">
                        <div 
                          className="dist-bar" 
                          style={{ 
                            width: `${(count / stats.total_predictions) * 100}%` 
                          }}
                        ></div>
                      </div>
                      <span className="dist-count">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="history-table-container">
        <table className="history-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Detection</th>
              <th>Confidence</th>
              <th>Timestamp</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item) => (
              <tr key={item.id}>
                <td className="id-cell">#{item.id}</td>
                <td className="prediction-cell">
                  <span className="prediction-badge">{item.prediction}</span>
                </td>
                <td className="confidence-cell">
                  <div className="confidence-indicator">
                    <div 
                      className="confidence-dot"
                      style={{
                        backgroundColor: 
                          item.confidence > 0.8 ? '#10b981' : 
                          item.confidence > 0.6 ? '#f59e0b' : '#ef4444'
                      }}
                    ></div>
                    {(item.confidence * 100).toFixed(1)}%
                  </div>
                </td>
                <td className="timestamp-cell">
                  {new Date(item.created_at).toLocaleString()}
                </td>
                <td className="actions-cell">
                  <button 
                    onClick={() => downloadReport(item.id)}
                    className="action-btn"
                    title="Download Report"
                  >
                    📄
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {history.length === 0 && (
          <div className="empty-state">
            <span className="empty-icon">📭</span>
            <p>No predictions yet</p>
            <button onClick={() => navigate('/')} className="cta-btn">
              Start Analyzing
            </button>
          </div>
        )}
      </div>
    </div>
  );
}


function AdminPage() {
  const [modelInfo, setModelInfo] = useState(null);
  const [training, setTraining] = useState(false);
  const [trainResult, setTrainResult] = useState(null);
  const [error, setError] = useState(null);
  const [adminToken, setAdminToken] = useState('admin123');

  useEffect(() => {
    fetchModelInfo();
  }, []);

  const fetchModelInfo = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/model/info`);
      setModelInfo(response.data);
    } catch (err) {
      console.error('Error fetching model info:', err);
    }
  };

  const handleRetrain = async () => {
    if (!window.confirm('Are you sure you want to retrain the model? This may take several minutes.')) {
      return;
    }

    setTraining(true);
    setError(null);
    setTrainResult(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/train`,
        {},
        {
          headers: {
            'X-Admin-Token': adminToken
          }
        }
      );
      
      setTrainResult(response.data);
      await fetchModelInfo();
    } catch (err) {
      setError(err.response?.data?.error || 'Training failed');
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="admin-page">
      <div className="page-header">
        <h1> Admin Dashboard</h1>
        <p></p>
      </div>

      <div className="admin-grid">
        {}
        <div className="admin-card">
          <h2> Model Information</h2>
          {modelInfo ? (
            <div className="info-list">
              <div className="info-item">
                <span className="info-label">Model Type:</span>
                <span className="info-value">{modelInfo.model_type}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Features:</span>
                <span className="info-value">{modelInfo.n_features}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Classes:</span>
                <span className="info-value">{modelInfo.n_classes}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Supported Types:</span>
                <div className="classes-list">
                  {modelInfo.classes?.map((cls) => (
                    <span key={cls} className="class-tag">{cls}</span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="loading-text">Loading model info...</p>
          )}
        </div>

        {}
        <div className="admin-card">
          <h2> Model Training</h2>
          <p className="card-description">
            Retrain the model with the latest dataset. This process may take several minutes.
          </p>
          
          <div className="form-group">
            <label htmlFor="admin-token">Admin Token:</label>
            <input
              type="password"
              id="admin-token"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              placeholder="Enter admin token"
              className="admin-input"
            />
          </div>

          <button 
            onClick={handleRetrain}
            disabled={training || !adminToken}
            className="retrain-btn"
          >
            {training ? (
              <>
                <span className="spinner"></span>
                Training Model...
              </>
            ) : (
              <>
                <span></span>
                Retrain Model
              </>
            )}
          </button>

          {error && (
            <div className="error-message">
              <span></span>
              {error}
            </div>
          )}

          {trainResult && (
            <div className="success-message">
              <h3>Training Complete!</h3>
              <div className="train-results">
                <div className="train-result-item">
                  <span className="result-label">Accuracy:</span>
                  <span className="result-value">
                    {(trainResult.accuracy * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="train-result-item">
                  <span className="result-label">Classes:</span>
                  <span className="result-value">
                    {trainResult.classes?.join(', ')}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* System Info */}
        <div className="admin-card">
          <h2> System Information</h2>
          <div className="info-list">
            <div className="info-item">
              <span className="info-label">API Endpoint:</span>
              <span className="info-value code">{API_BASE_URL}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Version:</span>
              <span className="info-value">1.0.0</span>
            </div>
            <div className="info-item">
              <span className="info-label">Status:</span>
              <span className="status-badge online"> Online</span>
            </div>
          </div>
        </div>

        {}
        <div className="admin-card">
          <h2> API Endpoints</h2>
          <div className="api-list">
            <div className="api-item">
              <span className="api-method post">POST</span>
              <span className="api-path">/predict</span>
            </div>
            <div className="api-item">
              <span className="api-method get">GET</span>
              <span className="api-path">/history</span>
            </div>
            <div className="api-item">
              <span className="api-method get">GET</span>
              <span className="api-path">/stats</span>
            </div>
            <div className="api-item">
              <span className="api-method get">GET</span>
              <span className="api-path">/report/:id</span>
            </div>
            <div className="api-item">
              <span className="api-method post">POST</span>
              <span className="api-path">/train</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<AnalyzePage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>
        <footer className="app-footer">
          <p>SonarSense © 2024</p>
          <p className="footer-tech"></p>
        </footer>
      </div>
    </Router>
  );
}

export default App;