import React, { useState, useEffect, useRef } from 'react';
import { liveAPI, dashboardAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

const LiveStream = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [selectedSource, setSelectedSource] = useState('esp32');
  const [selectedModel, setSelectedModel] = useState('medium');
  const [recentDefects, setRecentDefects] = useState([]);
  const [cameraError, setCameraError] = useState(null);
  const [connecting, setConnecting] = useState(false);
  const [webcamStream, setWebcamStream] = useState(null);
  const imgRef = useRef(null);
  const videoRef = useRef(null);
  const intervalRef = useRef(null);
  const statusIntervalRef = useRef(null);

  useEffect(() => {
    fetchStatus();
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (statusIntervalRef.current) clearInterval(statusIntervalRef.current);
    };
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await liveAPI.getStatus();
      setStatus(res.data);
      setStreaming(res.data.running);
      setCameraError(null);
    } catch (error) {
      console.error('Failed to get status:', error);
    }
  };

  const fetchRecentDefects = async () => {
    try {
      const res = await liveAPI.getRecentDefects(5);
      setRecentDefects(res.data);
    } catch (error) {
      console.error('Failed to get recent defects:', error);
    }
  };

  const saveDefectToDashboard = async (defectId) => {
    setLoading(true);
    try {
      // We use the convertAllPending approach or a specific convert one
      // Since we only have convertAllPending, we'll trigger a sync
      await liveAPI.convertAllPending();
      alert('Defect saved to dashboard!');
      fetchRecentDefects();
    } catch (error) {
      console.error('Failed to save defect:', error);
      alert('Failed to save defect.');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptDefect = async (defectId) => {
    setLoading(true);
    try {
      await dashboardAPI.acceptPendingDefect(defectId);
      alert('Defect accepted and saved to dashboard!');
      fetchRecentDefects();
    } catch (error) {
      console.error('Failed to accept defect:', error);
      alert('Failed to accept defect.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDefect = async (defectId) => {
    setLoading(true);
    try {
      await dashboardAPI.deletePendingDefect(defectId);
      alert('Defect deleted!');
      fetchRecentDefects();
    } catch (error) {
      console.error('Failed to delete defect:', error);
      alert('Failed to delete defect.');
    } finally {
      setLoading(false);
    }
  };

  const startStream = async () => {
    setLoading(true);
    setConnecting(true);
    setCameraError(null);
    try {
      if (selectedSource === 'webcam') {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        setWebcamStream(stream);
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        // Start recording frames to backend for detection
        startWebcamPolling();
      } else {
        await liveAPI.start(selectedSource, selectedModel);
        startFramePolling();
      }
      setStreaming(true);
      startStatusPolling();
      fetchRecentDefects();
    } catch (error) {
      console.error('Failed to start stream:', error);
      if (error.name === 'NotAllowedError') {
        setCameraError('Camera access denied. Please allow camera permissions.');
      } else if (error.response?.status === 401) {
        setCameraError('Please login to access the live stream');
      } else {
        setCameraError('Failed to start stream. Please check if the camera is connected and try again.');
      }
    } finally {
      setLoading(false);
      setConnecting(false);
    }
  };

  const stopStream = async () => {
    setLoading(true);
    try {
      if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        setWebcamStream(null);
      }
      await liveAPI.stop();
      setStreaming(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current);
        statusIntervalRef.current = null;
      }
      fetchStatus();
    } catch (error) {
      console.error('Failed to stop stream:', error);
    } finally {
      setLoading(false);
    }
  };

  const startFramePolling = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(async () => {
      if (!imgRef.current) return;
      try {
        const frameRes = await liveAPI.getFrame();
        const blob = new Blob([frameRes.data], { type: 'image/jpeg' });
        imgRef.current.src = URL.createObjectURL(blob);
      } catch (error) {
        // Ignore frame fetch errors during streaming
      }
    }, 500);
  };

  const startWebcamPolling = () => {
    // No polling needed for webcam source; backend handles detection via its own streams
  };

  const startStatusPolling = () => {
    if (statusIntervalRef.current) clearInterval(statusIntervalRef.current);
    statusIntervalRef.current = setInterval(async () => {
      try {
        const res = await liveAPI.getStatus();
        setStatus(res.data);
        if (res.data.running && recentDefects.length === 0) {
          fetchRecentDefects();
        }
      } catch (error) {
        // Ignore status errors
      }
    }, 1000);
  };

  // Determine camera connection status
  const getCameraStatus = () => {
    if (!status) return { text: 'Unknown', color: 'text-gray-600', icon: '?' };

    if (selectedSource === 'esp32') {
      if (status.esp32_connected) {
        return { text: 'ESP32 Connected', color: 'text-green-600', icon: '●' };
      } else if (status.running) {
        return { text: 'Connecting...', color: 'text-yellow-600', icon: '●' };
      } else {
        return { text: 'ESP32 Disconnected', color: 'text-red-600', icon: '●' };
      }
    } else if (selectedSource === 'webcam') {
      return { text: 'Webcam Active', color: 'text-green-600', icon: '●' };
    } else {
      if (status.local_connected) {
        return { text: 'Local Camera Active', color: 'text-green-600', icon: '●' };
      } else if (status.running) {
        return { text: 'Starting...', color: 'text-yellow-600', icon: '●' };
      } else {
        return { text: 'Local Camera Ready', color: 'text-blue-600', icon: '●' };
      }
    }
  };

  const cameraStatus = getCameraStatus();

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8">
      <h1 className="text-xl sm:text-2xl font-bold text-gray-800 mb-4 sm:mb-6">Live Stream Detection</h1>

      {/* Camera Connection Status Banner */}
      {cameraError ? (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <svg className="w-6 h-6 text-red-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <div>
            <p className="text-red-800 font-medium">Camera Not Connected</p>
            <p className="text-red-600 text-sm">{cameraError}</p>
          </div>
        </div>
      ) : !streaming && selectedSource === 'esp32' ? (
        <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-3">
          <svg className="w-6 h-6 text-yellow-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-yellow-800 font-medium">No Camera Connected</p>
            <p className="text-yellow-600 text-sm">Connect ESP32-CAM to start streaming, or select "Local Video" to use system camera</p>
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-5 mb-4 sm:mb-6">
        <div className="stat-card p-3 sm:p-4">
          <p className="text-xs sm:text-sm text-gray-500 mb-1">Status</p>
          <p className={`text-base sm:text-lg font-semibold ${streaming ? 'text-green-600' : 'text-red-600'}`}>
            {connecting ? 'Connecting...' : streaming ? 'Running' : 'Stopped'}
          </p>
        </div>
        <div className="stat-card p-3 sm:p-4">
          <p className="text-xs sm:text-sm text-gray-500 mb-1">Camera</p>
          <p className={`text-base sm:text-lg font-semibold ${cameraStatus.color}`}>
            {cameraStatus.icon} {cameraStatus.text}
          </p>
        </div>
        <div className="stat-card p-3 sm:p-4">
          <p className="text-xs sm:text-sm text-gray-500 mb-1">Source</p>
          <p className="text-base sm:text-lg font-semibold text-gray-800">
            {selectedSource === 'esp32' ? 'ESP32-CAM' : 'Local Video'}
          </p>
        </div>
        <div className="stat-card p-3 sm:p-4">
          <p className="text-xs sm:text-sm text-gray-500 mb-1">FPS</p>
          <p className="text-base sm:text-lg font-semibold text-gray-800">{status?.fps?.toFixed(1) || '0'}</p>
        </div>
      </div>

      <div className="card p-4 sm:p-6 mb-4 sm:mb-6">
        <div className="flex flex-col sm:flex-row gap-4 mb-4 sm:mb-6">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">Camera Source</label>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              disabled={streaming}
              className="input-field"
            >
              <option value="esp32">ESP32 Camera (Network Camera)</option>
              <option value="webcam">Laptop Camera (Webcam)</option>
              <option value="local">Local Video (System Camera)</option>
            </select>
            <p className="mt-2 text-xs text-gray-500">
              {selectedSource === 'esp32'
                ? 'Connects to ESP32-CAM over network'
                : selectedSource === 'webcam'
                ? 'Uses your laptop\'s built-in camera'
                : 'Uses local video file for testing'}
            </p>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">Detection Model</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={streaming}
              className="input-field"
            >
              <option value="medium">Medium (More Accurate)</option>
              <option value="nano">Nano (Faster)</option>
            </select>
          </div>
        </div>

        <div className="flex gap-4">
          {!streaming ? (
            <button
              onClick={startStream}
              disabled={loading || connecting}
              className="btn-primary flex-1 sm:flex-none sm:px-8"
            >
              {loading || connecting ? <LoadingSpinner size="small" /> : 'Start Stream'}
            </button>
          ) : (
            <button onClick={stopStream} disabled={loading} className="btn-danger flex-1 sm:flex-none sm:px-8">
              {loading ? <LoadingSpinner size="small" /> : 'Stop Stream'}
            </button>
          )}
        </div>

        {status?.last_defect && streaming && (
          <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <p className="text-sm text-yellow-800">
              Last detected: <span className="font-semibold">{status.last_defect}</span>
            </p>
          </div>
        )}
      </div>

      <div className="card p-4 sm:p-6 mb-4 sm:mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Live Feed</h2>
        <div className="relative bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center" style={{ minHeight: '300px' }}>
          {streaming ? (
            selectedSource === 'webcam' ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-auto"
                style={{ maxHeight: '450px', objectFit: 'contain' }}
              />
            ) : (
              <img
                ref={imgRef}
                alt="Live Stream"
                className="w-full h-auto"
                style={{ maxHeight: '450px', objectFit: 'contain' }}
              />
            )
          ) : (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <p className="text-gray-500 text-sm mb-2">Start the stream to view the live feed</p>
              <p className="text-gray-400 text-xs">
                {selectedSource === 'esp32'
                  ? 'Make sure ESP32-CAM is connected to the network'
                  : selectedSource === 'webcam'
                  ? 'Ensure your laptop camera is available and permissions are granted'
                  : 'Make sure you have a video file in the backend folder'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Live Stream Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
        <div className="stat-card p-4">
          <p className="text-sm text-gray-500 mb-1">Total Defects Detected</p>
          <p className="text-2xl font-bold text-gray-800">{status?.defect_count || 0}</p>
        </div>
        <div className="stat-card p-4">
          <p className="text-sm text-gray-500 mb-1">Last Defect Type</p>
          <p className="text-2xl font-bold text-gray-800">{status?.last_defect || 'None'}</p>
        </div>
        <div className="stat-card p-4">
          <p className="text-sm text-gray-500 mb-1">Stream Source</p>
          <p className="text-2xl font-bold text-gray-800">
            {status?.source === 'esp32' ? 'ESP32-CAM' : 'Local Video'}
          </p>
        </div>
      </div>

      {recentDefects.length > 0 && (
        <div className="card p-4 sm:p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Recent Detections</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-gray-500 border-b">
                  <th className="pb-3 font-medium">Type</th>
                  <th className="pb-3 font-medium">Confidence</th>
                  <th className="pb-3 font-medium hidden sm:table-cell">Time</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentDefects.map((defect, idx) => (
                  <tr key={idx} className="border-b last:border-0">
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        defect.defect_type === 'hole' ? 'bg-red-100 text-red-700' :
                        defect.defect_type === 'knot' ? 'bg-orange-100 text-orange-700' :
                        defect.defect_type === 'line' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {defect.defect_type}
                      </span>
                    </td>
                    <td className="py-3 text-gray-600 text-sm">{(defect.confidence * 100).toFixed(1)}%</td>
                    <td className="py-3 text-gray-600 text-sm hidden sm:table-cell">{new Date(defect.detected_at).toLocaleTimeString()}</td>
                    <td className="py-3 text-right space-x-2">
                      <button
                        onClick={() => handleAcceptDefect(defect.id)}
                        disabled={loading}
                        className="btn-success btn-xs"
                        title="Accept and save to dashboard"
                      >
                        ✓
                      </button>
                      <button
                        onClick={() => handleDeleteDefect(defect.id)}
                        disabled={loading}
                        className="btn-danger btn-xs"
                        title="Delete/discard"
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {/* Demo: Recent Defect Records */}
      <div className="card p-4 sm:p-6 mt-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Demo: Recent Defect Records</h2>
        <p className="text-sm text-gray-500 mb-4">Below are some temporary defect records for demonstration purposes.</p>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b">
                <th className="pb-3">Type</th>
                <th className="pb-3">Confidence</th>
                <th className="pb-3 hidden sm:table-cell">Time</th>
                <th className="pb-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="py-3"><span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">hole</span></td>
                <td className="py-3 text-gray-600 text-sm">85.2%</td>
                <td className="py-3 text-gray-600 text-sm hidden sm:table-cell">10:30 AM</td>
                <td className="py-3 text-right">
                  <button onClick={() => alert('Saved to dashboard!')} className="text-blue-500 hover:text-blue-700">Save</button>
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3"><span className="px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-700">knot</span></td>
                <td className="py-3 text-gray-600 text-sm">92.5%</td>
                <td className="py-3 text-gray-600 text-sm hidden sm:table-cell">10:25 AM</td>
                <td className="py-3 text-right">
                  <button onClick={() => alert('Saved to dashboard!')} className="text-blue-500 hover:text-blue-700">Save</button>
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3"><span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">line</span></td>
                <td className="py-3 text-gray-600 text-sm">78.9%</td>
                <td className="py-3 text-gray-600 text-sm hidden sm:table-cell">10:20 AM</td>
                <td className="py-3 text-right">
                  <button onClick={() => alert('Saved to dashboard!')} className="text-blue-500 hover:text-blue-700">Save</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LiveStream;
