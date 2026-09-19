import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
              files: [
                {
                  path: '/docs/notes.txt',
                  size: 128,
                  sha256: 'abc123def4567890abc123def4567890abc123def4567890abc123def4567890',
                  modified_at: 1700000000,
                  mime: 'text/plain',
                },
              ],
            }),
          json: async () => ({
            ok: true,
            provider: 'cx2h2-vault',
            files: [
              {
                path: '/docs/notes.txt',
                size: 128,
                sha256: 'abc123def4567890abc123def4567890abc123def4567890abc123def4567890',
                modified_at: 1700000000,
                mime: 'text/plain',
              },
            ],
          }),
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
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
})

describe('gunnch_shell production authority', () => {
  it('renders Home Living Workspace with brand and accessible name', () => {
    render(<CompleteExperienceShell profile="student_14_5" />)
    expect(screen.getByRole('application', { name: /gunnchOS Complete Experience/i })).toBeTruthy()
    expect(screen.getByLabelText(/gunnchOS brand/i)).toBeTruthy()
    expect(screen.getByRole('heading', { name: /^gunnchOS$/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /Continue/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /Spaces/i })).toBeTruthy()
    expect(screen.getByText(/Nothing to resume yet/i)).toBeTruthy()
  })

  it('exposes dock primary nav without second equal Back/Home row weight', () => {
    render(<CompleteExperienceShell />)
    const dock = screen.getByRole('navigation', { name: /Primary/i })
    const labels = Array.from(dock.querySelectorAll('button')).map((b) => b.textContent)
    expect(labels.join(' ')).toMatch(/Home/)
    expect(labels.join(' ')).toMatch(/Vault/)
    expect(labels.join(' ')).toMatch(/App Center/)
    expect(labels.join(' ')).toMatch(/Connect/)
    expect(labels.join(' ')).toMatch(/More/)
    expect(screen.getByLabelText(/Session controls/i)).toBeTruthy()
  })

  it('navigates Vault and App Center via dock', async () => {
    render(<CompleteExperienceShell />)
    const dock = screen.getByRole('navigation', { name: /Primary/i })
    const buttons = Array.from(dock.querySelectorAll('button'))
    fireEvent.click(buttons[1])
    expect(screen.getByRole('heading', { name: /^Vault$/i })).toBeTruthy()
    await waitFor(() => expect(screen.getByText(/notes\.txt/i)).toBeTruthy())
    fireEvent.click(buttons[2])
    expect(screen.getByRole('heading', { name: /App Center/i })).toBeTruthy()
    await waitFor(() => expect(screen.getByTestId('provider-label')).toBeTruthy())
  })

  it('opens More sheet for Assist and Care', async () => {
    render(<CompleteExperienceShell />)
    const dock = screen.getByRole('navigation', { name: /Primary/i })
    fireEvent.click(within(dock).getByRole('button', { name: /More/i }))
    const more = await screen.findByRole('dialog', { name: /More surfaces/i })
    fireEvent.click(within(more).getByRole('button', { name: /Assist/i }))
    expect(screen.getByRole('heading', { name: /^Assist$/i })).toBeTruthy()
    expect(screen.getByLabelText(/High contrast/i)).toBeTruthy()
    expect(screen.getByLabelText(/Reduce motion/i)).toBeTruthy()
    expect(screen.getByLabelText(/UI scale/i)).toBeTruthy()
  })

  it('shows offline banner honestly', () => {
    render(<CompleteExperienceShell offline />)
    expect(screen.getByText(/Offline — local work continues/i)).toBeTruthy()
    expect(document.querySelector('.cx2-banner.vxp-banner')).toBeTruthy()
  })

  it('supports keyboard Alt surface shortcuts', async () => {
    render(<CompleteExperienceShell />)
    await waitFor(() => {
      fireEvent.keyDown(window, { key: '2', altKey: true })
      expect(screen.getByRole('heading', { name: /^Vault$/i })).toBeTruthy()
    })
    fireEvent.keyDown(window, { key: 'h', altKey: true })
    expect(screen.getByRole('heading', { name: /^gunnchOS$/i })).toBeTruthy()
  })

  it('does not use ANDROID_CAPSULE as primary Home copy', () => {
    render(<CompleteExperienceShell hostKind="ANDROID_CAPSULE" />)
    expect(screen.getByTestId('home-identity-meta').textContent).toMatch(/Running on Capsule/i)
    expect(screen.queryByText(/^ANDROID_CAPSULE$/)).toBeNull()
  })
})
