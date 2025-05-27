import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, Activity, Play, Square } from 'lucide-react';

const HttpPoseAnalysis = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sessionId] = useState(`http_demo_${Date.now()}`);
  const [currentRom, setCurrentRom] = useState(null);
  const [bodyPart, setBodyPart] = useState('lower_back');
  const [movementType, setMovementType] = useState('flexion');
  const [fps, setFps] = useState(0);
  const [error, setError] = useState(null);
  const [poseData, setPoseData] = useState(null);
  const [isVideoReady, setIsVideoReady] = useState(false);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const animationRef = useRef(null);
  const analyzeIntervalRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastFpsTimeRef = useRef(Date.now());

  // Skeleton connections
  const skeletonConnections = [
    ['LShoulder', 'RShoulder'],
    ['LShoulder', 'LElbow'],
    ['LElbow', 'LWrist'],
    ['RShoulder', 'RElbow'],
    ['RElbow', 'RWrist'],
    ['LShoulder', 'LHip'],
    ['RShoulder', 'RHip'],
    ['LHip', 'RHip'],
    ['LHip', 'LKnee'],
    ['LKnee', 'LAnkle'],
    ['RHip', 'RKnee'],
    ['RKnee', 'RAnkle'],
    ['Neck', 'Hip'],
    ['Neck', 'Head']
  ];

  // Initialize camera
  useEffect(() => {
    const initCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            width: { ideal: 640 },
            height: { ideal: 480 }
          } 
        });
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          
          videoRef.current.onloadedmetadata = () => {
            videoRef.current.play();
            
            // Set canvas dimensions to match video
            const videoWidth = videoRef.current.videoWidth;
            const videoHeight = videoRef.current.videoHeight;
            
            if (canvasRef.current) {
              canvasRef.current.width = videoWidth;
              canvasRef.current.height = videoHeight;
            }
            if (overlayCanvasRef.current) {
              overlayCanvasRef.current.width = videoWidth;
              overlayCanvasRef.current.height = videoHeight;
            }
            
            console.log('Video initialized:', videoWidth, 'x', videoHeight);
            setIsVideoReady(true);
          };
        }
      } catch (err) {
        setError('Failed to access camera. Please allow camera permissions.');
        console.error('Camera error:', err);
      }
    };

    initCamera();

    return () => {
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  // Draw video to canvas continuously
  useEffect(() => {
    if (!isVideoReady) return;

    const drawVideo = () => {
      if (videoRef.current && canvasRef.current && !isAnalyzing) {
        const ctx = canvasRef.current.getContext('2d');
        ctx.drawImage(
          videoRef.current, 
          0, 0, 
          canvasRef.current.width, 
          canvasRef.current.height
        );
      }
      animationRef.current = requestAnimationFrame(drawVideo);
    };

    drawVideo();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isVideoReady, isAnalyzing]);

  // Draw skeleton on overlay
  const drawSkeleton = useCallback((keypoints, angles) => {
    const canvas = overlayCanvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!keypoints || Object.keys(keypoints).length === 0) return;

    // Draw skeleton connections
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;
    
    skeletonConnections.forEach(([start, end]) => {
      if (keypoints[start] && keypoints[end]) {
        ctx.beginPath();
        ctx.moveTo(keypoints[start].x, keypoints[start].y);
        ctx.lineTo(keypoints[end].x, keypoints[end].y);
        ctx.stroke();
      }
    });

    // Draw keypoints
    ctx.fillStyle = '#ff0000';
    Object.entries(keypoints).forEach(([name, point]) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Draw ROM info
    if (currentRom) {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
      ctx.fillRect(10, 10, 250, 100);
      
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 20px Arial';
      ctx.fillText(`ROM: ${currentRom.current.toFixed(1)}°`, 20, 40);
      ctx.font = '16px Arial';
      ctx.fillText(`Range: ${currentRom.min.toFixed(1)}° - ${currentRom.max.toFixed(1)}°`, 20, 70);
      ctx.fillText(`Total: ${currentRom.range.toFixed(1)}°`, 20, 95);
    }

    // Draw angle for lower back
    if (bodyPart === 'lower_back' && angles?.trunk !== undefined) {
      const neck = keypoints.Neck;
      const hip = keypoints.Hip;
      
      if (neck && hip) {
        ctx.strokeStyle = '#00ffff';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(neck.x, neck.y);
        ctx.lineTo(hip.x, hip.y);
        ctx.stroke();
        
        const midX = (neck.x + hip.x) / 2;
        const midY = (neck.y + hip.y) / 2;
        ctx.fillStyle = '#00ffff';
        ctx.font = 'bold 24px Arial';
        ctx.fillText(`${angles.trunk.toFixed(1)}°`, midX + 20, midY);
      }
    }
  }, [currentRom, bodyPart]);

  // Analyze single frame
  const analyzeSingleFrame = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || !isVideoReady) {
      console.log('Not ready to analyze');
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Draw current video frame
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    
    // Convert to blob
    return new Promise((resolve) => {
      canvas.toBlob(async (blob) => {
        if (!blob) {
          console.error('Failed to create blob');
          resolve(null);
          return;
        }

        const formData = new FormData();
        formData.append('file', blob, 'frame.jpg');
        formData.append('session_id', sessionId);
        formData.append('body_part', bodyPart);
        formData.append('movement_type', movementType);
        formData.append('include_keypoints', 'true');

        try {
          const startTime = Date.now();
          const response = await fetch('http://localhost:8000/api/v1/analyze/frame', {
            method: 'POST',
            body: formData
          });

          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
          }

          const result = await response.json();
          const processingTime = Date.now() - startTime;
          
          console.log('Analysis result:', result);
          
          // Update FPS
          frameCountRef.current++;
          const now = Date.now();
          if (now - lastFpsTimeRef.current >= 1000) {
            setFps(frameCountRef.current);
            frameCountRef.current = 0;
            lastFpsTimeRef.current = now;
          }
          
          if (result.rom) {
            setCurrentRom(result.rom);
          }
          
          if (result.pose_detected) {
            setPoseData({
              angles: result.angles,
              confidence: result.pose_confidence,
              validation: result.validation
            });
            
            if (result.keypoints) {
              drawSkeleton(result.keypoints, result.angles);
            }
          } else {
            // Clear overlay and show message
            const overlayCanvas = overlayCanvasRef.current;
            if (overlayCanvas) {
              const overlayCtx = overlayCanvas.getContext('2d');
              overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
              
              overlayCtx.fillStyle = 'rgba(255, 0, 0, 0.8)';
              overlayCtx.font = 'bold 24px Arial';
              overlayCtx.textAlign = 'center';
              overlayCtx.fillText('No pose detected', overlayCanvas.width / 2, overlayCanvas.height / 2);
              overlayCtx.textAlign = 'left';
            }
          }
          
          setError(null);
          resolve(result);
        } catch (error) {
          console.error('Analysis error:', error);
          setError(`Analysis failed: ${error.message}`);
          resolve(null);
        }
      }, 'image/jpeg', 0.9);
    });
  }, [sessionId, bodyPart, movementType, drawSkeleton, isVideoReady]);

  // Continuous analysis loop
  useEffect(() => {
    if (!isAnalyzing) {
      if (analyzeIntervalRef.current) {
        clearInterval(analyzeIntervalRef.current);
        analyzeIntervalRef.current = null;
      }
      return;
    }

    const analyzeLoop = () => {
      analyzeSingleFrame();
    };

    // Start analyzing every 100ms (10 FPS)
    analyzeIntervalRef.current = setInterval(analyzeLoop, 100);

    return () => {
      if (analyzeIntervalRef.current) {
        clearInterval(analyzeIntervalRef.current);
      }
    };
  }, [isAnalyzing, analyzeSingleFrame]);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 flex items-center gap-2">
          <Activity className="w-8 h-8" />
          HTTP-based ROM Analysis
        </h1>
        
        {error && (
          <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 mb-4">
            {error}
          </div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Display */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="relative">
                <video 
                  ref={videoRef} 
                  autoPlay 
                  playsInline
                  muted
                  style={{ display: 'none' }}
                />
                <canvas 
                  ref={canvasRef} 
                  className="w-full bg-black rounded-lg"
                  style={{ maxWidth: '640px', maxHeight: '480px' }}
                />
                <canvas
                  ref={overlayCanvasRef}
                  className="absolute top-0 left-0 w-full rounded-lg"
                  style={{ maxWidth: '640px', maxHeight: '480px', pointerEvents: 'none' }}
                />
                
                {/* Status overlay */}
                <div className="absolute top-2 right-2 bg-black/70 px-2 py-1 rounded text-sm">
                  {isVideoReady ? (
                    isAnalyzing ? `${fps} FPS` : 'Ready'
                  ) : 'Loading camera...'}
                </div>
              </div>
            </div>
          </div>
          
          {/* Controls */}
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <h2 className="text-xl font-semibold mb-3">Analysis Controls</h2>
              
              <div className="space-y-2">
                <button
                  onClick={analyzeSingleFrame}
                  className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
                  disabled={isAnalyzing || !isVideoReady}
                >
                  <Camera className="w-4 h-4" />
                  Analyze Single Frame
                </button>
                
                <button
                  onClick={() => setIsAnalyzing(!isAnalyzing)}
                  className={`w-full py-2 px-4 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 ${
                    isAnalyzing 
                      ? 'bg-red-600 hover:bg-red-700' 
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                  disabled={!isVideoReady}
                >
                  {isAnalyzing ? (
                    <><Square className="w-4 h-4" /> Stop Continuous</>
                  ) : (
                    <><Play className="w-4 h-4" /> Start Continuous</>
                  )}
                </button>
              </div>
            </div>
            
            {/* Movement Settings */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h2 className="text-xl font-semibold mb-3">Movement Settings</h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Body Part</label>
                  <select
                    value={bodyPart}
                    onChange={(e) => setBodyPart(e.target.value)}
                    className="w-full bg-gray-700 rounded px-3 py-2"
                    disabled={isAnalyzing}
                  >
                    <option value="lower_back">Lower Back</option>
                    <option value="shoulder">Shoulder</option>
                    <option value="elbow">Elbow</option>
                    <option value="hip">Hip</option>
                    <option value="knee">Knee</option>
                    <option value="ankle">Ankle</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Movement Type</label>
                  <select
                    value={movementType}
                    onChange={(e) => setMovementType(e.target.value)}
                    className="w-full bg-gray-700 rounded px-3 py-2"
                    disabled={isAnalyzing}
                  >
                    <option value="flexion">Flexion</option>
                    <option value="extension">Extension</option>
                    <option value="lateral_flexion">Lateral Flexion</option>
                    <option value="rotation">Rotation</option>
                  </select>
                </div>
              </div>
            </div>
            
            {/* ROM Display */}
            {currentRom && (
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-xl font-semibold mb-3">ROM Analysis</h2>
                <div className="space-y-2">
                  <div className="flex justify-between items-baseline">
                    <span>Current:</span>
                    <span className="font-bold text-3xl text-green-400">
                      {currentRom.current.toFixed(1)}°
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Min:</span>
                    <span className="text-lg">{currentRom.min.toFixed(1)}°</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Max:</span>
                    <span className="text-lg">{currentRom.max.toFixed(1)}°</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Range:</span>
                    <span className="font-semibold text-xl text-blue-400">
                      {currentRom.range.toFixed(1)}°
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Pose Info */}
            {poseData && (
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-xl font-semibold mb-3">Pose Detection</h2>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Confidence:</span>
                    <span className={poseData.confidence > 0.7 ? 'text-green-400' : 'text-yellow-400'}>
                      {(poseData.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  {poseData.validation && (
                    <div className="text-xs mt-2 p-2 bg-gray-700 rounded">
                      {poseData.validation.message}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HttpPoseAnalysis;