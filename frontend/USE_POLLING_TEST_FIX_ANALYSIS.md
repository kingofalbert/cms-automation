# usePolling测试失败根因分析

## 🔍 问题根源

### 核心问题
usePolling tests失败的根本原因是 **假计时器（Fake Timers）与React hooks异步行为的复杂交互**。

### 失败演变过程

#### 第1阶段：超时（Timeout）
**症状**: 测试超时5000ms
**原因**: `waitFor()` 需要真实时间流逝，但`vi.useFakeTimers()`冻结了时间
**表现**: 所有测试都超时失败

#### 第2阶段：无限循环（Infinite Loop）
**症状**: "Aborting after running 10000 timers, assuming an infinite loop!"
**原因**: `vi.runAllTimersAsync()` 尝试运行所有计时器，包括持续的`setInterval`
**表现**: 8个测试失败，达到Vitest的安全限制

#### 第3阶段：双重调用（Double Call）✅ **当前状态**
**症状**: "expected 'spy' to be called 1 times, but got 2 times"
**原因**: `vi.runOnlyPendingTimersAsync()` 同时运行了：
1. useEffect中立即调用的`poll()`（pollOnMount）
2. setInterval的第一次触发

**表现**: 5个测试失败（从12个→5个，进步明显！）

---

## 🧪 问题详细分析

### usePolling hook的执行流程

```typescript
useEffect(() => {
  if (isPolling) {
    // 1️⃣ pollOnMount为true时立即调用
    if (pollOnMount) {
      poll(); // ← 第1次调用
    }

    // 2️⃣ 设置interval
    intervalRef.current = setInterval(poll, interval); // ← 第2次调用在1秒后
  }

  return cleanup;
}, [isPolling, interval, poll, pollOnMount, pollWhenHidden]);
```

### 测试执行时发生了什么

```typescript
// 测试代码
renderHook(() => usePolling(callback, { interval: 1000, enabled: true, pollOnMount: true }));

await act(async () => {
  await vi.runOnlyPendingTimersAsync();
});
// 期望: callback被调用1次
// 实际: callback被调用2次

// ❓ 为什么会这样？
```

### vi.runOnlyPendingTimersAsync() 的行为

`vi.runOnlyPendingTimersAsync()` 会：
1. ✅ 运行所有pending的微任务（Microtasks） - 包括初始poll()
2. ✅ 运行所有pending的宏任务（Macrotasks） - 包括setInterval的第一次触发
3. ❌ 不会继续运行后续的interval - 这是好的

**问题**：在useEffect完成后，**两个任务都在pending队列中**：
- 初始的 `poll()` promise（由pollOnMount触发）
- setInterval的第一次触发（时间=0，立即pending）

---

## ✅ 解决方案

### 方案1: 分离初始化和interval（推荐）✨

```typescript
it('should start polling immediately by default', async () => {
  const callback = vi.fn().mockResolvedValue(undefined);

  const { result } = renderHook(() =>
    usePolling(callback, {
      interval: 1000,
      enabled: true,
      pollOnMount: true,
    })
  );

  // 等待初始render完成
  await act(async () => {
    await Promise.resolve(); // 只等待微任务队列
  });

  expect(callback).toHaveBeenCalledTimes(1);
  expect(result.current.isPolling).toBe(true);
});
```

**优点**：
- ✅ 只等待微任务，不触发interval
- ✅ 更精确地控制测试时间
- ✅ 符合测试的语义期望

### 方案2: 禁用 pollOnMount

```typescript
it('should poll at the specified interval', async () => {
  const callback = vi.fn().mockResolvedValue(undefined);

  renderHook(() =>
    usePolling(callback, {
      interval: 1000,
      enabled: true,
      pollOnMount: false, // ← 关键：避免立即轮询
    })
  );

  // 推进1秒
  await act(async () => {
    vi.advanceTimersByTime(1000);
    await vi.runOnlyPendingTimersAsync();
  });

  expect(callback).toHaveBeenCalledTimes(1);
});
```

**优点**：
- ✅ 避免双重调用
- ✅ 更清晰的测试场景

### 方案3: 使用真实计时器（最简单）

```typescript
it('should start polling immediately by default', async () => {
  const callback = vi.fn().mockResolvedValue(undefined);

  // 不使用假计时器
  vi.useRealTimers();

  const { result } = renderHook(() =>
    usePolling(callback, {
      interval: 100, // 短间隔
      enabled: true,
    })
  );

  await waitFor(() => {
    expect(callback).toHaveBeenCalled();
  }, { timeout: 200 });

  result.current.stop();
  vi.useFakeTimers(); // 恢复
});
```

**优点**：
- ✅ 最简单，不需要处理假计时器复杂性
- ✅ 测试真实行为

**缺点**：
- ❌ 测试速度较慢
- ❌ 需要清理（stop polling）

---

## 🎯 推荐的修复方案

我建议使用 **方案1** - 分离初始化和interval，因为：
1. 性能好（使用假计时器）
2. 精确控制（分步验证）
3. 语义清晰（每个测试验证一个行为）

### 需要修复的测试

修复以下5个失败的测试：
1. ✅ should start polling immediately by default
2. ✅ should poll at the specified interval
3. ✅ should stop polling when stop() is called
4. ✅ should pause polling when tab is hidden
5. ✅ should continue polling when tab is hidden if pollWhenHidden is true

---

## 🛠️ 具体修复示例

### Before (错误)
```typescript
await act(async () => {
  await vi.runOnlyPendingTimersAsync(); // ← 运行了2次callback
});
expect(callback).toHaveBeenCalledTimes(1); // ❌ 失败：actual = 2
```

### After (正确)
```typescript
// 只等待useEffect完成
await act(async () => {
  await Promise.resolve();
});
expect(callback).toHaveBeenCalledTimes(1); // ✅ 成功：actual = 1
```

---

## 📝 总结

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 超时 | waitFor + 假计时器不兼容 | 使用 act + vi.runOnlyPendingTimersAsync |
| 无限循环 | vi.runAllTimersAsync运行所有timers | 改用 vi.runOnlyPendingTimersAsync |
| 双重调用 | pollOnMount + interval同时pending | 使用 await Promise.resolve() 只等待初始化 |

### 关键学习点

1. **假计时器测试React hooks需要精确控制执行时机**
2. **useEffect + setInterval 创建复杂的异步流程**
3. **不同的Vitest timer方法有不同的行为**:
   - `vi.runAllTimersAsync()` - 运行所有timers（包括无限interval）❌
   - `vi.runOnlyPendingTimersAsync()` - 运行当前pending的timers（可能包括interval第一次）⚠️
   - `vi.advanceTimersByTime() + await Promise.resolve()` - 精确控制✅

---

**状态**: 🔧 待修复（5/12个测试失败）
**下一步**: 应用方案1修复剩余5个测试
