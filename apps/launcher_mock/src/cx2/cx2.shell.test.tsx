import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import CompleteExperienceShell from './CompleteExperienceShell'

describe('CX2 CompleteExperienceShell (launcher_mock adapter)', () => {
  it('delegates to gunnch_shell production authority', () => {
    render(<CompleteExperienceShell profile="student_14_5" />)
    expect(screen.getByRole('application', { name: /gunnchOS Complete Experience/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /gunnch Home/i })).toBeTruthy()
  })

  it('offline banner via adapter', () => {
    render(<CompleteExperienceShell offline />)
    expect(screen.getByRole('status')).toBeTruthy()
  })
})
