import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const token = request.headers.get('Authorization')
    
    const authHeader = token?.startsWith('Bearer ') ? token : token ? `Bearer ${token}` : ''
    
    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/learning/${params.id}/complete`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      }
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    )
  }
} 
