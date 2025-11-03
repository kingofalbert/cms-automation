/**
 * useWebSocket Hook
 *
 * Custom React hook for WebSocket connections with automatic reconnection,
 * heartbeat, and event handling.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketMessage } from '../types/api';

export interface UseWebSocketOptions {
  /**
   * WebSocket URL
   */
  url: string;

  /**
   * Whether to connect immediately
   * @default true
   */
  enabled?: boolean;

  /**
   * Reconnect automatically on disconnect
   * @default true
   */
  autoReconnect?: boolean;

  /**
   * Reconnect delay in milliseconds
   * @default 3000
   */
  reconnectDelay?: number;

  /**
   * Maximum reconnection attempts
   * @default 5
   */
  maxReconnectAttempts?: number;

  /**
   * Heartbeat interval in milliseconds (0 to disable)
   * @default 30000
   */
  heartbeatInterval?: number;

  /**
   * Message handler
   */
  onMessage?: (data: WebSocketMessage) => void;

  /**
   * Connection opened handler
   */
  onOpen?: () => void;

  /**
   * Connection closed handler
   */
  onClose?: () => void;

  /**
   * Error handler
   */
  onError?: (error: Event) => void;

  /**
   * Reconnection attempt handler
   */
  onReconnect?: (attempt: number) => void;
}

export interface UseWebSocketReturn {
  /**
   * WebSocket connection state
   */
  state: 'connecting' | 'connected' | 'disconnected' | 'error';

  /**
   * Send a message through WebSocket
   */
  send: (data: any) => void;

  /**
   * Manually connect
   */
  connect: () => void;

  /**
   * Manually disconnect
   */
  disconnect: () => void;

  /**
   * Current reconnection attempt count
   */
  reconnectAttempts: number;

  /**
   * Whether WebSocket is currently connected
   */
  isConnected: boolean;
}

/**
 * Hook for managing WebSocket connections with automatic reconnection.
 *
 * @example
 * ```tsx
 * function TaskMonitor() {
 *   const { state, isConnected, send } = useWebSocket({
 *     url: 'ws://localhost:8000/ws/tasks',
 *     onMessage: (message) => {
 *       if (message.type === 'task_update') {
 *         updateTask(message.data);
 *       }
 *     },
 *   });
 *
 *   return (
 *     <div>
 *       Status: {state}
 *       <Button onClick={() => send({ action: 'subscribe', topic: 'tasks' })}>
 *         Subscribe
 *       </Button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    enabled = true,
    autoReconnect = true,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    onMessage,
    onOpen,
    onClose,
    onError,
    onReconnect,
  } = options;

  const [state, setState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>(
    'disconnected'
  );
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const optionsRef = useRef(options);

  // Keep options ref in sync
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  /**
   * Clear heartbeat interval
   */
  const clearHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  /**
   * Start heartbeat
   */
  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval <= 0) return;

    clearHeartbeat();

    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval, clearHeartbeat]);

  /**
   * Send data through WebSocket
   */
  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      wsRef.current.send(message);
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  }, []);

  /**
   * Attempt to reconnect
   */
  const attemptReconnect = useCallback(() => {
    if (!autoReconnect) return;
    if (reconnectAttempts >= maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      setState('error');
      return;
    }

    setReconnectAttempts((prev) => prev + 1);
    onReconnect?.(reconnectAttempts + 1);

    reconnectTimeoutRef.current = setTimeout(() => {
      console.log(`Reconnection attempt ${reconnectAttempts + 1}/${maxReconnectAttempts}`);
      connect();
    }, reconnectDelay);
  }, [autoReconnect, reconnectAttempts, maxReconnectAttempts, reconnectDelay, onReconnect]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState('connecting');

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setState('connected');
        setReconnectAttempts(0);
        startHeartbeat();
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketMessage;

          // Ignore pong messages
          if (data.type === 'pong') return;

          onMessage?.(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setState('disconnected');
        clearHeartbeat();
        onClose?.();

        // Attempt reconnection
        if (autoReconnect) {
          attemptReconnect();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState('error');
        onError?.(error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setState('error');
    }
  }, [url, startHeartbeat, onOpen, onMessage, onClose, onError, autoReconnect, attemptReconnect, clearHeartbeat]);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear heartbeat
    clearHeartbeat();

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState('disconnected');
    setReconnectAttempts(0);
  }, [clearHeartbeat]);

  /**
   * Connect on mount if enabled
   */
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled]); // Only run on mount/unmount and when enabled changes

  const isConnected = state === 'connected';

  return {
    state,
    send,
    connect,
    disconnect,
    reconnectAttempts,
    isConnected,
  };
}

/**
 * Hook for subscribing to specific WebSocket topics/channels.
 *
 * @example
 * ```tsx
 * function TaskUpdates({ taskId }: { taskId: string }) {
 *   const [task, setTask] = useState(null);
 *
 *   useWebSocketSubscription({
 *     url: 'ws://localhost:8000/ws',
 *     topic: `task:${taskId}`,
 *     onMessage: (message) => {
 *       if (message.type === 'task_update') {
 *         setTask(message.data);
 *       }
 *     },
 *   });
 *
 *   return <div>Task Status: {task?.status}</div>;
 * }
 * ```
 */
export function useWebSocketSubscription(options: UseWebSocketOptions & { topic?: string }) {
  const { topic, onMessage, ...wsOptions } = options;

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      onMessage?.(message);
    },
    [onMessage]
  );

  const ws = useWebSocket({
    ...wsOptions,
    onMessage: handleMessage,
    onOpen: () => {
      // Subscribe to topic when connected
      if (topic) {
        ws.send({ action: 'subscribe', topic });
      }
      wsOptions.onOpen?.();
    },
  });

  // Unsubscribe on unmount
  useEffect(() => {
    return () => {
      if (topic && ws.isConnected) {
        ws.send({ action: 'unsubscribe', topic });
      }
    };
  }, [topic, ws]);

  return ws;
}
