-- 驗證管理員用戶是否正確創建
SELECT
  p.id,
  p.display_name,
  p.role,
  u.email,
  u.created_at
FROM public.profiles p
JOIN auth.users u ON p.id = u.id
WHERE u.email = 'albert.king@epochtimes.nyc';
