/**
 * Debug Footer Badge
 * Shows build info for quick sanity checks in development ONLY
 * Hidden in production to keep the UI clean for end users
 */
import { useState } from 'react';

const DebugFooter = () => {
  const [expanded, setExpanded] = useState(false);
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'NOT SET';
  const socketPath = '/api/socket.io';
  const buildHash = process.env.REACT_APP_BUILD_HASH || 'dev';
  const nodeEnv = process.env.NODE_ENV || 'development';

  // Hide debug footer in production
  if (nodeEnv === 'production') {
    return null;
  }

  return (
    <div
      className="fixed bottom-2 left-2 z-50 text-xs font-mono"
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      <div
        className={`
          bg-gray-800 text-gray-100 rounded-lg shadow-lg border border-gray-700
          transition-all duration-200 ease-in-out
          ${expanded ? 'px-3 py-2' : 'px-2 py-1'}
        `}
      >
        {!expanded ? (
          <div className="flex items-center gap-1">
            <span className="text-green-400">●</span>
            <span className="text-gray-400">FE</span>
          </div>
        ) : (
          <div className="space-y-1">
            <div className="flex items-center gap-2 border-b border-gray-700 pb-1 mb-1">
              <span className="text-green-400">●</span>
              <span className="font-semibold text-white">Frontend Info</span>
            </div>
            
            <div className="grid grid-cols-[80px_1fr] gap-x-2 gap-y-0.5">
              <span className="text-gray-400">Build:</span>
              <span className="text-blue-400 font-medium">{buildHash}</span>
              
              <span className="text-gray-400">Env:</span>
              <span className={nodeEnv === 'production' ? 'text-green-400' : 'text-yellow-400'}>
                {nodeEnv}
              </span>
              
              <span className="text-gray-400">Backend:</span>
              <span className="text-purple-400 break-all">{backendUrl}</span>
              
              <span className="text-gray-400">Socket:</span>
              <span className="text-cyan-400">{socketPath}</span>
            </div>
            
            <div className="text-gray-500 text-[10px] mt-1 pt-1 border-t border-gray-700">
              Hover to see details
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DebugFooter;
