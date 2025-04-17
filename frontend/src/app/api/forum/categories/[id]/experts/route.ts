import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  
  request: NextRequest,
  { params }: { params: { id: string } }
) {

  try {
    const categoryId = params.id;
    
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    const response = await fetch(`${backendUrl}/forum/categories/${categoryId}/experts`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('Authorization') || ''
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { message: errorData.message || 'Failed to fetch experts' },
        { status: response.status }
      );
    }

    const data = await response.json();
        return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching category experts:', error);
    return NextResponse.json(
      { message: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    );
  }
} 
