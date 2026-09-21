import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import CompleteExperienceShell from './CompleteExperienceShell'

describe('CX2 CompleteExperienceShell (launcher_mock adapter)', () => {
  it('test setup supplies window.matchMedia', () => {
    expect(typeof window.matchMedia).toBe('function')
    const mql = window.matchMedia('(min-width: 900px)')
    expect(mql.matches).toBe(false)
    expect(mql.media).toBe('(min-width: 900px)')
  })

  it('delegates to gunnch_shell production authority', () => {
    render(<CompleteExperienceShell profile="student_14_5" />)
    expect(screen.getByRole('application', { name: /gunnchOS Complete Experience/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /^gunnchOS$/i })).toBeTruthy()
  })

  it('offline banner via adapter', () => {
    render(<CompleteExperienceShell offline />)
    expect(screen.getByText(/Offline — local work continues/i)).toBeTruthy()
  })
})
