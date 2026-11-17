// Side panel showing memory activity and the current PAD mood breakdown.
function Row({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '4px 0' }}>
      <span style={{ color: '#555' }}>{label}</span>
      <strong>{(value ?? 0).toFixed(2)}</strong>
    </div>
  )
}

export default function MemoryPanel({ mood, memoriesRetrieved }) {
  return (
    <div style={{ padding: 16 }}>
      <h3 style={{ marginTop: 0, fontSize: 15 }}>Memory & Mood</h3>

      <p style={{ fontSize: 13, color: '#555' }}>
        Memories retrieved (last turn):{' '}
        <strong style={{ color: '#111' }}>{memoriesRetrieved}</strong>
      </p>

      <h4 style={{ marginBottom: 4, fontSize: 13 }}>Current PAD mood</h4>
      <Row label="Pleasure" value={mood?.pleasure} />
      <Row label="Arousal" value={mood?.arousal} />
      <Row label="Dominance" value={mood?.dominance} />
    </div>
  )
}
