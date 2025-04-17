import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = 'http://localhost:5000'

export async function POST(request: NextRequest) {
  try {
    const token = request.headers.get('Authorization')
    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized - No token provided' },
        { status: 401 }
      )
    }

    const data = await request.json()
    
    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/learning/community`, {
      method: 'POST',
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })

    const responseData = await response.json()
    
    return NextResponse.json(responseData, { 
      status: response.ok ? 201 : response.status 
    })
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to create community content' },
      { status: 500 }
    )
  }
} 
