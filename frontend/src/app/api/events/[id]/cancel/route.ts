import { NextRequest, NextResponse } from "next/server"

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const eventId = parseInt(params.id)
    if (isNaN(eventId)) {
      return NextResponse.json(
        { message: 'Invalid event ID' },
        { status: 400 }
      )
    }

    if (!process.env.NEXT_PUBLIC_BACKEND_URL) {
      throw new Error('Backend URL is not configured')
    }

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/events/${eventId}/cancel`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': request.headers.get('Authorization') || ''
        }
      }
    )

    const contentType = response.headers.get('content-type')
    if (!contentType?.includes('application/json')) {
      console.error('Received non-JSON response:', await response.text())
      return NextResponse.json(
        { 
          message: 'Unexpected response from server',
          success: false 
        },
        { status: 500 }
      )
    }

    const result = await response.json()

    if (!response.ok) {
      console.error('Event registration cancellation failed:', result)
      return NextResponse.json(
        { 
          message: result.message || 'Failed to cancel event registration',
          success: false 
        },
        { status: response.status }
      )
    }

    return NextResponse.json({
      ...result,
      success: true
    })
  } catch (error) {
    console.error('Error canceling event registration:', error)
    return NextResponse.json(
      { 
        message: error instanceof Error ? error.message : 'Internal server error',
        success: false 
      },
      { status: 500 }
    )
  }
} 