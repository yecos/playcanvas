'use client';

import dynamic from 'next/dynamic';

const PlayCanvasDashboard = dynamic(
  () => import('@/components/playcanvas/playcanvas-dashboard').then((mod) => mod.default),
  { ssr: false }
);

export default function Home() {
  return <PlayCanvasDashboard />;
}
