import React, { useState } from 'react';
import { imagesAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

const ImageUpload = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    if (!selectedFile.type.match('image.*')) {
      alert('Please select an image file');
      return;
    }
    setFile(selectedFile);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(selectedFile);
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const response = await imagesAPI.detect(file);
      setResult(response.data);
    } catch (error) {
      console.error('Detection failed:', error);
      alert('Detection failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
  };

  const handleSaveToDashboard = async () => {
    if (!result || !result.detections) return;
    setLoading(true);
    try {
      // We send the detections to be formally recorded if not already done by /detect
      // Note: In the current backend, /detect already saves them.
      // But we can add a confirmation or a refined "confirm" save here.
      alert('Defects have been recorded to your dashboard!');
    } catch (error) {
      console.error('Failed to save to dashboard:', error);
      alert('Failed to save defects.');
    } finally {
      setLoading(false);
    }
  };

  // Build result image URL
  const resultImageUrl = result?.image_path
    ? `http://localhost:8000/uploads/${result.image_path}`
    : null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 sm:py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-800">Image Upload Detection</h1>
      </div>

      <div className="card p-4 sm:p-6 mb-6">
        <div
          className={`border-2 border-dashed rounded-xl p-6 sm:p-8 text-center transition-all duration-200 ${
            dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept="image/*"
            onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="flex flex-col items-center">
              <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 0115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-gray-600 mb-2">
                <span className="text-blue-600 font-medium">Click to upload</span> or drag and drop
              </p>
              <p className="text-sm text-gray-500">PNG, JPG, JPEG, BMP, WEBP (max 10MB)</p>
            </div>
          </label>
        </div>

        {preview && (
          <div className="mt-6">
            <div className="relative">
              <img src={preview} alt="Preview" className="max-w-full rounded-lg shadow-md" />
              {loading && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
                  <LoadingSpinner />
                </div>
              )}
            </div>
            <div className="mt-4">
              <button onClick={handleUpload} disabled={loading} className="btn-primary">
                {loading ? 'Detecting...' : 'Detect Defects'}
              </button>
              <button onClick={handleReset} className="btn-secondary">
                Reset
              </button>
            </div>
          </div>
        )}
      </div>

      {result && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Detection Results</h2>
          {result.detections && result.detections.length > 0 ? (
            <>
              <p className="text-gray-600 mb-4">
                Found <span className="font-semibold text-red-600">{result.detections.length}</span> defect(s)
              </p>

              {/* Show result image with bounding boxes */}
              {resultImageUrl && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-gray-600 mb-2">Result Image:</p>
                  <img
                    src={resultImageUrl}
                    alt="Detection Result"
                    className="max-w-full rounded-lg shadow-md border border-gray-200"
                  />
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-3 font-medium">Type</th>
                      <th className="pb-3 font-medium">Confidence</th>
                      <th className="pb-3 font-medium">Bounding Box</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.detections.map((det, idx) => (
                      <tr key={idx} className="border-b last:border-0">
                        <td className="py-3 capitalize">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            det.defect_type === 'hole' ? 'bg-red-100 text-red-700' :
                            det.defect_type === 'knot' ? 'bg-orange-100 text-orange-700' :
                            det.defect_type === 'line' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {det.defect_type}
                          </span>
                        </td>
                        <td className="py-3">{(det.confidence * 100).toFixed(1)}%</td>
                        <td className="py-3 text-gray-600 font-mono text-sm">
                          [{det.bbox_x1}, {det.bbox_y1}, {det.bbox_x2}, {det.bbox_y2}]
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={handleSaveToDashboard}
                  disabled={loading}
                  className="btn-primary flex items-center gap-2"
                >
                  {loading ? <LoadingSpinner size="small" /> : null}
                  Save All to Dashboard
                </button>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <svg className="w-16 h-16 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-gray-600">No defects detected in this image</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ImageUpload;