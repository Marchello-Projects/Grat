import { useState } from 'react'
import { generateGreeting } from './api.js'

export const STYLES = [
  { id: 'brainrot', label: 'Брейнрот', emoji: '🧠' },
  { id: 'warm', label: 'Душевно', emoji: '💛' },
  { id: 'official', label: 'Офіційно', emoji: '🎩' },
]

export default function App() {
  const [name, setName] = useState('')
  const [style, setStyle] = useState(null)
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [greeting, setGreeting] = useState('')
  const [error, setError] = useState('')

  const trimmedName = name.trim()
  const canGenerate = trimmedName.length > 0 && style !== null && status !== 'loading'

  async function handleGenerate(e) {
    e?.preventDefault()
    if (!canGenerate) return
    setStatus('loading')
    setError('')
    try {
      const data = await generateGreeting({ name: trimmedName, style })
      setGreeting(data.text)
      setStatus('done')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <main className="page">
      <header>
        <h1>🎂 ДРбот</h1>
        <p className="subtitle">Смішне привітання з днем народження за хвилину</p>
      </header>

      <form className="card" onSubmit={handleGenerate}>
        <label htmlFor="name">Імʼя іменинника</label>
        <input
          id="name"
          type="text"
          maxLength={50}
          autoComplete="off"
          placeholder="Наприклад, Саша"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {trimmedName && (
          <fieldset className="styles">
            <legend>Стиль гумору</legend>
            {STYLES.map((s) => (
              <button
                key={s.id}
                type="button"
                className={style === s.id ? 'style selected' : 'style'}
                aria-pressed={style === s.id}
                onClick={() => setStyle(s.id)}
              >
                <span aria-hidden="true">{s.emoji}</span> {s.label}
              </button>
            ))}
          </fieldset>
        )}

        {trimmedName && (
          <button type="submit" className="primary" disabled={!canGenerate}>
            {status === 'loading' ? 'Генеруємо…' : 'Згенерувати'}
          </button>
        )}
      </form>

      {status === 'done' && (
        <section className="card result" aria-live="polite">
          <p>{greeting}</p>
        </section>
      )}

      {status === 'error' && (
        <section className="card error" role="alert">
          <p>{error}</p>
          <button type="button" onClick={handleGenerate}>
            Повторити
          </button>
        </section>
      )}
    </main>
  )
}
