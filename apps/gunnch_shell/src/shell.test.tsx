import { fireEvent, render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import CompleteExperienceShell from './CompleteExperienceShell'

describe('gunnch_shell production authority', () => {
  it('renders Home with brand and accessible name', () => {
    render(<CompleteExperienceShell profile="student_14_5" />)
    expect(screen.getByRole('application', { name: /gunnchOS Complete Experience/i })).toBeTruthy()
    expect(screen.getByLabelText(/gunnchOS brand/i)).toBeTruthy()
    expect(screen.getByRole('heading', { name: /gunnch Home/i })).toBeTruthy()
  })

  it('navigates primary surfaces via nav', () => {
    render(<CompleteExperienceShell />)
    fireEvent.click(screen.getByRole('navigation', { name: /Primary/i }).querySelector('button')!)
    // first nav is Home — click Vault (2nd)
    const nav = screen.getByRole('navigation', { name: /Primary/i })
    const buttons = Array.from(nav.querySelectorAll('button'))
    fireEvent.click(buttons[1])
    expect(screen.getByRole('heading', { name: /^Vault$/i })).toBeTruthy()
    fireEvent.click(buttons[2])
    expect(screen.getByRole('heading', { name: /App Center/i })).toBeTruthy()
    fireEvent.click(buttons[3])
    expect(screen.getByRole('heading', { name: /^Connect$/i })).toBeTruthy()
    fireEvent.click(buttons[4])
    expect(screen.getByRole('heading', { name: /^Assist$/i })).toBeTruthy()
    fireEvent.click(buttons[5])
    expect(screen.getByRole('heading', { name: /^Care$/i })).toBeTruthy()
  })

  it('shows offline banner', () => {
    render(<CompleteExperienceShell offline />)
    expect(screen.getByRole('status')).toBeTruthy()
  })
})
