import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App.jsx'

function mockFetch(...responses) {
  const fn = vi.fn()
  for (const r of responses) {
    fn.mockResolvedValueOnce({
      ok: r.status < 400,
      status: r.status,
      json: async () => r.body,
    })
  }
  vi.stubGlobal('fetch', fn)
  return fn
}

afterEach(() => vi.unstubAllGlobals())

describe('App', () => {
  it('FR-01: показує поле імені', () => {
    render(<App />)
    expect(screen.getByLabelText('Імʼя іменинника')).toBeInTheDocument()
  })

  it('FR-02: кнопки стилю зʼявляються після введення імені', async () => {
    render(<App />)
    expect(screen.queryByRole('button', { name: /Брейнрот/ })).not.toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Імʼя іменинника'), 'Саша')
    expect(screen.getByRole('button', { name: /Брейнрот/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Згенерувати' })).toBeDisabled()
  })

  it('FR-03: генерує й показує привітання', async () => {
    const fetch = mockFetch({ status: 200, body: { text: 'З ДН, Саша!', style: 'warm' } })
    render(<App />)
    await userEvent.type(screen.getByLabelText('Імʼя іменинника'), 'Саша')
    await userEvent.click(screen.getByRole('button', { name: /Душевно/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Згенерувати' }))

    expect(await screen.findByText('З ДН, Саша!')).toBeInTheDocument()
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ name: 'Саша', style: 'warm' })
  })

  it('FR-06: показує помилку й кнопку «Повторити», яка повторює запит', async () => {
    mockFetch(
      { status: 503, body: { detail: 'Сервіс генерації тимчасово недоступний' } },
      { status: 200, body: { text: 'Вийшло!', style: 'brainrot' } },
    )
    render(<App />)
    await userEvent.type(screen.getByLabelText('Імʼя іменинника'), 'Саша')
    await userEvent.click(screen.getByRole('button', { name: /Брейнрот/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Згенерувати' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('тимчасово недоступний')
    await userEvent.click(screen.getByRole('button', { name: 'Повторити' }))
    expect(await screen.findByText('Вийшло!')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('показує «зачекайте» на 429', async () => {
    mockFetch({ status: 429, body: { detail: 'Забагато запитів, зачекайте кілька секунд' } })
    render(<App />)
    await userEvent.type(screen.getByLabelText('Імʼя іменинника'), 'Саша')
    await userEvent.click(screen.getByRole('button', { name: /Офіційно/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Згенерувати' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('зачекайте')
  })
})
