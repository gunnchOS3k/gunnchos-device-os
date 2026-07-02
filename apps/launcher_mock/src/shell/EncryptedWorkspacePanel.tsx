import { useEffect, useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import {
  changePassphrase,
  enableEncryption,
  exportEncryptedBackup,
  getEncryptionClaim,
  importEncryptedBackup,
  isEncryptionEnabled,
  isWorkspaceLocked,
  isWorkspaceUnlocked,
  loadPlaintextPayload,
  lockWorkspace,
  resetEncryptedWorkspace,
  subscribeEncryptedWorkspace,
  unlockWorkspace,
} from '../services/encryptedWorkspaceStore'
import { createDemoWorkspace, resetDemoWorkspace } from '../services/localWorkspaceStore'
import { createStarterNotes, resetStarterNotes } from '../services/notesStore'

export default function EncryptedWorkspacePanel() {
  const [, tick] = useState(0)
  const [passphrase, setPassphrase] = useState('')
  const [newPassphrase, setNewPassphrase] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => subscribeEncryptedWorkspace(() => tick(n => n + 1)), [])

  const enabled = isEncryptionEnabled()
  const locked = isWorkspaceLocked()
  const unlocked = isWorkspaceUnlocked()

  const run = async (fn: () => Promise<void>) => {
    setError('')
    setMessage('')
    try {
      await fn()
      setPassphrase('')
      setNewPassphrase('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Operation failed')
    }
  }

  return (
    <section style={{ marginBottom: 28 }}>
      <h2 style={{ fontSize: 14, color: theme.textMuted, textTransform: 'uppercase', margin: '0 0 12px' }}>
        Encrypted workspace prototype
      </h2>
      <div style={{ background: theme.surfaceRaised, borderRadius: theme.radius, border: `1px solid ${theme.border}`, padding: 16 }}>
        <p style={{ fontSize: 13, color: theme.warning ?? theme.textMuted, margin: '0 0 12px' }}>
          {getEncryptionClaim()}
        </p>
        {!enabled && (
          <p style={{ fontSize: 13, color: theme.textMuted, margin: '0 0 12px' }}>
            Unencrypted prototype mode: workspace and notes persist in plain browser localStorage until you enable encryption.
          </p>
        )}
        {enabled && locked && (
          <p style={{ fontSize: 13, color: theme.textMuted, margin: '0 0 12px' }}>
            Workspace locked — File Manager and Notes content is hidden until unlock.
          </p>
        )}
        {enabled && unlocked && (
          <p style={{ fontSize: 13, color: theme.accent, margin: '0 0 12px' }}>
            Unlocked — changes re-encrypt on save (passphrase kept in session memory only).
          </p>
        )}

        <label style={labelStyle}>
          Passphrase
          <input
            type="password"
            value={passphrase}
            onChange={e => setPassphrase(e.target.value)}
            style={inputStyle}
            autoComplete="new-password"
          />
        </label>

        {!enabled && (
          <button
            type="button"
            style={primaryBtn}
            onClick={() =>
              run(async () => {
                const payload = loadPlaintextPayload()
                if (payload.workspace.length === 0) payload.workspace = createDemoWorkspace()
                if (payload.notes.length === 0) payload.notes = createStarterNotes()
                await enableEncryption(passphrase, payload)
                setMessage('Encrypted workspace enabled and migrated.')
              })
            }
          >
            Enable encrypted workspace prototype
          </button>
        )}

        {enabled && locked && (
          <button
            type="button"
            style={primaryBtn}
            onClick={() =>
              run(async () => {
                await unlockWorkspace(passphrase)
                setMessage('Workspace unlocked.')
              })
            }
          >
            Unlock workspace
          </button>
        )}

        {enabled && unlocked && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
            <button type="button" style={secondaryBtn} onClick={() => { void lockWorkspace().then(() => setMessage('Workspace locked.')) }}>
              Lock workspace
            </button>
            <label style={labelStyle}>
              New passphrase
              <input
                type="password"
                value={newPassphrase}
                onChange={e => setNewPassphrase(e.target.value)}
                style={inputStyle}
              />
            </label>
            <button
              type="button"
              style={secondaryBtn}
              onClick={() =>
                run(async () => {
                  await changePassphrase(passphrase, newPassphrase)
                  setMessage('Passphrase changed.')
                })
              }
            >
              Change passphrase
            </button>
            <button
              type="button"
              style={secondaryBtn}
              onClick={() =>
                run(async () => {
                  const backup = await exportEncryptedBackup()
                  const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = 'gunnchos-encrypted-workspace-backup.json'
                  a.click()
                  URL.revokeObjectURL(url)
                  setMessage('Encrypted backup exported.')
                })
              }
            >
              Export encrypted backup
            </button>
            <label style={secondaryBtn}>
              Import backup
              <input
                type="file"
                accept="application/json"
                style={{ display: 'block', marginTop: 4 }}
                onChange={e => {
                  const file = e.target.files?.[0]
                  if (!file) return
                  void run(async () => {
                    const text = await file.text()
                    const data = JSON.parse(text)
                    await importEncryptedBackup(data, passphrase)
                    setMessage('Encrypted backup imported.')
                  })
                }}
              />
            </label>
            <button
              type="button"
              style={dangerBtn}
              onClick={() =>
                run(async () => {
                  await resetEncryptedWorkspace()
                  resetDemoWorkspace()
                  resetStarterNotes()
                  setMessage('Encrypted workspace reset. Plain prototype folders restored.')
                })
              }
            >
              Reset encrypted workspace
            </button>
          </div>
        )}

        {message && <p style={{ color: theme.accent, fontSize: 13, marginTop: 12 }}>{message}</p>}
        {error && <p style={{ color: theme.danger, fontSize: 13, marginTop: 12 }}>{error}</p>}
      </div>
    </section>
  )
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 13,
  marginBottom: 8,
  width: '100%',
}

const inputStyle: React.CSSProperties = {
  display: 'block',
  width: '100%',
  maxWidth: 320,
  marginTop: 4,
  padding: '8px 10px',
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.surface,
  color: theme.text,
}

const primaryBtn: React.CSSProperties = {
  padding: '10px 16px',
  borderRadius: 8,
  border: 'none',
  background: theme.accent,
  color: '#000',
  fontWeight: 600,
  cursor: 'pointer',
  marginTop: 8,
}

const secondaryBtn: React.CSSProperties = {
  padding: '8px 12px',
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.surface,
  color: theme.text,
  cursor: 'pointer',
  fontSize: 13,
}

const dangerBtn: React.CSSProperties = {
  padding: '8px 12px',
  borderRadius: 8,
  border: `1px solid ${theme.danger}`,
  background: 'transparent',
  color: theme.danger,
  cursor: 'pointer',
  fontSize: 13,
}
