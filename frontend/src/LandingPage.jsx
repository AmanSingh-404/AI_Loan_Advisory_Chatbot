import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import './LandingPage.css'

function LandingPage() {
  const navigate = useNavigate()
  const cursorRef = useRef(null)
  const spotlightRef = useRef(null)
  const statsRowRef = useRef(null)
  const flapRefs = useRef([])
  const flapped = useRef(false)

  useEffect(() => {
    const cursor = cursorRef.current
    const spotlight = spotlightRef.current

    const handleMouseMove = (e) => {
      if (cursor) {
        cursor.style.left = e.clientX + 'px'
        cursor.style.top = e.clientY + 'px'
      }
      if (spotlight) {
        spotlight.style.setProperty('--mx', e.clientX + 'px')
        spotlight.style.setProperty('--my', e.clientY + 'px')
      }
    }
    document.addEventListener('mousemove', handleMouseMove)

    const hoverEls = document.querySelectorAll('.case-file, .principle, a')
    const growCursor = () => cursor && cursor.classList.add('big')
    const shrinkCursor = () => cursor && cursor.classList.remove('big')
    hoverEls.forEach((el) => {
      el.addEventListener('mouseenter', growCursor)
      el.addEventListener('mouseleave', shrinkCursor)
    })

    // Scroll reveal
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) e.target.classList.add('in')
        })
      },
      { threshold: 0.15 }
    )
    document.querySelectorAll('.reveal').forEach((el) => io.observe(el))

    // Split-flap stat counters
    const flapTargets = [
      { val: 4, suffix: '' },
      { val: 0, suffix: '' },
      { val: 100, suffix: '%' },
    ]

    const flapIO = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting && !flapped.current) {
            flapped.current = true
            flapTargets.forEach((t, i) => {
              let current = 0
              const step = Math.max(1, Math.round(t.val / 20))
              const iv = setInterval(() => {
                current += step
                if (current >= t.val) {
                  current = t.val
                  clearInterval(iv)
                }
                if (flapRefs.current[i]) {
                  flapRefs.current[i].textContent = current + t.suffix
                }
              }, 35)
            })
          }
        })
      },
      { threshold: 0.4 }
    )
    if (statsRowRef.current) flapIO.observe(statsRowRef.current)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      hoverEls.forEach((el) => {
        el.removeEventListener('mouseenter', growCursor)
        el.removeEventListener('mouseleave', shrinkCursor)
      })
      io.disconnect()
      flapIO.disconnect()
    }
  }, [])

  const goToChat = (e) => {
    e.preventDefault()
    navigate('/chat')
  }

  return (
    <div className="verita-landing">
      <div id="cursor" ref={cursorRef}></div>
      <div className="spotlight" id="spotlight" ref={spotlightRef}></div>

      <nav>
        <div className="wrap">
          <span className="brand">
            LoanSense AI<span className="dot">.</span>
          </span>
          <span className="nav-tag mono">CASE FILES: OPEN</span>
        </div>
      </nav>

      <section className="hero">
        <div className="wrap">
          <div className="hero-tag">CLASSIFIED — LOAN TERMS INSIDE</div>
          <h1>
            <span className="glitch-word">STOP</span> <span className="outline">GUESSING</span>
            <br />
            <span className="glitch-word hi">WHAT</span> YOUR
            <br />
            LOAN <span className="glitch-word">DOCS</span> SAY.
          </h1>
          <div className="hero-sub">
            <p className="hero-lede">
              LoanSense AI cracks open your loan paperwork and answers in plain language —{' '}
              <strong>every claim traced, every guess refused.</strong>
            </p>
            <a href="/chat" onClick={goToChat} className="cta-btn">
              Open a case file <span className="arrow">↗</span>
            </a>
          </div>
        </div>
      </section>

      <div className="wrap">
        <div className="angled-marquee">
          <div className="track">
            <span>HOME LOAN POLICY</span>
            <span>SBI PERSONAL LOAN T&C</span>
            <span>STANDARD CHARTERED T&C</span>
            <span>RBI CIRCULARS</span>
            <span>HOME LOAN POLICY</span>
            <span>SBI PERSONAL LOAN T&C</span>
            <span>STANDARD CHARTERED T&C</span>
            <span>RBI CIRCULARS</span>
          </div>
        </div>

        <div className="stats-row reveal" ref={statsRowRef}>
          <div className="stat">
            <div className="flap" ref={(el) => (flapRefs.current[0] = el)}>0</div>
            <div className="label">Documents loaded</div>
          </div>
          <div className="stat">
            <div className="flap" ref={(el) => (flapRefs.current[1] = el)}>0</div>
            <div className="label">Facts invented</div>
          </div>
          <div className="stat">
            <div className="flap" ref={(el) => (flapRefs.current[2] = el)}>0%</div>
            <div className="label">Answers cited or declined</div>
          </div>
        </div>
      </div>

      <section className="section" id="how">
        <div className="wrap">
          <div className="kicker reveal">OPERATION: GROUNDED ANSWER</div>
          <h2 className="display reveal d1">
            THREE MOVES.
            <br />
            NO SHORTCUTS.
          </h2>

          <div className="case-files">
            <div className="case-file reveal">
              <span className="tag">FILE 01</span>
              <div>
                <h3>You ask, plainly</h3>
                <p>"Am I eligible for a home loan?" — no legal phrasing required. Verita reads the intent.</p>
              </div>
            </div>
            <div className="case-file reveal d1">
              <span className="tag">FILE 02</span>
              <div>
                <h3>The clause gets extracted</h3>
                <p>Only your loaded documents are searched. Never outside knowledge. Never a guess.</p>
              </div>
            </div>
            <div className="case-file reveal d2">
              <span className="tag">FILE 03</span>
              <div>
                <h3>The answer is interrogated</h3>
                <p>A second pass checks every claim against the source. Fails the check? Verita won't say it.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="demo">
        <div className="wrap">
          <div className="kicker reveal">EVIDENCE ON FILE</div>
          <h2 className="display reveal d1">
            DECLASSIFIED,
            <br />
            ON REQUEST.
          </h2>

          <div className="redact-block reveal d2">
            <div className="redact-q">
              Q — <strong>"Is there a pre-payment penalty on SBI personal loans?"</strong>
            </div>
            <div className="redact-line">
              No penalty on standard SBI personal loans — only the Rent Plus product charges 1% of the amount
              prepaid.
              <div className="redact-bar"></div>
            </div>
            <div>
              <span className="stamp-verified">✓ SOURCE VERIFIED — SEC. 9</span>
            </div>

            <div className="decline-strip">
              <span className="x">✕</span>
              <p>"What is the current RBI repo rate?" — no loaded document states it. Case closed: unanswered, on purpose.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="why">
        <div className="wrap">
          <div className="kicker reveal">RULES OF EVIDENCE</div>
          <h2 className="display reveal d1">
            CONFIDENCE IS EASY.
            <br />
            BEING RIGHT ISN'T.
          </h2>

          <div className="principle-grid">
            <div className="principle reveal">
              <div className="pn">01</div>
              <h3>Cited, not summarized</h3>
              <p>Every answer names the exact document and section behind it.</p>
            </div>
            <div className="principle reveal d1">
              <div className="pn">02</div>
              <h3>Refuses, never improvises</h3>
              <p>No answer in the docs means no answer, period.</p>
            </div>
            <div className="principle reveal d2">
              <div className="pn">03</div>
              <h3>Minimum necessary exposure</h3>
              <p>Only the relevant passages are shared — never a full document.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="final">
        <div className="wrap">
          <h2 className="reveal">
            READY TO <span className="hi">INTERROGATE</span>
            <br />
            YOUR LOAN TERMS?
          </h2>
          <a href="/chat" onClick={goToChat} className="cta-btn reveal d1">
            Open a case file <span className="arrow">↗</span>
          </a>
        </div>
      </section>

      <footer>
        <div className="wrap">
          <span>LoanSense AI // GROUNDED LOAN ANSWERS</span>
          <span>NOTHING ANSWERED WITHOUT A SOURCE</span>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage