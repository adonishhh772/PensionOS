import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Proxy to backend running on localhost:8000
  const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
  const resp = await fetch(`${backend}/sources`)
  const json = await resp.json()
  res.status(200).json(json)
}
