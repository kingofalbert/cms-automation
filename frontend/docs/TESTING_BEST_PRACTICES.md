# Frontend Testing Best Practices

## 目录

- [Vitest Fake Timers 与异步操作](#vitest-fake-timers-与异步操作)
  - [usePolling Hook 测试案例分析](#usepolling-hook-测试案例分析)
  - [问题根因](#问题根因)
  - [解决方案](#解决方案)
  - [最佳实践](#最佳实践)
- [React Testing Library 最佳实践](#react-testing-library-最佳实践)
- [Playwright E2E 测试最佳实践](#playwright-e2e-测试最佳实践)

---

## Vitest Fake Timers 与异步操作

### usePolling Hook 测试案例分析

#### 背景

在测试 `usePolling` hook 时，我们遇到了一个常见但容易误判的问题：使用 Vitest fake timers 时，测试断言与实际 hook 行为不符，导致测试失败。

**症状**：
- 期望 callback 被调用 1 次，实际被调用 2 次
- 错误计数跳跃（期望 1，实际 2）
- 使用 `waitFor()` 导致超时
- 使用 `runAllTimersAsync()` 触发 "Aborting after running 10000 timers"

#### 问题根因

`usePolling` hook 的实现在 mount 时执行两个异步操作：

```typescript
// frontend/src/hooks/usePolling.ts (lines 225-239)
useEffect(() => {
  if (isPolling) {
    // 操作 1: 如果 pollOnMount 为 true，立即执行一次
    if (pollOnMount) {
      poll();  // 👈 作为 microtask 排队
    }

    // 操作 2: 启动 setInterval
    intervalRef.current = setInterval(poll, interval);  // 👈 第一个 tick 在时间 0 处排队
  }

  return () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  };
}, [isPolling, poll, interval]);
```

**关键问题**：在 Vitest fake timers 下：
1. `poll()` 调用作为 **microtask** 立即执行
2. `setInterval` 的第一个 tick 也在**同一模拟时间戳**排队
3. 单次 `vi.runOnlyPendingTimersAsync()` 会**同时执行两者**
4. 导致 callback 被调用 2 次而非预期的 1 次

**错误的修复尝试**：

```typescript
// ❌ 错误 1: 使用 waitFor (需要真实定时器)
await waitFor(() => expect(callback).toHaveBeenCalledTimes(1));
// 结果: 超时，因为 fake timers 下 waitFor 无法推进时间

// ❌ 错误 2: 使用 runAllTimersAsync (执行所有定时器)
await vi.runAllTimersAsync();
// 结果: "Aborting after running 10000 timers"
// 原因: setInterval 是无限循环，fake timers 会一直执行直到达到安全限制
```

### 解决方案

核心原则：**分离 microtask 执行和 timer 推进**

#### 正确的测试模式

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePolling } from '../usePolling';

describe('usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  // ✅ 模式 1: 测试 mount 时的立即执行
  it('should start polling immediately by default', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        pollOnMount: true,
      })
    );

    // 步骤 1: 只执行 microtask（让 mount 触发的 poll() 完成）
    await act(async () => {
      await Promise.resolve();
    });

    // 此时只有 mount 触发的 poll() 执行了
    expect(callback).toHaveBeenCalledTimes(1);
    expect(result.current.isPolling).toBe(true);
  });

  // ✅ 模式 2: 测试后续的 interval ticks
  it('should poll at the specified interval', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        pollOnMount: true,
      })
    );

    // 步骤 1: 等待初始 poll (只 microtasks)
    await act(async () => {
      await Promise.resolve();
    });
    expect(callback).toHaveBeenCalledTimes(1);

    // 步骤 2: 推进时间到第一个 interval tick
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve(); // 等待 interval callback 的 promise
    });
    expect(callback).toHaveBeenCalledTimes(2);

    // 步骤 3: 推进到第二个 interval tick
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
    });
    expect(callback).toHaveBeenCalledTimes(3);
  });

  // ✅ 模式 3: 测试第一个 interval (无 mount 调用)
  it('should not poll on mount if pollOnMount is false', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        pollOnMount: false,  // 👈 禁用 mount 时立即执行
      })
    );

    // 等待 microtasks
    await act(async () => {
      await Promise.resolve();
    });
    expect(callback).not.toHaveBeenCalled();

    // 推进到第一个 interval tick
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
    });
    expect(callback).toHaveBeenCalledTimes(1);
  });
});
```

#### 关键技术点

1. **`await Promise.resolve()`**
   - 只执行当前 event loop 中排队的 microtasks
   - 不触发 timers
   - 用于让 useEffect 中的异步操作完成

2. **`vi.advanceTimersByTime(ms)`**
   - 精确推进 fake timer 到指定时间
   - 执行该时间点之前的所有定时器
   - 比 `runAllTimers()` 更可控

3. **`act()` 包装**
   - 所有导致状态更新的操作都应该在 `act()` 中
   - 包括 timer 推进和 promise 等待

### 最佳实践

#### DO ✅

```typescript
// ✅ 使用 Promise.resolve() 只执行 microtasks
await act(async () => {
  await Promise.resolve();
});

// ✅ 使用 advanceTimersByTime() 精确控制时间
await act(async () => {
  vi.advanceTimersByTime(1000);
  await Promise.resolve();
});

// ✅ 理解 microtask 和 timer 的执行顺序
// 1. mount 时的 poll() -> microtask
// 2. setInterval 的 tick -> timer

// ✅ 分别测试立即执行和后续 ticks
// 立即执行: 只用 Promise.resolve()
// 后续 ticks: advanceTimersByTime() + Promise.resolve()

// ✅ 在 act() 中包装所有状态更新
await act(async () => {
  // 所有异步操作
});
```

#### DON'T ❌

```typescript
// ❌ 不要使用 waitFor() - 需要真实定时器
await waitFor(() => expect(callback).toHaveBeenCalled());

// ❌ 不要使用 runAllTimersAsync() - 会执行无限 interval
await vi.runAllTimersAsync();

// ❌ 不要假设单次 timer flush 只触发一次回调
vi.runOnlyPendingTimersAsync();  // 可能执行多次

// ❌ 不要混淆 microtask 和 timer 的执行时机
// 如果不清楚，分开测试

// ❌ 不要在没有 act() 的情况下推进 timers
vi.advanceTimersByTime(1000);  // 缺少 act() 包装
```

#### 通用测试模式

```typescript
// 模式 1: 测试只执行 mount 时的操作
renderHook(...);
await act(async () => {
  await Promise.resolve();  // 只执行 microtasks
});
// 验证 mount 时的行为

// 模式 2: 测试 interval 的第 N 次执行
for (let i = 0; i < N; i++) {
  await act(async () => {
    vi.advanceTimersByTime(interval);
    await Promise.resolve();
  });
}
// 验证执行了 N + 1 次 (mount + N intervals)

// 模式 3: 测试停止和重启
await act(async () => {
  result.current.stop();
});
// 验证停止

await act(async () => {
  vi.advanceTimersByTime(interval);
  await Promise.resolve();
});
// 验证没有新的调用
```

### 调试技巧

当遇到 fake timers 相关的测试问题时：

#### 1. 检查 hook 的 useEffect 逻辑

```typescript
// 查找是否有多个异步操作
useEffect(() => {
  // 操作 1: 立即执行?
  someAsyncFunction();

  // 操作 2: 定时器?
  const timer = setInterval(...);

  // 这两个操作的时序是什么？
}, [deps]);
```

#### 2. 添加日志观察执行顺序

```typescript
it('debug timing', async () => {
  const callback = vi.fn().mockImplementation(() => {
    console.log('Callback called at:', Date.now());
  });

  renderHook(...);
  console.log('After renderHook');

  await act(async () => {
    console.log('Before Promise.resolve');
    await Promise.resolve();
    console.log('After Promise.resolve');
  });

  await act(async () => {
    console.log('Before advanceTimersByTime');
    vi.advanceTimersByTime(1000);
    console.log('After advanceTimersByTime');
    await Promise.resolve();
    console.log('After Promise.resolve #2');
  });
});
```

#### 3. 逐步推进 timers

```typescript
// 不要一次推进太多时间
// ❌ 错误
vi.advanceTimersByTime(10000);

// ✅ 正确: 分步推进，每步验证
for (let i = 0; i < 10; i++) {
  await act(async () => {
    vi.advanceTimersByTime(1000);
    await Promise.resolve();
  });
  console.log(`After ${i + 1}s:`, callback.mock.calls.length);
}
```

#### 4. 使用 spy 的 mock 历史

```typescript
// 查看每次调用的详细信息
console.log('Calls:', callback.mock.calls);
console.log('Call count:', callback.mock.calls.length);
console.log('Call args:', callback.mock.calls.map(c => c[0]));
```

### 常见陷阱

#### 陷阱 1: 混淆 microtask 和 timer

```typescript
// ❌ 错误理解
// 认为 setInterval 的第一次执行会在 interval 时间后
useEffect(() => {
  setInterval(fn, 1000);  // 第一次执行在 1000ms 后？
}, []);

// ✅ 实际行为
// setInterval 的第一次执行在下一个 timer phase
// 在 fake timers 下，可能与 mount 时的操作"合并"
```

#### 陷阱 2: 忘记等待 promise

```typescript
// ❌ 缺少 promise 等待
await act(async () => {
  vi.advanceTimersByTime(1000);
  // 缺少 await Promise.resolve()
});
// interval callback 返回的 promise 可能未完成

// ✅ 正确
await act(async () => {
  vi.advanceTimersByTime(1000);
  await Promise.resolve();  // 等待 callback 的 promise
});
```

#### 陷阱 3: 使用 real timers 的工具函数

```typescript
// ❌ waitFor 内部使用 real timers
await waitFor(() => {
  expect(callback).toHaveBeenCalled();
}, { timeout: 1000 });
// 在 fake timers 下永远不会通过

// ✅ 直接使用 fake timers 控制
await act(async () => {
  await Promise.resolve();
});
expect(callback).toHaveBeenCalled();
```

### 参考文档

- [Vitest: Mocking Timers](https://vitest.dev/api/vi.html#vi-usefaketimers)
- [React Testing Library: async utilities](https://testing-library.com/docs/dom-testing-library/api-async/)
- [usePolling Test Fix Analysis](../USE_POLLING_TEST_FIX_ANALYSIS.md)

### 相关问题 Troubleshooting

#### 问题: "Aborting after running 10000 timers"

**原因**: 使用了 `runAllTimersAsync()` 或 `runAllTimers()` 在有无限 `setInterval` 的情况下

**解决**:
```typescript
// ❌ 不要这样
await vi.runAllTimersAsync();

// ✅ 改用精确控制
await act(async () => {
  vi.advanceTimersByTime(1000);
  await Promise.resolve();
});
```

#### 问题: waitFor 超时

**原因**: `waitFor` 需要 real timers 来推进时间

**解决**:
```typescript
// ❌ 在 fake timers 下不工作
vi.useFakeTimers();
await waitFor(() => expect(callback).toHaveBeenCalled());

// ✅ 选项 1: 使用 real timers
vi.useRealTimers();
await waitFor(() => expect(callback).toHaveBeenCalled());

// ✅ 选项 2: 手动推进 fake timers
vi.useFakeTimers();
await act(async () => {
  vi.advanceTimersByTime(1000);
  await Promise.resolve();
});
expect(callback).toHaveBeenCalled();
```

#### 问题: Callback 被调用的次数不对

**调试步骤**:
1. 检查 hook 是否在 mount 时立即执行
2. 检查是否正确分离了 microtask 和 timer 推进
3. 添加 console.log 追踪执行顺序
4. 逐步推进时间，每步验证

---

## React Testing Library 最佳实践

*(待补充)*

---

## Playwright E2E 测试最佳实践

### 缓存和错误处理

在测试生产环境时，要注意 CDN 缓存可能导致的问题。

#### 问题: 部署后测试仍然看到旧版本

**原因**: Google Cloud Storage 的 CDN 缓存

**解决**:
```typescript
// 选项 1: 清除缓存并重新加载
await page.goto(url, {
  waitUntil: 'networkidle',
});

await page.evaluate(() => {
  localStorage.clear();
  sessionStorage.clear();
});

await page.reload({
  waitUntil: 'networkidle'
});

// 选项 2: 添加 cache-busting query parameter
await page.goto(`${url}?v=${Date.now()}`);
```

### 等待异步加载

```typescript
// ✅ 等待网络空闲
await page.goto(url, {
  waitUntil: 'networkidle'
});

// ✅ 等待特定元素出现
await page.waitForSelector('[data-testid="content"]');

// ✅ 等待 JavaScript 执行完成
await page.waitForFunction(() => {
  return window.myApp !== undefined;
});
```

### 错误捕获

```typescript
const pageErrors: Error[] = [];
const consoleErrors: string[] = [];

page.on('pageerror', (error) => {
  pageErrors.push(error);
  console.log(`Page Error: ${error.message}`);
});

page.on('console', (msg) => {
  if (msg.type() === 'error') {
    consoleErrors.push(msg.text());
  }
});

// 测试结束时验证
expect(pageErrors).toHaveLength(0);
expect(consoleErrors).toHaveLength(0);
```

---

## 总结

测试是保证代码质量的重要手段，但测试本身也需要正确的方法。特别是在处理异步操作和 fake timers 时，理解底层机制比盲目尝试更重要。

**记住**:
1. 理解工具的工作原理（fake timers, microtask, timer）
2. 分离不同类型的异步操作
3. 使用精确的控制方法而非"全量执行"
4. 在遇到问题时，先添加日志观察实际行为
5. 为团队记录经验，避免重复踩坑

**持续更新**: 本文档会随着项目发展持续更新，欢迎团队成员补充新的最佳实践和经验。
