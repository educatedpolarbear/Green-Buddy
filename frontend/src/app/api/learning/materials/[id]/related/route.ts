import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string} }
) {
  try {
    const id = params.id
    const sameTypeRaw = request.nextUrl.searchParams.get('sameType') || 'false';
    const limit = request.nextUrl.searchParams.get('limit') || '3';
    
    const sameType = sameTypeRaw.toLowerCase() === 'true' ? 'true' : 'false';
    
        
    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/learning/${id}/related?sameType=${sameType}&limit=${limit}`, {
      cache: 'no-store'
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Backend error response:', errorText)
      throw new Error(`Backend responded with status ${response.status}: ${errorText}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch related articles' },
      { status: 500 }
    )
  }
} 

