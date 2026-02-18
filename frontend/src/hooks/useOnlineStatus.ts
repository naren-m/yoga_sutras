import { useState, useEffect, useCallback, useRef } from 'react';

interface OnlineStatusResult {
  isOnline: boolean;
  showBackOnline: boolean;
}

/**
 * Hook to track online/offline status and "back online" transition.
 * Uses the Navigator.onLine API and listens for online/offline events.
 */
export function useOnlineStatus(): OnlineStatusResult {
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [showBackOnline, setShowBackOnline] = useState(false);

  // Use ref for wasOffline since we only need to read it in event callbacks
  const wasOfflineRef = useRef(false);

  // Handler for going online
  const handleOnline = useCallback(() => {
    setIsOnline(true);
    // If we were offline, show the "back online" message
    if (wasOfflineRef.current) {
      setShowBackOnline(true);
      wasOfflineRef.current = false;
      // Auto-hide after 3 seconds
      setTimeout(() => setShowBackOnline(false), 3000);
    }
  }, []);

  // Handler for going offline
  const handleOffline = useCallback(() => {
    setIsOnline(false);
    wasOfflineRef.current = true;
  }, []);

  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline]);

  return { isOnline, showBackOnline };
}
