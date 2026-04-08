import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { username, password } = await request.json();

    if (username === 'admin' && password === 'admin2026*') {
      return NextResponse.json({ success: true, message: 'Autenticación exitosa' });
    } else {
      return NextResponse.json(
        { success: false, message: 'Credenciales inválidas' },
        { status: 401 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      { success: false, message: 'Error procesando solicitud' },
      { status: 400 }
    );
  }
}
