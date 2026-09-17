import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, it, expect, vi } from 'vitest'
import CompleteExperienceShell from './CompleteExperienceShell'

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes(':8767')) {
        if (url.includes('/api/backups')) {
          return {
            ok: true,
            text: async () => JSON.stringify({ ok: true, backups: [] }),
            json: async () => ({ ok: true, backups: [] }),
          }
        }
        return {
          ok: true,
          text: async () =>
            JSON.stringify({
              ok: true,
              provider: 'cx2h2-vault',
              files: [],
            }),
          json: async () => ({ ok: true, provider: 'cx2h2-vault', files: [] }),
        }
      }
      return {
        ok: true,
        text: async () =>
          JSON.stringify({
            provider: 'flatpak',
            apps: [
              {
                id: 'org.gunnchos.CX2HTestApp',
                name: 'CX2H Test App',
                source: 'flatpak:cx2h-local',
                version: '1.0.0',
                permissions: ['wayland'],
                installed: false,
                provenance: 'local_flatpak_repo',
              },
            ],
          }),
        json: async () => ({
          provider: 'flatpak',
          apps: [
            {
              id: 'org.gunnchos.CX2HTestApp',
              name: 'CX2H Test App',
              source: 'flatpak:cx2h-local',
              version: '1.0.0',
              permissions: ['wayland'],
              installed: false,
              provenance: 'local_flatpak_repo',
            },
          ],
        }),
      }
    }),
  )
})

describe('gunnch_shell production authority', () => {
  it('renders Home with brand and accessible name', () => {
    render(<CompleteExperienceShell profile="student_14_5" />)
    expect(screen.getByRole('application', { name: /gunnchOS Complete Experience/i })).toBeTruthy()
    expect(screen.getByLabelText(/gunnchOS brand/i)).toBeTruthy()
    expect(screen.getByRole('heading', { name: /gunnch Home/i })).toBeTruthy()
  })

  it('navigates primary surfaces via nav', async () => {
    render(<CompleteExperienceShell />)
    fireEvent.click(screen.getByRole('navigation', { name: /Primary/i }).querySelector('button')!)
    // first nav is Home — click Vault (2nd)
    const nav = screen.getByRole('navigation', { name: /Primary/i })
    const buttons = Array.from(nav.querySelectorAll('button'))
    fireEvent.click(buttons[1])
    expect(screen.getByRole('heading', { name: /^Vault$/i })).toBeTruthy()
    fireEvent.click(buttons[2])
    expect(screen.getByRole('heading', { name: /App Center/i })).toBeTruthy()
    await waitFor(() => expect(screen.getByTestId('provider-label')).toBeTruthy())
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
