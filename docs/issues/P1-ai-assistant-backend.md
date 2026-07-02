# OS-010: AI assistant backend

**Priority:** P1 · **Release target:** Beta (basic) / RC (full)

## Problem

GunnchAI panel is UI-only with suggestion chips. No backend.

## Why it matters

AI study companion is core product vision for stuck learners.

## Definition of done

- API endpoint or local model wrapper
- Privacy mode respected (no training on student data)
- Explain/quiz/flashcard flows for one path

## Tests

- API smoke; privacy flag pytest

## Evidence required

- Demo script output

## Non-goals

- Full NotebookLM parity
- Voice/camera v1

## Claim boundary

Assistant prototype. Not FERPA-certified without review.
