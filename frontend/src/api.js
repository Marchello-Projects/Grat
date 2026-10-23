const API_URL = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

export async function generateGreeting({ name, style }) {
  let response
  try {
    response = await fetch(`${API_URL}/api/greetings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, style }),
    })
  } catch {
    throw new ApiError('Немає звʼязку з сервером. Перевірте інтернет.', 0)
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : null
    if (response.status === 429) {
      throw new ApiError(detail ?? 'Забагато запитів, зачекайте кілька секунд', 429)
    }
    throw new ApiError(detail ?? 'Не вдалося згенерувати привітання', response.status)
  }
  return data
}
