import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, it, expect, vi } from 'vitest'
import CompleteExperienceShell from './CompleteExperienceShell'
import { clearContinuity, recordContinuity } from './platform/continuityStore'
beforeEach(() => {
  clearContinuity()
  try {
    localStorage.clear()
  } catch {
    // ignore
  }
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
    expect(labels.join(' ')).toMatch(/Apps/)
    expect(labels.join(' ')).toMatch(/Connect/)
    expect(labels.join(' ')).toMatch(/More/)
    expect(screen.getByLabelText(/Session controls/i)).toBeTruthy()
  })

  it('navigates Vault and App Library via dock', async () => {
    render(<CompleteExperienceShell />)
    const dock = screen.getByRole('navigation', { name: /Primary/i })
    const buttons = Array.from(dock.querySelectorAll('button'))
    fireEvent.click(buttons[1])
    expect(screen.getByRole('heading', { name: /^Vault$/i })).toBeTruthy()
    await waitFor(() => expect(screen.getByText(/notes\.txt/i)).toBeTruthy())
    fireEvent.click(buttons[2])
    expect(screen.getByRole('heading', { name: /App Library/i })).toBeTruthy()
    await waitFor(() => expect(screen.getByTestId('provider-label')).toBeTruthy())
    expect(screen.getByTestId('app-library-categories')).toBeTruthy()
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

describe('VXP-2 universal parity surfaces', () => {
  it('opens searchable Settings with AI runtime honesty and diagnostics', async () => {
    render(<CompleteExperienceShell hostKind="ANDROID_CAPSULE" />)
    fireEvent.click(screen.getByTestId('open-settings'))
    expect(screen.getByRole('heading', { name: /^Settings$/i })).toBeTruthy()
    expect(screen.getByTestId('settings-search')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /^AI \/ Assist$/i }))
    expect(screen.getByTestId('settings-ai-runtime').textContent).toMatch(/Local deterministic|Remote|Unavailable|Nearby Mac/)
    expect(screen.getByTestId('settings-ai-runtime').textContent).not.toMatch(/On-device AI/)
    fireEvent.click(screen.getByRole('button', { name: /Developer \/ Diagnostics/i }))
    expect(screen.getByTestId('settings-diagnostics').textContent).toMatch(/Engineering metadata/)
  })

  it('indexes Search / Command to real destinations only', async () => {
    render(<CompleteExperienceShell />)
    fireEvent.click(screen.getByTestId('open-search'))
    expect(screen.getByRole('heading', { name: /Search \/ Command/i })).toBeTruthy()
    fireEvent.change(screen.getByTestId('system-search'), { target: { value: 'WAIKE' } })
    const hits = screen.getByLabelText(/Search results/i)
    expect(within(hits).getAllByText(/WAIKE/i).length).toBeGreaterThan(0)
    fireEvent.click(within(hits).getAllByRole('button')[0])
    await waitFor(() => expect(screen.getByTestId('waike-surface')).toBeTruthy())
  })

  it('wires Continuity continue cards from real activity only', async () => {
    recordContinuity({
      id: 'creation-demo',
      domain: 'creation',
      title: 'Lab note',
      surface: 'creation',
    })
    render(<CompleteExperienceShell />)
    expect(screen.getByTestId('continue-list')).toBeTruthy()
    expect(screen.getByText(/Lab note/i)).toBeTruthy()
    expect(screen.queryByTestId('continue-empty')).toBeNull()
  })

  it('provides WAIKE, gunnchAI, Games, Creation, Leisure routes', async () => {
    render(<CompleteExperienceShell />)
    const dock = screen.getByRole('navigation', { name: /Primary/i })
    fireEvent.click(within(dock).getByRole('button', { name: /More/i }))
    const more = await screen.findByRole('dialog', { name: /More surfaces/i })

    fireEvent.click(within(more).getByRole('button', { name: /^WAIKE$/i }))
    expect(screen.getByTestId('waike-surface')).toBeTruthy()
    expect(screen.getByTestId('waike-mode').textContent).toMatch(/FULL_VIA_ADAPTER|ADAPTER|WEB_PWA/i)

    fireEvent.click(within(dock).getByRole('button', { name: /More/i }))
    const more2 = await screen.findByRole('dialog', { name: /More surfaces/i })
    fireEvent.click(within(more2).getByRole('button', { name: /gunnchAI/i }))
    expect(screen.getByTestId('gunnchai-surface')).toBeTruthy()
    expect(screen.getByTestId('gunnchai-runtime').textContent).not.toMatch(/On-device/)

    fireEvent.click(within(dock).getByRole('button', { name: /More/i }))
    const more3 = await screen.findByRole('dialog', { name: /More surfaces/i })
    fireEvent.click(within(more3).getByRole('button', { name: /^Games$/i }))
    expect(screen.getByTestId('games-surface')).toBeTruthy()
    expect(screen.getByText(/Anime Aggressors/i)).toBeTruthy()
    expect(screen.queryByText(/sha256|git@|refs\/heads/i)).toBeNull()

    fireEvent.click(within(dock).getByRole('button', { name: /More/i }))
    const more4 = await screen.findByRole('dialog', { name: /More surfaces/i })
    fireEvent.click(within(more4).getByRole('button', { name: /^Creation$/i }))
    expect(screen.getByTestId('creation-surface')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /New note/i }))
    fireEvent.change(screen.getByTestId('creation-title'), { target: { value: 'Pixel draft' } })
    fireEvent.change(screen.getByTestId('creation-body'), { target: { value: 'save me' } })
    fireEvent.click(screen.getByTestId('creation-save'))
    expect(screen.getByText(/Pixel draft/i)).toBeTruthy()

    fireEvent.click(within(dock).getByRole('button', { name: /More/i }))
    const more5 = await screen.findByRole('dialog', { name: /More surfaces/i })
    fireEvent.click(within(more5).getByRole('button', { name: /^Leisure$/i }))
    expect(screen.getByTestId('leisure-surface')).toBeTruthy()
    expect(screen.getByText(/No unlicensed streaming/i)).toBeTruthy()
  })

  it('states Connect telephony honesty', () => {
    render(<CompleteExperienceShell initialSurface="connect" />)
    expect(screen.getByTestId('telephony-status').textContent).toMatch(/not available/i)
  })
})
