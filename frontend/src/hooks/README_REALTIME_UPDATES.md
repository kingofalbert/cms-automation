# 實時更新機制使用指南

本項目提供了完整的實時更新機制，包括輪詢（Polling）和 WebSocket 兩種方式。

## 目錄

1. [Polling (輪詢)](#polling-輪詢)
2. [WebSocket](#websocket)
3. [AutoRefreshControl 組件](#autorefreshcontrol-組件)
4. [使用示例](#使用示例)
5. [最佳實踐](#最佳實踐)

## Polling (輪詢)

### usePolling Hook

基礎的輪詢 hook，可用於任何需要定期更新數據的場景。

#### 基本用法

```tsx
import { usePolling } from '@/hooks/usePolling';

function TaskList() {
  const [tasks, setTasks] = useState([]);

  const { isPolling, start, stop, toggle } = usePolling(
    async () => {
      const response = await fetch('/api/tasks');
      const data = await response.json();
      setTasks(data);
    },
    {
      interval: 5000,       // 每 5 秒輪詢一次
      enabled: true,        // 自動開始
      pollWhenHidden: false, // 標籤頁隱藏時停止
      maxErrors: 3,         // 連續錯誤 3 次後停止
    }
  );

  return (
    <div>
      <button onClick={toggle}>
        {isPolling ? '停止自動刷新' : '開始自動刷新'}
      </button>
      <TaskTable data={tasks} />
    </div>
  );
}
```

#### 配置選項

| 選項 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| `interval` | number | 5000 | 輪詢間隔（毫秒） |
| `enabled` | boolean | true | 是否立即開始輪詢 |
| `pollWhenHidden` | boolean | false | 標籤頁隱藏時是否繼續輪詢 |
| `maxErrors` | number | 3 | 最大連續錯誤次數 |
| `onMaxErrors` | function | - | 達到最大錯誤次數的回調 |
| `pollOnMount` | boolean | true | 掛載時是否立即輪詢 |

#### 返回值

| 屬性 | 類型 | 說明 |
|------|------|------|
| `isPolling` | boolean | 當前是否正在輪詢 |
| `start` | function | 開始輪詢 |
| `stop` | function | 停止輪詢 |
| `toggle` | function | 切換輪詢狀態 |
| `poll` | function | 手動觸發一次輪詢 |
| `errorCount` | number | 連續錯誤次數 |
| `resetErrors` | function | 重置錯誤計數 |

### useQueryPolling Hook

與 React Query 集成的輪詢 hook。

```tsx
import { useQuery } from '@tanstack/react-query';
import { useQueryPolling } from '@/hooks/usePolling';

function TaskList() {
  const { data, refetch } = useQuery({
    queryKey: ['tasks'],
    queryFn: fetchTasks,
  });

  const { isPolling, toggle } = useQueryPolling(refetch, {
    interval: 5000,
    enabled: true,
  });

  return (
    <div>
      <button onClick={toggle}>
        {isPolling ? '停止' : '開始'} 自動刷新
      </button>
      {data && <TaskTable data={data} />}
    </div>
  );
}
```

## WebSocket

### useWebSocket Hook

用於建立 WebSocket 連接並處理實時消息。

#### 基本用法

```tsx
import { useWebSocket } from '@/hooks/useWebSocket';

function TaskMonitor() {
  const [tasks, setTasks] = useState({});

  const { state, isConnected, send } = useWebSocket({
    url: 'ws://localhost:8000/ws/tasks',
    enabled: true,
    autoReconnect: true,
    onMessage: (message) => {
      if (message.type === 'task_update') {
        setTasks(prev => ({
          ...prev,
          [message.data.task_id]: message.data
        }));
      }
    },
    onOpen: () => {
      console.log('WebSocket connected');
      // 訂閱特定主題
      send({ action: 'subscribe', topic: 'tasks' });
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  return (
    <div>
      <div>連接狀態: {state}</div>
      <TaskList tasks={Object.values(tasks)} />
    </div>
  );
}
```

#### 配置選項

| 選項 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| `url` | string | 必填 | WebSocket URL |
| `enabled` | boolean | true | 是否立即連接 |
| `autoReconnect` | boolean | true | 斷線自動重連 |
| `reconnectDelay` | number | 3000 | 重連延遲（毫秒） |
| `maxReconnectAttempts` | number | 5 | 最大重連次數 |
| `heartbeatInterval` | number | 30000 | 心跳間隔（0 禁用） |
| `onMessage` | function | - | 消息處理回調 |
| `onOpen` | function | - | 連接建立回調 |
| `onClose` | function | - | 連接關閉回調 |
| `onError` | function | - | 錯誤處理回調 |
| `onReconnect` | function | - | 重連嘗試回調 |

#### 返回值

| 屬性 | 類型 | 說明 |
|------|------|------|
| `state` | string | 連接狀態: 'connecting', 'connected', 'disconnected', 'error' |
| `send` | function | 發送消息 |
| `connect` | function | 手動連接 |
| `disconnect` | function | 手動斷開 |
| `reconnectAttempts` | number | 當前重連次數 |
| `isConnected` | boolean | 是否已連接 |

### useWebSocketSubscription Hook

訂閱特定主題的 WebSocket hook。

```tsx
import { useWebSocketSubscription } from '@/hooks/useWebSocket';

function TaskUpdates({ taskId }: { taskId: string }) {
  const [task, setTask] = useState(null);

  useWebSocketSubscription({
    url: 'ws://localhost:8000/ws',
    topic: `task:${taskId}`,
    onMessage: (message) => {
      if (message.type === 'task_update') {
        setTask(message.data);
      }
    },
  });

  return <TaskCard task={task} />;
}
```

## AutoRefreshControl 組件

可重用的自動刷新控制組件，提供開關和間隔選擇。

### 基本用法

```tsx
import AutoRefreshControl from '@/components/AutoRefreshControl';
import { useQuery } from '@tanstack/react-query';

function TasksPage() {
  const { data, refetch } = useQuery({
    queryKey: ['tasks'],
    queryFn: fetchTasks,
  });

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <AutoRefreshControl
          onRefresh={refetch}
          interval={5000}
          label="自動更新任務"
          defaultEnabled={true}
          showIntervalSelector={true}
          intervalOptions={[3000, 5000, 10000, 30000, 60000]}
        />
      </div>
      <TaskTable data={data} />
    </div>
  );
}
```

### 精簡版本

```tsx
import { AutoRefreshToggle } from '@/components/AutoRefreshControl';

function Toolbar() {
  const { refetch } = useQuery(['data'], fetchData);

  return (
    <div className="toolbar">
      <AutoRefreshToggle
        onRefresh={refetch}
        interval={5000}
        defaultEnabled={true}
      />
    </div>
  );
}
```

## 使用示例

### 示例 1: 任務監控頁面

```tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import AutoRefreshControl from '@/components/AutoRefreshControl';
import { publishingAPI } from '@/services';

function PublishTasksPage() {
  const [statusFilter, setStatusFilter] = useState('all');

  // 查詢任務列表
  const { data: tasks = [], refetch } = useQuery({
    queryKey: ['publish-tasks', statusFilter],
    queryFn: () => publishingAPI.list({ status: statusFilter }),
  });

  // 計算統計數據
  const stats = {
    total: tasks.length,
    running: tasks.filter(t => t.status === 'running').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
  };

  return (
    <div className="page">
      <div className="header">
        <h1>發布任務監控</h1>
        <AutoRefreshControl
          onRefresh={refetch}
          interval={3000}
          label="實時更新"
          defaultEnabled={true}
        />
      </div>

      <div className="stats">
        <StatCard title="總任務" value={stats.total} />
        <StatCard title="運行中" value={stats.running} color="blue" />
        <StatCard title="已完成" value={stats.completed} color="green" />
        <StatCard title="失敗" value={stats.failed} color="red" />
      </div>

      <TaskTable data={tasks} />
    </div>
  );
}
```

### 示例 2: Worklist 頁面

```tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import AutoRefreshControl from '@/components/AutoRefreshControl';
import { worklistAPI } from '@/services';

function WorklistPage() {
  const [filters, setFilters] = useState({ status: 'all', search: '' });

  // 查詢 worklist 項目
  const { data: items = [], refetch: refetchItems } = useQuery({
    queryKey: ['worklist', filters],
    queryFn: () => worklistAPI.list(filters),
  });

  // 查詢統計數據
  const { data: statistics, refetch: refetchStats } = useQuery({
    queryKey: ['worklist-statistics'],
    queryFn: () => worklistAPI.getStatistics(),
  });

  // 組合刷新函數
  const handleRefresh = async () => {
    await Promise.all([refetchItems(), refetchStats()]);
  };

  return (
    <div className="page">
      <div className="header">
        <h1>Worklist</h1>
        <AutoRefreshControl
          onRefresh={handleRefresh}
          interval={10000}
          label="自動同步"
          defaultEnabled={true}
          intervalOptions={[5000, 10000, 30000, 60000]}
        />
      </div>

      <WorklistStatistics data={statistics} />
      <WorklistTable data={items} />
    </div>
  );
}
```

### 示例 3: WebSocket 實時任務更新

```tsx
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWebSocket } from '@/hooks/useWebSocket';
import { publishingAPI } from '@/services';

function RealTimeTaskMonitor() {
  const [tasks, setTasks] = useState({});

  // 初始加載任務列表
  const { data: initialTasks } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => publishingAPI.list(),
  });

  // 使用初始數據
  useEffect(() => {
    if (initialTasks) {
      const taskMap = {};
      initialTasks.forEach(task => {
        taskMap[task.id] = task;
      });
      setTasks(taskMap);
    }
  }, [initialTasks]);

  // WebSocket 實時更新
  const { state, isConnected } = useWebSocket({
    url: `ws://${window.location.host}/ws/tasks`,
    enabled: true,
    onMessage: (message) => {
      if (message.type === 'task_update') {
        setTasks(prev => ({
          ...prev,
          [message.data.task_id]: {
            ...prev[message.data.task_id],
            ...message.data,
          },
        }));
      }
    },
  });

  return (
    <div>
      <div className="connection-status">
        WebSocket: {state}
        {isConnected && <Badge status="success" text="已連接" />}
      </div>
      <TaskList tasks={Object.values(tasks)} />
    </div>
  );
}
```

### 示例 4: 混合模式（Polling + WebSocket）

```tsx
function HybridTaskMonitor() {
  const [tasks, setTasks] = useState([]);

  // 使用輪詢作為後備方案
  const { refetch } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const response = await publishingAPI.list();
      setTasks(response.data.items);
      return response.data.items;
    },
  });

  // WebSocket 實時更新（優先）
  const { isConnected } = useWebSocket({
    url: 'ws://localhost:8000/ws/tasks',
    enabled: true,
    onMessage: (message) => {
      if (message.type === 'task_update') {
        setTasks(prev =>
          prev.map(task =>
            task.id === message.data.task_id
              ? { ...task, ...message.data }
              : task
          )
        );
      }
    },
  });

  // WebSocket 斷開時使用輪詢
  const { isPolling } = usePolling(refetch, {
    interval: 5000,
    enabled: !isConnected, // 僅在 WebSocket 斷開時啟用
  });

  return (
    <div>
      <div>
        更新方式: {isConnected ? 'WebSocket' : isPolling ? 'Polling' : '手動'}
      </div>
      <TaskList tasks={tasks} />
    </div>
  );
}
```

## 最佳實踐

### 1. 選擇合適的更新機制

```
使用輪詢 (Polling) 當:
✓ 數據更新頻率較低（> 5 秒）
✓ 無需實時性（可接受幾秒延遲）
✓ 後端不支持 WebSocket
✓ 實現簡單，維護成本低

使用 WebSocket 當:
✓ 需要真正的實時更新（< 1 秒）
✓ 數據變化頻繁
✓ 需要雙向通信
✓ 多用戶協作場景
```

### 2. 輪詢間隔設置

```tsx
// 高頻更新（任務監控）
interval: 3000  // 3 秒

// 中頻更新（列表頁面）
interval: 5000  // 5 秒

// 低頻更新（統計數據）
interval: 30000 // 30 秒

// 極低頻（配置信息）
interval: 60000 // 1 分鐘
```

### 3. 標籤頁隱藏時停止輪詢

```tsx
const { isPolling } = usePolling(fetchData, {
  interval: 5000,
  pollWhenHidden: false, // 標籤頁隱藏時停止，節省資源
});
```

### 4. 錯誤處理

```tsx
const { isPolling, errorCount, resetErrors } = usePolling(fetchData, {
  interval: 5000,
  maxErrors: 3,
  onMaxErrors: (count) => {
    // 提示用戶
    notification.error({
      message: '自動刷新已停止',
      description: `連續 ${count} 次失敗，請檢查網絡連接`,
    });
  },
});

// 重試按鈕
if (errorCount > 0) {
  return (
    <Button onClick={() => {
      resetErrors();
      refetch();
    }}>
      重試
    </Button>
  );
}
```

### 5. 用戶控制

```tsx
// 總是提供關閉自動刷新的選項
<AutoRefreshControl
  onRefresh={refetch}
  interval={5000}
  defaultEnabled={true}  // 可配置默認狀態
  showIntervalSelector={true}  // 讓用戶選擇頻率
/>
```

### 6. 性能優化

```tsx
// 使用 useMemo 避免不必要的重新渲染
const filteredTasks = useMemo(() =>
  tasks.filter(task => task.status === filter),
  [tasks, filter]
);

// 使用虛擬滾動處理大列表
import { FixedSizeList } from 'react-window';

function TaskList({ tasks }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={tasks.length}
      itemSize={50}
    >
      {({ index, style }) => (
        <div style={style}>
          <TaskItem task={tasks[index]} />
        </div>
      )}
    </FixedSizeList>
  );
}
```

### 7. WebSocket 重連策略

```tsx
const { state, reconnectAttempts } = useWebSocket({
  url: 'ws://localhost:8000/ws',
  autoReconnect: true,
  reconnectDelay: 3000,
  maxReconnectAttempts: 5,
  onReconnect: (attempt) => {
    console.log(`Reconnection attempt ${attempt}`);
  },
});

// 顯示重連狀態
if (state === 'connecting' && reconnectAttempts > 0) {
  return <div>重新連接中... ({reconnectAttempts}/5)</div>;
}
```

## 環境變量配置

在 `.env` 文件中配置 WebSocket URL：

```env
# WebSocket 端點
VITE_WS_URL=ws://localhost:8000/ws

# 是否啟用 WebSocket（開發環境可能禁用）
VITE_ENABLE_WEBSOCKET=true

# 默認輪詢間隔（毫秒）
VITE_DEFAULT_POLLING_INTERVAL=5000
```

## 總結

- ✅ **usePolling**: 簡單可靠的輪詢解決方案
- ✅ **useQueryPolling**: React Query 集成
- ✅ **useWebSocket**: 真正的實時更新
- ✅ **AutoRefreshControl**: 用戶友好的控制組件
- ✅ **混合模式**: 結合兩者優勢
- ✅ **最佳實踐**: 性能優化和錯誤處理

根據實際需求選擇合適的更新機制，為用戶提供最佳體驗。
