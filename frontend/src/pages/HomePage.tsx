/**
 * Home page - Landing page for CMS automation.
 */

import { Card, CardHeader, CardContent } from '../components/ui';

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-gray-900 mb-8">
        AI-Powered CMS Automation
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader title="Article Generation" />
          <CardContent>
            <p className="text-gray-600">
              Generate high-quality articles from topics in 3-5 minutes using Claude AI.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Smart Tagging" />
          <CardContent>
            <p className="text-gray-600">
              Automatically tag and categorize content with 85%+ accuracy.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Scheduling" />
          <CardContent>
            <p className="text-gray-600">
              Schedule articles for future publication with ±1 minute accuracy.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
