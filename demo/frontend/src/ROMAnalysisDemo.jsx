import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, Activity, Wifi, WifiOff, AlertCircle, ChevronDown, ChevronUp, Copy } from 'lucide-react';

const ROMAnalysisDemo = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId] = useState(`demo_${Date.now()}`);
  const [bodyPart, setBodyPart] = useState('lower_back');
  const [movementType, setMovementType] = useState('flexion');
  const [romData, setRomData] = useState(null);
  const [poseData, setPoseData] = useState(null);
  const [error, setError] = useState(null);
  const [fps, setFps] = useState(0);
  const [processingTime, setProcessingTime] = useState(0);
  const [showJsonOutput, setShowJsonOutput] = useState(true);
  const [lastJsonResponse, setLastJsonResponse] = useState(null);
  const [framesSent, setFramesSent] = useState(0);
  const [framesReceived, setFramesReceived] = useState(0);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const wsRef = useRef(null);
  const streamRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastFpsTimeRef = useRef(Date.now());
  const sendTimestamps = useRef(new Map());

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
    ['Neck', 'Head'],
    ['LAnkle', 'LBigToe'],
    ['RAnkle', 'RBigToe']
  ];

  // Movement-specific colors
  const movementColors = {
    lower_back: { primary: '#00ffff', secondary: '#0088ff' },
    shoulder: { primary: '#ff00ff', secondary: '#ff0088' },
    elbow: { primary: '#ffff00', secondary: '#ff8800' },
    hip: { primary: '#00ff00', secondary: '#00ff88' },
    knee: { primary: '#ff8888', secondary: '#ff4444' },
    ankle: { primary: '#88ff88', secondary: '#44ff44' }
  };

  // Initialize camera
  useEffect(() => {
    const initCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { width: 640, height: 480 } 
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          streamRef.current = stream;
          
          // Wait for video to be ready
          videoRef.current.onloadedmetadata = () => {
            console.log('Video ready:', videoRef.current.videoWidth, 'x', videoRef.current.videoHeight);
            
            // Set canvas dimensions to match video
            if (canvasRef.current && overlayCanvasRef.current) {
              canvasRef.current.width = videoRef.current.videoWidth;
              canvasRef.current.height = videoRef.current.videoHeight;
              overlayCanvasRef.current.width = videoRef.current.videoWidth;
              overlayCanvasRef.current.height = videoRef.current.videoHeight;
            }
          };
        }
      } catch (err) {
        setError('Failed to access camera. Please allow camera permissions.');
        console.error('Camera error:', err);
      }
    };

    initCamera();

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Copy JSON to clipboard
  const copyJsonToClipboard = () => {
    if (lastJsonResponse) {
      navigator.clipboard.writeText(JSON.stringify(lastJsonResponse, null, 2));
    }
  };

  // Draw skeleton on canvas with ROM visualization
  const drawSkeleton = useCallback((keypoints, angles) => {
    const canvas = overlayCanvasRef.current;
    const ctx = canvas.getContext('2d');
    const video = videoRef.current;

    if (!canvas || !ctx || !video) return;

    // Clear overlay
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!keypoints || Object.keys(keypoints).length === 0) return;

    const colors = movementColors[bodyPart];

    // Draw skeleton connections
    ctx.strokeStyle = 'rgba(0, 255, 0, 0.6)';
    ctx.lineWidth = 2;
    
    skeletonConnections.forEach(([start, end]) => {
      if (keypoints[start] && keypoints[end]) {
        ctx.beginPath();
        ctx.moveTo(keypoints[start].x, keypoints[start].y);
        ctx.lineTo(keypoints[end].x, keypoints[end].y);
        ctx.stroke();
      }
    });

    // Highlight movement-specific connections
    if (bodyPart === 'lower_back' && keypoints.Neck && keypoints.Hip) {
      ctx.strokeStyle = colors.primary;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(keypoints.Neck.x, keypoints.Neck.y);
      ctx.lineTo(keypoints.Hip.x, keypoints.Hip.y);
      ctx.stroke();
    }

    // Draw keypoints
    ctx.fillStyle = '#ff0000';
    Object.entries(keypoints).forEach(([name, point]) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Draw angle visualization
    if (angles) {
      drawAngleVisualization(ctx, keypoints, angles, colors);
    }

    // Draw ROM overlay
    if (romData) {
      // ROM info box
      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
      ctx.fillRect(10, 10, 280, 140);
      
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 20px Arial';
      ctx.fillText(`ROM: ${romData.current.toFixed(1)}°`, 20, 40);
      
      ctx.font = '16px Arial';
      ctx.fillText(`Range: ${romData.min.toFixed(1)}° - ${romData.max.toFixed(1)}°`, 20, 70);
      ctx.fillText(`Total: ${romData.range.toFixed(1)}°`, 20, 95);
      
      // Visual ROM indicator
      const normalRange = getNormalRange();
      const isNormal = romData.current >= normalRange[0] && romData.current <= normalRange[1];
      
      ctx.fillStyle = isNormal ? '#00ff00' : '#ff9900';
      ctx.fillRect(20, 110, 250, 20);
      
      // Current position marker
      const rangeWidth = 250;
      const normalizedPos = (romData.current - normalRange[0]) / (normalRange[1] - normalRange[0]);
      const markerX = 20 + Math.max(0, Math.min(rangeWidth, normalizedPos * rangeWidth));
      
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.moveTo(markerX, 105);
      ctx.lineTo(markerX - 5, 110);
      ctx.lineTo(markerX + 5, 110);
      ctx.fill();
    }

    // Performance indicator
    ctx.fillStyle = processingTime > 100 ? '#ff0000' : '#00ff00';
    ctx.font = '12px Arial';
    ctx.fillText(`Processing: ${processingTime}ms`, canvas.width - 120, 20);
  }, [romData, bodyPart, processingTime]);

  // Draw angle visualization with arcs
  const drawAngleVisualization = (ctx, keypoints, angles, colors) => {
    ctx.save();
    
    // Lower back flexion
    if (bodyPart === 'lower_back' && angles.trunk !== undefined) {
      const neck = keypoints.Neck;
      const hip = keypoints.Hip;
      
      if (neck && hip) {
        // Draw angle arc
        const midX = (neck.x + hip.x) / 2;
        const midY = (neck.y + hip.y) / 2;
        
        ctx.strokeStyle = colors.primary;
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        // Draw arc showing angle
        const radius = 60;
        const startAngle = -Math.PI / 2; // Vertical
        const endAngle = startAngle + (angles.trunk * Math.PI / 180);
        
        ctx.arc(midX, midY, radius, startAngle, endAngle);
        ctx.stroke();
        
        // Angle text
        ctx.fillStyle = colors.primary;
        ctx.font = 'bold 24px Arial';
        ctx.shadowColor = 'black';
        ctx.shadowBlur = 4;
        ctx.fillText(`${angles.trunk.toFixed(1)}°`, midX + 70, midY);
      }
    }
    
    // Elbow flexion
    if (bodyPart === 'elbow' && angles.elbow !== undefined) {
      const shoulder = keypoints.RShoulder;
      const elbow = keypoints.RElbow;
      const wrist = keypoints.RWrist;
      
      if (shoulder && elbow && wrist) {
        ctx.strokeStyle = colors.primary;
        ctx.lineWidth = 3;
        
        // Highlight arm segments
        ctx.beginPath();
        ctx.moveTo(shoulder.x, shoulder.y);
        ctx.lineTo(elbow.x, elbow.y);
        ctx.lineTo(wrist.x, wrist.y);
        ctx.stroke();
        
        // Draw angle at elbow
        ctx.fillStyle = colors.primary;
        ctx.font = 'bold 20px Arial';
        ctx.fillText(`${angles.elbow.toFixed(1)}°`, elbow.x + 20, elbow.y - 20);
      }
    }
    
    ctx.restore();
  };

  // Get normal range for current movement
  const getNormalRange = () => {
    const ranges = {
      lower_back: {
        flexion: [0, 60],
        extension: [-30, 0],
        lateral_flexion: [-30, 30],
        rotation: [-45, 45]
      },
      shoulder: {
        flexion: [0, 180],
        extension: [0, 60],
        abduction: [0, 180],
        adduction: [0, 45]
      },
      elbow: {
        flexion: [0, 145],
        extension: [0, 10]
      },
      hip: {
        flexion: [0, 120],
        extension: [0, 30],
        abduction: [0, 45]
      },
      knee: {
        flexion: [0, 135],
        extension: [0, 10]
      },
      ankle: {
        dorsiflexion: [0, 20],
        plantarflexion: [0, 50]
      }
    };

    return ranges[bodyPart]?.[movementType] || [0, 90];
  };

  // Capture and send frame
  const captureAndSendFrame = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const video = videoRef.current;
    
    // Ensure video is ready
    if (video.readyState !== video.HAVE_ENOUGH_DATA) {
      console.warn('Video not ready');
      return;
    }
    
    // Clear and draw video to canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Get image data for debugging
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const hasContent = imageData.data.some(pixel => pixel !== 0);
    
    if (!hasContent) {
      console.warn('Canvas appears to be empty');
      return;
    }
    
    // Convert to base64 with higher quality
    const frameData = canvas.toDataURL('image/jpeg', 0.9).split(',')[1];
    
    // Debug: Check frame data
    console.log('Sending frame:', {
      canvasSize: canvas.width + 'x' + canvas.height,
      dataLength: frameData.length,
      first50Chars: frameData.substring(0, 50)
    });
    
    // Track send timestamp
    const frameId = Date.now().toString();
    sendTimestamps.current.set(frameId, Date.now());
    
    // Send frame
    const message = {
      frame_base64: frameData,
      body_part: bodyPart,
      movement_type: movementType,
      include_keypoints: true,
      frame_id: frameId
    };
    
    wsRef.current.send(JSON.stringify(message));
    setFramesSent(prev => prev + 1);
    
    // Update FPS
    frameCountRef.current++;
    const now = Date.now();
    if (now - lastFpsTimeRef.current >= 1000) {
      setFps(frameCountRef.current);
      frameCountRef.current = 0;
      lastFpsTimeRef.current = now;
    }
  }, [bodyPart, movementType]);

  // Connect WebSocket
  const connectWebSocket = () => {
    const wsUrl = `ws://localhost:8000/ws/${sessionId}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        setIsConnected(true);
        setError(null);
        console.log('WebSocket connected');
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Calculate processing time if frame_id exists
          if (data.frame_id && sendTimestamps.current.has(data.frame_id)) {
            const sendTime = sendTimestamps.current.get(data.frame_id);
            const processingMs = Date.now() - sendTime;
            setProcessingTime(processingMs);
            sendTimestamps.current.delete(data.frame_id);
            
            // Clean old timestamps
            if (sendTimestamps.current.size > 100) {
              const entries = Array.from(sendTimestamps.current.entries());
              entries.slice(0, 50).forEach(([id]) => sendTimestamps.current.delete(id));
            }
          }
          
          setFramesReceived(prev => prev + 1);
          setLastJsonResponse(data);
          
          if (data.error) {
            setError(data.error);
            return;
          }
          
          // Update ROM data
          if (data.rom) {
            setRomData(data.rom);
          }
          
          // Update pose data
          if (data.pose_detected) {
            setPoseData({
              angles: data.angles,
              confidence: data.pose_confidence,
              validation: data.validation,
              guidance: data.guidance
            });
            
            // Draw skeleton if keypoints are included
            if (data.keypoints) {
              drawSkeleton(data.keypoints, data.angles);
            }
          } else {
            // Clear skeleton overlay
            const canvas = overlayCanvasRef.current;
            if (canvas) {
              const ctx = canvas.getContext('2d');
              ctx.clearRect(0, 0, canvas.width, canvas.height);
              
              // Show no pose message
              ctx.fillStyle = 'rgba(255, 0, 0, 0.8)';
              ctx.font = 'bold 24px Arial';
              ctx.textAlign = 'center';
              ctx.fillText('No pose detected', canvas.width / 2, canvas.height / 2);
              ctx.textAlign = 'left';
            }
          }
        } catch (err) {
          console.error('Failed to parse message:', err);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };
      
      wsRef.current.onclose = () => {
        setIsConnected(false);
        setIsStreaming(false);
        console.log('WebSocket disconnected');
      };
    } catch (err) {
      setError('Failed to connect to WebSocket');
      console.error(err);
    }
  };

  // Disconnect WebSocket
  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsStreaming(false);
    setFramesSent(0);
    setFramesReceived(0);
  };

  // Start streaming
  const startStreaming = () => {
    setIsStreaming(true);
    setFramesSent(0);
    setFramesReceived(0);
    
    let intervalId;
    
    // Wait a bit for video to stabilize
    setTimeout(() => {
      // Send frames at 10 FPS
      intervalId = setInterval(() => {
        if (!isStreaming || !isConnected) {
          clearInterval(intervalId);
          return;
        }
        captureAndSendFrame();
      }, 100);
    }, 500); // 500ms delay to ensure video is ready
  };

  // Stop streaming
  const stopStreaming = () => {
    setIsStreaming(false);
  };

  // Update video display
  useEffect(() => {
    const updateVideoCanvas = () => {
      if (!videoRef.current || !canvasRef.current) return;
      
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      
      if (!isStreaming) {
        requestAnimationFrame(updateVideoCanvas);
      }
    };
    
    if (!isStreaming) {
      updateVideoCanvas();
    }
  }, [isStreaming]);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 flex items-center gap-2">
          <Activity className="w-8 h-8" />
          ROM Analysis Live Demo
        </h1>
        
        {error && (
          <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video/Canvas Display */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="relative">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="w-full rounded-lg"
                  style={{ display: 'none' }}
                />
                <canvas
                  ref={canvasRef}
                  width={640}
                  height={480}
                  className="w-full rounded-lg bg-black"
                />
                <canvas
                  ref={overlayCanvasRef}
                  width={640}
                  height={480}
                  className="absolute top-0 left-0 w-full rounded-lg"
                  style={{ pointerEvents: 'none' }}
                />
                
                {/* Status Overlay */}
                <div className="absolute top-2 left-2 right-2 flex justify-between">
                  <div className="flex items-center gap-2 bg-black/70 px-2 py-1 rounded text-sm">
                    {isConnected ? (
                      <><Wifi className="w-4 h-4 text-green-500" /> Connected</>
                    ) : (
                      <><WifiOff className="w-4 h-4 text-red-500" /> Disconnected</>
                    )}
                  </div>
                  
                  {isStreaming && (
                    <div className="bg-black/70 px-2 py-1 rounded text-sm">
                      {fps} FPS | {processingTime}ms | Sent: {framesSent} | Received: {framesReceived}
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {/* JSON Output Panel */}
            <div className="bg-gray-800 rounded-lg p-4 mt-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  JSON Response
                  <button
                    onClick={() => setShowJsonOutput(!showJsonOutput)}
                    className="text-gray-400 hover:text-white"
                  >
                    {showJsonOutput ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </h3>
                <button
                  onClick={copyJsonToClipboard}
                  className="flex items-center gap-1 text-sm bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded"
                  disabled={!lastJsonResponse}
                >
                  <Copy className="w-4 h-4" /> Copy
                </button>
              </div>
              
              {showJsonOutput && (
                <pre className="bg-gray-900 p-3 rounded text-xs overflow-auto max-h-96">
                  {lastJsonResponse ? JSON.stringify(lastJsonResponse, null, 2) : 'No data yet...'}
                </pre>
              )}
            </div>
          </div>
          
          {/* Controls and Info */}
          <div className="space-y-4">
            {/* Connection Controls */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h2 className="text-xl font-semibold mb-3">Connection</h2>
              <div className="space-y-2">
                <button
                  onClick={isConnected ? disconnectWebSocket : connectWebSocket}
                  className={`w-full py-2 px-4 rounded-lg font-medium transition ${
                    isConnected 
                      ? 'bg-red-600 hover:bg-red-700' 
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {isConnected ? 'Disconnect' : 'Connect'}
                </button>
                
                {isConnected && (
                  <>
                    <button
                      onClick={isStreaming ? stopStreaming : startStreaming}
                      className={`w-full py-2 px-4 rounded-lg font-medium transition ${
                        isStreaming 
                          ? 'bg-yellow-600 hover:bg-yellow-700' 
                          : 'bg-blue-600 hover:bg-blue-700'
                      }`}
                    >
                      {isStreaming ? 'Stop Stream' : 'Start Stream'}
                    </button>
                    
                    <button
                      onClick={() => {
                        // Test single frame capture
                        const canvas = canvasRef.current;
                        const video = videoRef.current;
                        if (canvas && video) {
                          const ctx = canvas.getContext('2d');
                          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                          
                          // Save frame for inspection
                          canvas.toBlob((blob) => {
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'test_frame.jpg';
                            a.click();
                            URL.revokeObjectURL(url);
                          }, 'image/jpeg', 0.9);
                          
                          // Also send single frame
                          captureAndSendFrame();
                        }
                      }}
                      className="w-full py-2 px-4 rounded-lg font-medium bg-purple-600 hover:bg-purple-700 transition"
                      disabled={isStreaming}
                    >
                      Capture Test Frame
                    </button>
                  </>
                )}
              </div>
            </div>
            
            {/* Movement Selection */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h2 className="text-xl font-semibold mb-3">Movement Settings</h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Body Part</label>
                  <select
                    value={bodyPart}
                    onChange={(e) => setBodyPart(e.target.value)}
                    className="w-full bg-gray-700 rounded px-3 py-2"
                    disabled={isStreaming}
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
                    disabled={isStreaming}
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
            {romData && (
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-xl font-semibold mb-3">ROM Analysis</h2>
                <div className="space-y-2">
                  <div className="flex justify-between items-baseline">
                    <span>Current:</span>
                    <span className="font-bold text-3xl text-green-400">
                      {romData.current.toFixed(1)}°
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Min:</span>
                    <span className="text-lg">{romData.min.toFixed(1)}°</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Max:</span>
                    <span className="text-lg">{romData.max.toFixed(1)}°</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Range:</span>
                    <span className="font-semibold text-xl text-blue-400">
                      {romData.range.toFixed(1)}°
                    </span>
                  </div>
                  
                  {/* Visual range indicator */}
                  <div className="mt-3">
                    <div className="bg-gray-700 h-4 rounded-full overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-green-500 h-full transition-all duration-300"
                        style={{ width: `${(romData.range / 180) * 100}%` }}
                      />
                    </div>
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
                  
                  {poseData.angles && (
                    <div className="mt-2">
                      <div className="text-xs font-medium mb-1">Detected Angles:</div>
                      {Object.entries(poseData.angles).map(([angle, value]) => (
                        <div key={angle} className="flex justify-between text-xs">
                          <span className="text-gray-400">{angle}:</span>
                          <span>{value.toFixed(1)}°</span>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {poseData.validation && (
                    <div className={`text-xs mt-2 p-2 rounded ${
                      poseData.validation.in_normal_range 
                        ? 'bg-green-900/50 text-green-300' 
                        : 'bg-yellow-900/50 text-yellow-300'
                    }`}>
                      {poseData.validation.message}
                    </div>
                  )}
                  
                  {poseData.guidance && (
                    <div className="text-xs mt-2 p-2 bg-blue-900/50 rounded">
                      <div className="font-medium">Guidance:</div>
                      <div>{poseData.guidance.instruction}</div>
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

export default ROMAnalysisDemo;