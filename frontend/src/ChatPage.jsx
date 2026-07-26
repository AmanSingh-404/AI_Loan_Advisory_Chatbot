import { useState, useRef, useEffect } from 'react'
import './ChatPage.css'

const API_URL = 'https://ailoanadvisorychatbot-production.up.railway.app'
// const API_URL = 'http://127.0.0.1:8000'

function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  const sessionId = useRef(crypto.randomUUID())

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, loading])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = { role: 'user', text: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMessage.text, session_id: sessionId.current }),
      })

      if (!response.ok) throw new Error('Server error')

      const data = await response.json()
      const botMessage = { role: 'bot', text: data.answer, sources: data.sources, answerType: data.answer_type }
      setMessages((prev) => [...prev, botMessage])
    } catch (err) {
      console.error(err)
      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: "Connection to the case file server failed. Confirm the backend is running.", sources: [] },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: 'Only PDF files are supported.', sources: [] },
      ])
      e.target.value = ''
      return
    }

    setUploading(true)
    setMessages((prev) => [
      ...prev,
      { role: 'system', text: `Uploading "${file.name}" to the case file index...` },
    ])

    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId.current)

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        setMessages((prev) => [
          ...prev,
          { role: 'system', text: `Upload failed: ${data.detail}`, isError: true },
        ])
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'system',
            text: `"${data.filename}" added to the case file index (${data.chunks_added} sections indexed). You can ask about it now.`,
          },
        ])
      }
    } catch (err) {
      console.error(err)
      setMessages((prev) => [
        ...prev,
        { role: 'system', text: 'Upload failed: could not reach the server.', isError: true },
      ])
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="verita-chat">
      <header className="vc-header">
        <div className="vc-header-inner">
          <div className="vc-brand">
            LoanSense AI<span className="dot">.</span>
          </div>
          <a href="/" className="vc-back">← BACK TO CASE FILES</a>
        </div>
        <div className="vc-header-sub mono">LIVE INTERROGATION — LOAN DOCUMENTS ONLY</div>
      </header>

      <div className="vc-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="vc-empty">
            <div className="vc-empty-tag mono">CASE FILE — EMPTY</div>
            <h2>Ask something about your loan terms.</h2>
            <p>LoanSense AI only answers from the documents it's been given — home loan policy, SBI &amp; Standard Chartered personal loan terms, and RBI circulars. No source, no answer.</p>
          </div>
        )}

        {messages.map((msg, idx) => {
          if (msg.role === 'system') {
            return (
              <div key={idx} className="vc-row system">
                <div className={`vc-system-note mono ${msg.isError ? 'error' : ''}`}>
                  {msg.isError ? '⚠ ' : '📎 '}{msg.text}
                </div>
              </div>
            )
          }

          const isBot = msg.role === 'bot'
          const answerType = msg.answerType || 'document'
          const hasSources = msg.sources && msg.sources.length > 0
          const isCalculated = isBot && answerType === 'calculated'
          const isDeclined = isBot && !isCalculated && !hasSources

          let statusClass = 'verified'
          let statusLabel = '✓ SOURCE VERIFIED'
          if (isDeclined) {
            statusClass = 'declined'
            statusLabel = '✕ DECLINED — NOT IN FILE'
          } else if (isCalculated) {
            statusClass = 'calculated'
            statusLabel = '≈ CALCULATED — NOT FROM DOCUMENTS'
          }

          return (
            <div key={idx} className={`vc-row ${isBot ? 'bot' : 'user'}`}>
              <div className={`vc-bubble ${isBot ? statusClass : 'user'}`}>
                {isBot && <div className={`vc-status mono ${statusClass}`}>{statusLabel}</div>}
                <div className="vc-text">{msg.text}</div>
                {isBot && hasSources && (
                  <div className="vc-sources mono">§ {msg.sources.join(' · ')}</div>
                )}
              </div>
            </div>
          )
        })}

        {loading && (
          <div className="vc-row bot">
            <div className="vc-bubble loading">
              <span className="vc-loading-dots">
                <span></span><span></span><span></span>
              </span>
              <span className="mono">SEARCHING CASE FILES...</span>
            </div>
          </div>
        )}
      </div>

      <div className="vc-input-area">
        <input
          type="file"
          accept=".pdf"
          ref={fileInputRef}
          onChange={handleFileUpload}
          style={{ display: 'none' }}
        />
        <button
          className="vc-upload-btn"
          onClick={() => fileInputRef.current.click()}
          disabled={loading || uploading}
          title="Upload a PDF document"
        >
          <span className="clip-icon">📎</span>
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your question..."
          disabled={loading || uploading}
        />
        <button onClick={handleSend} disabled={loading || uploading}>
          SEND <span className="arrow">↗</span>
        </button>
      </div>
    </div>
  )
}

export default ChatPage