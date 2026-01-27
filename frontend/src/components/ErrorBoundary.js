/**
 * Error Boundary Component
 * Production Hardening - Days 9-10: Error Recovery & Resilience
 * 
 * Catches React errors and displays fallback UI instead of crashing the entire app
 */

import React from 'react';
import { captureException } from '../utils/sentry';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    // Send to Sentry if configured
    captureException(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: true,
    });
    
    // Update state with error details
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    // Reset error state
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    
    // Reload page as fallback
    if (this.props.onReset) {
      this.props.onReset();
    } else {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback({
          error: this.state.error,
          reset: this.handleReset,
        });
      }

      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center px-4" style={{ background: '#0B101B' }}>
          <div 
            className="max-w-md w-full rounded-2xl p-8"
            style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
          >
            <div className="text-center">
              <div className="text-6xl mb-4">😕</div>
              <h1 className="text-2xl font-bold text-white mb-2">
                Oops! Something went wrong
              </h1>
              <p className="text-white/60 mb-6">
                We're sorry, but something unexpected happened. The error has been reported and we'll fix it as soon as possible.
              </p>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mb-6 text-left">
                  <summary className="cursor-pointer text-sm text-white/40 hover:text-white/60 mb-2">
                    Error Details (Development Only)
                  </summary>
                  <div 
                    className="p-4 rounded-xl text-xs overflow-auto max-h-48"
                    style={{ background: 'rgba(0, 0, 0, 0.3)' }}
                  >
                    <p className="font-mono text-[#EF4444] mb-2">
                      {this.state.error.toString()}
                    </p>
                    {this.state.errorInfo && (
                      <pre className="text-white/60 whitespace-pre-wrap">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    )}
                  </div>
                </details>
              )}
              
              <div className="space-y-3">
                <button
                  onClick={() => window.location.href = '/'}
                  className="w-full px-6 py-3 rounded-xl transition-colors font-medium"
                  style={{ background: '#00F0FF', color: '#0B101B' }}
                >
                  Return to Home
                </button>
                
                <button
                  onClick={() => window.location.href = '/app/my-competitions'}
                  className="w-full px-6 py-3 rounded-xl transition-colors font-medium"
                  style={{ background: '#10B981', color: 'white' }}
                >
                  Go to My Competitions
                </button>
                
                <button
                  onClick={this.handleReset}
                  className="w-full px-6 py-3 rounded-xl transition-colors font-medium"
                  style={{ background: 'rgba(255, 255, 255, 0.1)', color: 'white' }}
                >
                  Reload This Page
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Hook-based error boundary wrapper
 * Usage: const ErrorFallback = useErrorBoundary();
 */
export const useErrorBoundary = () => {
  const [error, setError] = React.useState(null);
  
  const resetError = () => setError(null);
  
  if (error) {
    throw error;
  }
  
  return { setError, resetError };
};

/**
 * Higher-order component to wrap components with error boundary
 * Usage: export default withErrorBoundary(MyComponent);
 */
export const withErrorBoundary = (Component, fallback) => {
  return function WrappedComponent(props) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
};

export default ErrorBoundary;
