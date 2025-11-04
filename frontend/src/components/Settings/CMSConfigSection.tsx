/**
 * CMS Configuration Section component.
 * Configure WordPress/CMS connection settings.
 */

import { useState } from 'react';
import { CMSConfig } from '@/types/settings';
import { Card, Input, Button } from '@/components/ui';
import { Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react';

export interface CMSConfigSectionProps {
  config: CMSConfig;
  onChange: (config: CMSConfig) => void;
  onTestConnection?: () => Promise<boolean>;
}

export const CMSConfigSection: React.FC<CMSConfigSectionProps> = ({
  config,
  onChange,
  onTestConnection,
}) => {
  // Provide safe defaults for when backend returns empty objects
  const safeConfig = {
    wordpress_url: config.wordpress_url ?? '',
    username: config.username ?? '',
    password: config.password ?? '',
    verify_ssl: config.verify_ssl ?? true,
    timeout: config.timeout ?? 30000,
    max_retries: config.max_retries ?? 3,
  };

  const [showPassword, setShowPassword] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const handleTestConnection = async () => {
    if (!onTestConnection) return;

    setTesting(true);
    setTestResult(null);

    try {
      const success = await onTestConnection();
      setTestResult(success ? 'success' : 'error');
    } catch (error) {
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  const updateConfig = (updates: Partial<CMSConfig>) => {
    onChange({ ...safeConfig, ...updates });
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        WordPress 连接配置
      </h2>

      <div className="space-y-4">
        <Input
          type="url"
          label="WordPress URL"
          value={safeConfig.wordpress_url}
          onChange={(e) => updateConfig({ wordpress_url: e.target.value })}
          placeholder="https://example.com"
          required
        />

        <Input
          type="text"
          label="用户名"
          value={safeConfig.username}
          onChange={(e) => updateConfig({ username: e.target.value })}
          required
        />

        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            label="密码"
            value={safeConfig.password}
            onChange={(e) => updateConfig({ password: e.target.value })}
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
          >
            {showPassword ? (
              <EyeOff className="w-5 h-5" />
            ) : (
              <Eye className="w-5 h-5" />
            )}
          </button>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="verify-ssl"
            checked={safeConfig.verify_ssl}
            onChange={(e) => updateConfig({ verify_ssl: e.target.checked })}
            className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
          />
          <label htmlFor="verify-ssl" className="ml-2 text-sm text-gray-700">
            验证 SSL 证书
          </label>
        </div>

        <Input
          type="number"
          label="超时时间 (毫秒)"
          value={safeConfig.timeout}
          onChange={(e) => updateConfig({ timeout: parseInt(e.target.value) })}
          min={1000}
          max={60000}
        />

        <Input
          type="number"
          label="最大重试次数"
          value={safeConfig.max_retries}
          onChange={(e) => updateConfig({ max_retries: parseInt(e.target.value) })}
          min={0}
          max={5}
        />

        {/* Test Connection */}
        <div className="pt-4 border-t border-gray-200">
          <Button
            variant="outline"
            onClick={handleTestConnection}
            disabled={testing || !safeConfig.wordpress_url || !safeConfig.username || !safeConfig.password}
            className="w-full"
          >
            {testing ? '测试中...' : '测试连接'}
          </Button>

          {testResult && (
            <div
              className={`mt-3 p-3 rounded-lg flex items-center ${
                testResult === 'success'
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              {testResult === 'success' ? (
                <>
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <span className="text-sm text-green-700">
                    连接成功！WordPress 配置正确。
                  </span>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-red-600 mr-2" />
                  <span className="text-sm text-red-700">
                    连接失败。请检查 URL、用户名和密码是否正确。
                  </span>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
