import React from 'react'
import { createRoot } from 'react-dom/client'
import CompleteExperienceShell from './CompleteExperienceShell'

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <CompleteExperienceShell profile="student_14_5" />
  </React.StrictMode>,
)
