import { useState, useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'

export default function ChatWindow({ messages, onSend, sending }) {
  const [input, setInput] = useState('')
  const endRef = useRef(null)

  // Keep the latest message in view as history grows.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const submit = (e) => {
    e.preventDefault()
    onSend(input)
    setInput('')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
        {messages.length === 0 && (
          <p style={{ color: '#999' }}>Say hello to EMA…</p>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={submit}
        style={{ display: 'flex', gap: 8, padding: 16, borderTop: '1px solid #ddd' }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          style={{
            flex: 1,
            padding: 10,
            borderRadius: 8,
            border: '1px solid #ccc',
            fontSize: 14
          }}
        />
        <button
          type="submit"
          disabled={sending}
          style={{
            padding: '10px 18px',
            borderRadius: 8,
            border: 'none',
            background: sending ? '#90a4ae' : '#1565c0',
            color: '#fff',
            cursor: sending ? 'default' : 'pointer'
          }}
        >
          {sending ? '…' : 'Send'}
        </button>
      </form>
    </div>
  )
}
