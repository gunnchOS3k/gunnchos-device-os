import { describe, it, expect, beforeEach } from 'vitest'
import {
  ENCRYPTED_WORKSPACE_KEY,
  ENCRYPTION_ENABLED_KEY,
  enableEncryption,
  exportEncryptedBackup,
  importEncryptedBackup,
  isEncryptionEnabled,
  isWorkspaceLocked,
  loadPlaintextPayload,
  lockWorkspace,
  resetEncryptedWorkspace,
  unlockWorkspace,
} from './encryptedWorkspaceStore'
import {
  WORKSPACE_STORAGE_KEY,
  createFile,
  getChildren,
  loadFileContent,
  resetDemoWorkspace,
} from './localWorkspaceStore'
import {
  NOTES_STORAGE_KEY,
  createNote,
  listNotes,
  resetStarterNotes,
} from './notesStore'
import {
  decryptPayload,
  encryptPayload,
  envelopeContainsPlaintext,
} from './workspaceCrypto'

const PASS = 'test-passphrase-123'
const WRONG = 'wrong-passphrase'

describe('workspaceCrypto', () => {
  it('encrypts and decrypts round trip', async () => {
    const payload = { secret: 'hello world', count: 42 }
    const envelope = await encryptPayload(payload, PASS)
    const restored = await decryptPayload<typeof payload>(envelope, PASS)
    expect(restored).toEqual(payload)
  })

  it('wrong passphrase fails decryption', async () => {
    const envelope = await encryptPayload({ x: 1 }, PASS)
    await expect(decryptPayload(envelope, WRONG)).rejects.toThrow(/Decryption failed/)
  })

  it('encrypted payload does not contain plaintext', async () => {
    const secret = 'super-secret-note-body'
    const envelope = await encryptPayload({ body: secret }, PASS)
    expect(envelopeContainsPlaintext(envelope, secret)).toBe(false)
    expect(envelope.ciphertext).toBeTruthy()
    expect(envelope.salt).toBeTruthy()
    expect(envelope.iv).toBeTruthy()
  })
})

describe('encryptedWorkspaceStore integration', () => {
  beforeEach(async () => {
    localStorage.clear()
    await resetEncryptedWorkspace()
    resetDemoWorkspace()
    resetStarterNotes()
  })

  it('unencrypted storage still works when encryption disabled', () => {
    expect(isEncryptionEnabled()).toBe(false)
    const file = createFile(null, 'plain.txt', 'visible')
    expect(loadFileContent(file.id)).toBe('visible')
    const raw = localStorage.getItem(WORKSPACE_STORAGE_KEY)
    expect(raw).toContain('visible')
  })

  it('notes save/load through encrypted store', async () => {
    const payload = loadPlaintextPayload()
    payload.notes = resetStarterNotes()
    await enableEncryption(PASS, payload)
    const note = createNote('Encrypted Note', 'secret body')
    expect(listNotes().some(n => n.id === note.id)).toBe(true)
    const stored = localStorage.getItem(ENCRYPTED_WORKSPACE_KEY)
    expect(stored).toBeTruthy()
    expect(stored).not.toContain('secret body')
  })

  it('files save/load through encrypted store', async () => {
    const payload = loadPlaintextPayload()
    payload.workspace = resetDemoWorkspace()
    await enableEncryption(PASS, payload)
    const folder = getChildren(null)[0]
    const file = createFile(folder.id, 'enc.txt', 'classified')
    expect(loadFileContent(file.id)).toBe('classified')
    const stored = localStorage.getItem(ENCRYPTED_WORKSPACE_KEY)
    expect(stored).not.toContain('classified')
  })

  it('lock hides content', async () => {
    const payload = loadPlaintextPayload()
    payload.workspace = resetDemoWorkspace()
    payload.notes = resetStarterNotes()
    await enableEncryption(PASS, payload)
    createFile(null, 'hidden.txt', 'gone while locked')
    await lockWorkspace()
    expect(isWorkspaceLocked()).toBe(true)
    expect(getChildren(null).length).toBe(0)
    expect(listNotes().length).toBe(0)
  })

  it('unlock restores content', async () => {
    const payload = loadPlaintextPayload()
    payload.workspace = resetDemoWorkspace()
    await enableEncryption(PASS, payload)
    const file = createFile(null, 'restore.txt', 'back again')
    await lockWorkspace()
    await unlockWorkspace(PASS)
    expect(loadFileContent(file.id)).toBe('back again')
  })

  it('export/import encrypted backup works', async () => {
    const payload = loadPlaintextPayload()
    payload.workspace = resetDemoWorkspace()
    payload.notes = resetStarterNotes()
    await enableEncryption(PASS, payload)
    createNote('Backup Note', 'persist me')
    const backup = await exportEncryptedBackup()
    await resetEncryptedWorkspace()
    localStorage.removeItem(WORKSPACE_STORAGE_KEY)
    localStorage.removeItem(NOTES_STORAGE_KEY)
    await importEncryptedBackup(backup, PASS)
    expect(listNotes().some(n => n.title === 'Backup Note')).toBe(true)
  })

  it('does not store passphrase in localStorage', async () => {
    const payload = loadPlaintextPayload()
    await enableEncryption(PASS, payload)
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i)
      if (key) expect(localStorage.getItem(key)).not.toContain(PASS)
    }
    expect(localStorage.getItem(ENCRYPTION_ENABLED_KEY)).toBe('true')
  })
})
