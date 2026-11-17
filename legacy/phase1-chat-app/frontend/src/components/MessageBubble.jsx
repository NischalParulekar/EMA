// Maps a model id (ModelTier value) to a short display name.
function modelName(model) {
  if (!model) return null
  if (model.includes('haiku')) return 'Haiku'
  if (model.includes('sonnet')) return 'Sonnet'
  if (model.includes('opus')) return 'Opus'
  return model
}

const badgeStyle = {
  fontSize: 11,
  padding: '1px 6px',
  borderRadius: 6,
  background: '#e0e0e0',
  color: '#333'
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  const model = modelName(message.model)

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 12
      }}
    >
      <div
        style={{
          maxWidth: '72%',
          padding: '10px 14px',
          borderRadius: 12,
          background: isUser ? '#1565c0' : '#f1f3f4',
          color: isUser ? '#fff' : '#111'
        }}
      >
        <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>

        {!isUser && (
          <div
            style={{
              marginTop: 6,
              fontSize: 12,
              color: '#666',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            <span>🏷 {message.emotionalLabel}</span>
            {model && <span style={badgeStyle}>{model}</span>}
          </div>
        )}
      </div>
    </div>
  )
}
