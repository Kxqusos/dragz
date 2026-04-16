export function formatDistanceKm(distanceKm: number): string {
  const safeDistance = Math.max(0, distanceKm);
  return `${safeDistance.toFixed(1)} км`;
}
