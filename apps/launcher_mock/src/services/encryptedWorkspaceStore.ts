/**
 * Encrypted workspace session — browser-backed prototype, not OS full-disk encryption.
 * Stores salt, IV, ciphertext, and metadata only. Passphrase never persisted.
 */

import type { WorkspaceNode } from './localWorkspaceStore'
import { WORKSPACE_STORAGE_KEY } from './localWorkspaceStore'
import type { Note } from './notesStore'
import { NOTES_STORAGE_KEY } from './notesStore'
import {
  ENCRYPTION_CLAIM,
  EncryptedEnvelope,
  decryptPayload,
  encryptPayload,
} from './workspaceCrypto'

export const ENCRYPTED_WORKSPACE_KEY = 'gunnchos-encrypted-workspace-v1'
export const ENCRYPTION_ENABLED_KEY = 'gunnchos-encrypted-workspace-enabled'

export interface WorkspacePayload {
  workspace: WorkspaceNode[]
  notes: Note[]
}

export interface EncryptedBackupExport extends EncryptedEnvelope {
  backupType: 'encrypted_workspace_backup'
}

interface SessionState {
  unlocked: boolean
  payload: WorkspacePayload | null
}

const session: SessionState = {
  unlocked: false,
  payload: null,
}

const listeners = new Set<() => void>()

export function subscribeEncryptedWorkspace(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function notify(): void {
  listeners.forEach(l => l())
}

export function isEncryptionEnabled(): boolean {
  return localStorage.getItem(ENCRYPTION_ENABLED_KEY) === 'true'
}

export function setEncryptionEnabled(enabled: boolean): void {
  localStorage.setItem(ENCRYPTION_ENABLED_KEY, enabled ? 'true' : 'false')
  notify()
}

export function isWorkspaceUnlocked(): boolean {
  return !isEncryptionEnabled() || session.unlocked
}

export function isWorkspaceLocked(): boolean {
  return isEncryptionEnabled() && !session.unlocked
}

export function getEncryptionClaim(): string {
  return ENCRYPTION_CLAIM
}

function loadEnvelope(): EncryptedEnvelope | null {
  try {
    const raw = localStorage.getItem(ENCRYPTED_WORKSPACE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as EncryptedEnvelope
  } catch {
    return null
  }
}

function saveEnvelope(envelope: EncryptedEnvelope): void {
  localStorage.setItem(ENCRYPTED_WORKSPACE_KEY, JSON.stringify(envelope))
}

function clearPlaintextKeys(): void {
  localStorage.removeItem(WORKSPACE_STORAGE_KEY)
  localStorage.removeItem(NOTES_STORAGE_KEY)
}

export function readWorkspaceFromSession(): WorkspacePayload {
  if (!session.payload) {
    return { workspace: [], notes: [] }
  }
  return session.payload
}

export async function persistSession(passphrase: string): Promise<void> {
  if (!session.payload) throw new Error('No workspace data in session')
  const envelope = await encryptPayload(session.payload, passphrase)
  saveEnvelope(envelope)
  clearPlaintextKeys()
}

async function unlockWithPassphrase(passphrase: string): Promise<void> {
  const envelope = loadEnvelope()
  if (!envelope) throw new Error('No encrypted workspace found')
  session.payload = await decryptPayload<WorkspacePayload>(envelope, passphrase)
  session.unlocked = true
  rememberSessionPassphrase(passphrase)
  notify()
}

export async function enableEncryption(
  passphrase: string,
  initial: WorkspacePayload,
): Promise<void> {
  if (!passphrase.trim()) throw new Error('Passphrase required')
  session.payload = initial
  rememberSessionPassphrase(passphrase)
  await persistSession(passphrase)
  setEncryptionEnabled(true)
  session.unlocked = true
  notify()
}

export async function unlockWorkspace(passphrase: string): Promise<void> {
  if (!isEncryptionEnabled()) throw new Error('Encryption not enabled')
  await unlockWithPassphrase(passphrase)
}

export async function lockWorkspace(): Promise<void> {
  await persistSessionIfPossible()
  session.unlocked = false
  session.payload = null
  clearSessionPassphrase()
  notify()
}

export async function changePassphrase(
  oldPassphrase: string,
  newPassphrase: string,
): Promise<void> {
  if (!newPassphrase.trim()) throw new Error('New passphrase required')
  await unlockWithPassphrase(oldPassphrase)
  rememberSessionPassphrase(newPassphrase)
  await persistSession(newPassphrase)
}

export function writeWorkspaceToSession(
  patch: Partial<WorkspacePayload>,
): void {
  if (!session.unlocked && isEncryptionEnabled()) {
    throw new Error('Workspace is locked')
  }
  const current = session.payload ?? { workspace: [], notes: [] }
  session.payload = {
    workspace: patch.workspace ?? current.workspace,
    notes: patch.notes ?? current.notes,
  }
}

export async function flushEncryptedSession(passphrase: string): Promise<void> {
  if (!isEncryptionEnabled() || !session.unlocked) return
  await persistSession(passphrase)
}

let cachedPassphrase: string | null = null

export function rememberSessionPassphrase(passphrase: string): void {
  cachedPassphrase = passphrase
}

export function clearSessionPassphrase(): void {
  cachedPassphrase = null
}

export async function persistSessionIfPossible(): Promise<void> {
  if (cachedPassphrase && session.unlocked && session.payload) {
    await persistSession(cachedPassphrase)
  }
}

export async function exportEncryptedBackup(): Promise<EncryptedBackupExport> {
  if (session.unlocked && session.payload && cachedPassphrase) {
    const envelope = await encryptPayload(session.payload, cachedPassphrase)
    saveEnvelope(envelope)
    return { ...envelope, backupType: 'encrypted_workspace_backup' }
  }
  const envelope = loadEnvelope()
  if (!envelope) throw new Error('No encrypted workspace to export')
  return { ...envelope, backupType: 'encrypted_workspace_backup' }
}

export async function importEncryptedBackup(
  data: EncryptedBackupExport,
  passphrase: string,
): Promise<void> {
  if (data.backupType !== 'encrypted_workspace_backup') {
    throw new Error('Invalid encrypted backup')
  }
  session.payload = await decryptPayload<WorkspacePayload>(data, passphrase)
  saveEnvelope(data)
  setEncryptionEnabled(true)
  session.unlocked = true
  rememberSessionPassphrase(passphrase)
  clearPlaintextKeys()
  notify()
}

export async function resetEncryptedWorkspace(): Promise<void> {
  localStorage.removeItem(ENCRYPTED_WORKSPACE_KEY)
  localStorage.removeItem(ENCRYPTION_ENABLED_KEY)
  session.unlocked = false
  session.payload = null
  cachedPassphrase = null
  notify()
}

export function loadPlaintextPayload(): WorkspacePayload {
  let workspace: WorkspaceNode[] = []
  let notes: Note[] = []
  try {
    const wsRaw = localStorage.getItem(WORKSPACE_STORAGE_KEY)
    if (wsRaw) workspace = JSON.parse(wsRaw) as WorkspaceNode[]
  } catch {
    workspace = []
  }
  try {
    const notesRaw = localStorage.getItem(NOTES_STORAGE_KEY)
    if (notesRaw) notes = JSON.parse(notesRaw) as Note[]
  } catch {
    notes = []
  }
  return { workspace, notes }
}
