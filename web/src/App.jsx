import { useCallback, useEffect, useRef, useState } from 'react'

let idCounter = 0
const nextId = () => `m${++idCounter}`

async function streamChat(userInput, onEvent) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput }),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Request failed with status ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const frames = buffer.split('\n\n')
    buffer = frames.pop()

    for (const frame of frames) {
      for (const line of frame.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          onEvent(JSON.parse(line.slice(6)))
        } catch {
          // ignore malformed frames
        }
      }
    }
  }
}

export default function App() {
  const [config, setConfig] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    fetch('/api/config')
      .then((res) => res.json())
      .then(setConfig)
      .catch(() => setConfig({ ready: false, error: 'API unreachable' }))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async () => {
    const userInput = input.trim()
    if (!userInput || streaming) return

    setInput('')
    setStreaming(true)
    setMessages((prev) => [
      ...prev,
      { id: nextId(), role: 'user', content: userInput },
      { id: nextId(), role: 'assistant', content: '', statuses: [], running: true },
    ])

    const onEvent = (event) => {
      setMessages((prev) => {
        const last = prev[prev.length - 1]
        if (!last || last.role !== 'assistant') return prev

        let next = { ...last }
        if (event.type === 'token') {
          next = { ...next, content: last.content + event.data }
        } else if (event.type === 'status') {
          next = {
            ...next,
            statuses: [...last.statuses, { text: event.data, done: false }],
          }
        } else if (event.type === 'done') {
          next = {
            ...next,
            running: false,
            statuses: (last.statuses || []).map((s) => ({ ...s, done: true })),
          }
        } else if (event.type === 'error') {
          next = {
            ...next,
            running: false,
            content: last.content + `\n[error] ${event.data}`,
          }
        }
        return [...prev.slice(0, -1), next]
      })
    }

    try {
      await streamChat(userInput, onEvent)
    } catch (err) {
      setMessages((prev) => {
        const last = prev[prev.length - 1]
        if (!last) return prev
        return [
          ...prev.slice(0, -1),
          {
            ...last,
            running: false,
            content: last.content + `\n[error] ${err.message}`,
          },
        ]
      })
    } finally {
      setStreaming(false)
    }
  }, [input, streaming])

  const ready = config?.ready
  const running = config?.ollama_running

  return (
    <div className="app">
      <header className="header">
        <h1>Mail Agent</h1>
        <div className="status">
          {config && (
            <>
              {ready ? (
                <span className="dot ok" />
              ) : (
                <span className="dot bad" />
              )}
              <span>{ready ? 'agent ready' : 'agent offline'}</span>
              {config.model && <span className="chip">{config.model}</span>}
              {[...new Set(config.enabled_tools || [])].map((t) => (
                <span className="chip" key={t}>
                  {t}
                </span>
              ))}
              <span className={`chip ${running ? 'ok' : 'bad'}`}>
                ollama {running ? 'up' : 'down'}
              </span>
            </>
          )}
        </div>
      </header>

      {config && !config.ready && (
        <div className="banner">
          {config.error || 'Agent not initialized.'} Run{' '}
          <code>mail-agent setup</code> and restart the API.
        </div>
      )}

      <main className="messages">
        {messages.length === 0 && (
          <div className="empty">Ask me to read or send an email.</div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`msg ${m.role}`}>
            {m.role === 'assistant' && m.statuses.length > 0 && (
              <div className="statuses">
                {m.statuses.map((s, i) => (
                  <div key={i} className={`tool-status ${s.done ? 'done' : 'active'}`}>
                    {s.done ? '✓' : <span className="spinner" />} {s.text}
                  </div>
                ))}
              </div>
            )}
            <div className="bubble">
              {m.content || (m.running ? '…' : '')}
              {m.running && m.content && <span className="cursor" />}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </main>

      <footer className="composer">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask your mail agent…"
          disabled={!ready}
        />
        <button onClick={handleSend} disabled={!ready || !input.trim() || streaming}>
          {streaming ? '…' : 'Send'}
        </button>
      </footer>
    </div>
  )
}
