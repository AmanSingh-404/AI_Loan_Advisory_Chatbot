import { useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

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
        body: JSON.stringify({ question: userMessage.text }),
      })

      if (!response.ok) throw new Error('Server error')

      const data = await response.json()
      const botMessage = { role: 'bot', text: data.answer, sources: data.sources }
      setMessages((prev) => [...prev, botMessage])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: "Sorry, I couldn't reach the server. Please check the backend is running." },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>AI Loan Advisory Chatbot</h1>
      </header>

      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="empty-state">Ask me anything about loan eligibility, EMI, or policies.</p>
        )}
        {messages.map((msg, idx) => {
          const isRefusal = msg.role === 'bot' && (!msg.sources || msg.sources.length === 0)
          return (
            <div key={idx} className={`message ${msg.role} ${isRefusal ? 'not-found' : ''}`}>
              {msg.text}
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">📄 Source: {msg.sources.join(', ')}</div>
              )}
            </div>
          )
        })}
        {loading && <div className="message bot loading">Thinking...</div>}
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your question..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading}>Send</button>
      </div>
    </div>
  )
}

export default App