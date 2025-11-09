# Settings Save Button Issue - Diagnosis Report

**Date**: 2025-11-08
**Issue**: User reports clicking "立即儲存" (Save Now) button shows no visual feedback
**Status**: ✅ ROOT CAUSE IDENTIFIED

---

## User's Report

> "更改了設置。好比說改動了 Provider 配置裏面的 Hybrid。使用了主 Provider，使用了 Computer Use。然後點擊右上角藍色的立即儲存按鈕，沒有任何反應。視覺效果上沒有任何反應，不知道保存了還是沒保存。"

Translation: Changed Provider settings (Hybrid mode, Computer Use as primary). Clicked the blue "Save Now" button in the upper right. No response, no visual feedback, don't know if settings were saved.

---

## Investigation

### Debug Test Results

Created `e2e/debug-settings-save.spec.ts` and found:

```
✅ Toast notification IS working
✅ Found 3 toast(s) with selector: [role="alert"]
Toast text: "WordPress URL 不能为空"
```

**Critical Finding**: The Toast IS appearing, but it's showing an **ERROR message**, not a success message!

### Network Analysis

```
Settings API calls: [
  {
    url: 'https://.../v1/settings',
    method: 'GET',   // ← Only GET request
    status: 200
  }
]
```

**No PUT request was sent** - The save was blocked by validation before reaching the API.

---

## Root Cause

### Field Name Mismatch Between Backend and Frontend

**Backend API Response** (`/v1/settings GET`):
```json
{
  "cms_config": {
    "base_url": "https://admin.epochtimes.com",
    "application_password": "kfS*qxdQqm@zic6lXvnR(ih!",
    "username": "ping.xie",
    ...
  }
}
```

**Frontend Form Schema** (`src/schemas/settings-schema.ts:73-91`):
```typescript
export const cmsConfigSchema = z.object({
  wordpress_url: z    // ← Expects "wordpress_url", NOT "base_url"
    .string(baseError)
    .min(1, 'WordPress URL 不能为空')  // Validation error message
    .url('请输入合法的 URL'),
  password: z         // ← Expects "password", NOT "application_password"
    .string(baseError)
    .min(1, '密码不能为空'),
  ...
});
```

**Type Definitions:**

1. **API Type** (`src/types/api.ts:321`):
   ```typescript
   export interface CMSConfig {
     cms_type: CMSType;
     base_url: string;              // ← Backend field
     username?: string;
     application_password?: string;  // ← Backend field
     api_token?: string;
   }
   ```

2. **Form Type** (`src/types/settings.ts:54`):
   ```typescript
   export interface CMSConfig {
     wordpress_url: string;  // ← Frontend field
     username: string;
     password: string;       // ← Frontend field
     verify_ssl: boolean;
     timeout: number;
     max_retries: number;
   }
   ```

### The Problem Flow

1. User loads Settings page
2. Backend returns `base_url` and `application_password`
3. Frontend form expects `wordpress_url` and `password`
4. **Mapping is broken** → fields stay empty
5. User changes Provider settings
6. User clicks "Save Settings"
7. React Hook Form validation runs
8. Validation fails: `wordpress_url` is empty
9. Toast shows: "WordPress URL 不能为空"
10. **No API call is made**

---

## Why User Didn't See the Toast

Possible reasons:
1. **Toast appeared off-screen** (top of page, user scrolled down)
2. **Auto-dismiss** (5-second duration)
3. **Expected success toast**, not error toast
4. **Red error toast** vs expected green success toast

---

## The Fix

Need to fix the `buildDefaultSettings` function in `SettingsPageModern.tsx` to properly map backend fields to frontend fields:

```typescript
// Current (BROKEN):
cms_config: {
  wordpress_url: settings.cms_config?.wordpress_url ?? defaults.cms_config.wordpress_url,
  password: settings.cms_config?.password ?? defaults.cms_config.password,
  ...
}

// Fixed (CORRECT):
cms_config: {
  wordpress_url: settings.cms_config?.base_url ?? defaults.cms_config.wordpress_url,
  password: settings.cms_config?.application_password ?? defaults.cms_config.password,
  ...
}
```

Also need to fix the reverse mapping in `onSubmit`:

```typescript
// When sending to backend, map frontend → backend:
const updates: SettingsUpdateRequest = {
  cms_config: {
    base_url: values.cms_config.wordpress_url,
    application_password: values.cms_config.password,
    username: values.cms_config.username,
    ...
  },
  ...
};
```

---

## Verification Plan

1. Fix field mapping in `buildDefaultSettings`
2. Fix field mapping in `onSubmit`
3. Deploy to production
4. Test: Change Provider settings → Click Save → Should see success toast
5. Verify API PUT request is sent
6. Verify settings are persisted

---

## Summary

- ✅ Toast notifications ARE working correctly
- ✅ Form validation IS working correctly
- ❌ Field mapping between backend/frontend is BROKEN
- ❌ This causes `wordpress_url` to be empty
- ❌ Validation blocks save with error toast
- ❌ User doesn't see the error toast or mistakes it for lack of feedback

**Fix**: Update field name mapping to correctly translate between backend (`base_url`, `application_password`) and frontend (`wordpress_url`, `password`).
