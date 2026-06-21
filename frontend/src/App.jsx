import { useState, useEffect, useRef } from 'react'
import { sendMessage, getMood } from './services/api'
import MoodIndicator from './components/MoodIndicator'
import ChatWindow from './components/ChatWindow'
import MemoryPanel from './components/MemoryPanel'

const USER_ID = 'dev_user'

// Mirror of PADVector.label() on the backend so each EMA response can show
// an emotional label derived from its returned PAD emotional_tag.
function labelFromPad(pad) {
  const { pleasure = 0, arousal = 0, dominance = 0 } = pad || {}
  if (pleasure > 0.5 && arousal > 0.3) return 'excited'
  if (pleasure > 0.5 && arousal <= 0.3) return 'content'
  if (pleasure < -0.3 && arousal > 0.5) return 'frustrated'
  if (pleasure < -0.3 && arousal <= 0.3) return 'sad'
  if (arousal > 0.7) return 'alert'
  if (dominance < -0.5) return 'overwhelmed'
  return 'neutral'
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [mood, setMood] = useState({ pleasure: 0, arousal: 0, dominance: 0 })
  const [moodLabel, setMoodLabel] = useState('neutral')
  const [sending, setSending] = useState(false)
  const [memoriesRetrieved, setMemoriesRetrieved] = useState(0)

  // Stable session id generated once on app load.
  const sessionId = useRef(crypto.randomUUID())

  // Poll /mood/{user_id} every 10 seconds.
  useEffect(() => {
    let active = true
    const fetchMood = async () => {
      try {
        const data = await getMood(USER_ID)
        if (!active) return
        setMood(data.pad)
        setMoodLabel(data.label)
      } catch {
        // Ignore polling errors (backend may not be up yet).
      }
    }
    fetchMood()
    const id = setInterval(fetchMood, 10000)
    return () => {
      active = false
      clearInterval(id)
    }
  }, [])

  const handleSend = async (text) => {
    if (!text.trim() || sending) return
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setSending(true)
    try {
      const data = await sendMessage(text, USER_ID, sessionId.current)
      setMessages((prev) => [
        ...prev,
        {
          role: 'ema',
          content: data.response,
          emotionalLabel: labelFromPad(data.emotional_tag),
          model: data.model_used,
          canaryVerified: data.canary_verified
        }
      ])
      setMood(data.current_mood)
      setMoodLabel(labelFromPad(data.current_mood))
      setMemoriesRetrieved(data.memories_retrieved)
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'ema',
          content: 'EMA: (connection error — is the backend running on :8000?)',
          emotionalLabel: 'neutral',
          model: null
        }
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div
      style={{
        fontFamily: 'system-ui, -apple-system, sans-serif',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        color: '#111'
      }}
    >
      <header
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid #ddd',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16
        }}
      >
        <h2 style={{ margin: 0, fontSize: 18 }}>EMA — Emotional Memory Agent</h2>
        <MoodIndicator pad={mood} label={moodLabel} />
      </header>

      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <ChatWindow messages={messages} onSend={handleSend} sending={sending} />
        </div>
        <aside style={{ width: 280, borderLeft: '1px solid #ddd', overflowY: 'auto' }}>
          <MemoryPanel mood={mood} memoriesRetrieved={memoriesRetrieved} />
        </aside>
      </div>
    </div>
  )
}
