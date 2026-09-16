import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import CompleteExperienceShell from './CompleteExperienceShell'

describe('CX2 CompleteExperienceShell', () => {
  it('renders brand Home and navigates all surfaces with accessible names', () => {
    render(<CompleteExperienceShell profile="student_14_5" />)
    expect(screen.getByLabelText('gunnchOS brand')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'gunnch Home' })).toBeInTheDocument()

    for (const name of ['Vault', 'App Center', 'Connect', 'Assist', 'Care'] as const) {
      fireEvent.click(screen.getByRole('button', { name }))
      expect(screen.getByRole('heading', { name })).toBeInTheDocument()
    }

    fireEvent.click(screen.getByLabelText('Home'))
    expect(screen.getByRole('heading', { name: 'gunnch Home' })).toBeInTheDocument()
  })

  it('supports keyboard focus targets and offline banner', () => {
    render(<CompleteExperienceShell offline />)
    expect(screen.getByRole('status')).toHaveTextContent(/Offline/)
    const vault = screen.getByRole('button', { name: 'Vault' })
    vault.focus()
    expect(vault).toHaveFocus()
  })
})
