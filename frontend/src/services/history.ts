import type { TripPlan } from '@/types'

export interface SavedTrip {
  id: string
  updatedAt: string
  plan: TripPlan
}

const HISTORY_KEY = 'tripPlanHistory'

export function readHistory(): SavedTrip[] {
  return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
}

export function saveTrip(plan: TripPlan, id: string = crypto.randomUUID()): void {
  const entry = { id, updatedAt: new Date().toISOString(), plan }
  const history = readHistory().filter(item => item.id !== id)
  localStorage.setItem(HISTORY_KEY, JSON.stringify([entry, ...history]))
  sessionStorage.setItem('tripPlan', JSON.stringify(plan))
  sessionStorage.setItem('tripPlanId', id)
}

