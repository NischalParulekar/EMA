// Top-bar mood indicator. Color encodes pleasure:
// green = positive, red = negative, yellow = neutral.
function colorForPleasure(p) {
  if (p > 0.15) return '#2e7d32' // green
  if (p < -0.15) return '#c62828' // red
  return '#f9a825' // yellow
}

export default function MoodIndicator({ pad, label }) {
  const p = pad?.pleasure ?? 0
  const a = pad?.arousal ?? 0
  const d = pad?.dominance ?? 0
  const color = colorForPleasure(p)

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
      <span
        style={{
          width: 14,
          height: 14,
          borderRadius: '50%',
          background: color,
          display: 'inline-block'
        }}
      />
      <strong style={{ textTransform: 'capitalize' }}>{label}</strong>
      <span style={{ color: '#666' }}>
        P {p.toFixed(2)} · A {a.toFixed(2)} · D {d.toFixed(2)}
      </span>
    </div>
  )
}
