import { NextRequest, NextResponse } from 'next/server';
import { writeFile } from 'fs/promises';
import { join } from 'path';
import { v4 as uuidv4 } from 'uuid';

export async function POST(request: NextRequest) {
  try {
    const data = await request.formData();
    const file: File | null = data.get('file') as unknown as File;

    if (!file) {
      return NextResponse.json({ success: false, error: 'No file uploaded' });
    }

    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    // Generate unique filename
    const filename = `${uuidv4()}-${file.name}`;
    const filepath = join(process.cwd(), 'uploads', filename);

    // Ensure uploads directory exists
    const uploadsDir = join(process.cwd(), 'uploads');
    try {
      const fs = await import('fs');
      await fs.promises.mkdir(uploadsDir, { recursive: true });
    } catch (error) {
      // Directory might already exist
    }

    await writeFile(filepath, buffer);

    return NextResponse.json({
      success: true,
      filename,
      originalName: file.name,
      size: file.size
    });
  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to upload file' },
      { status: 500 }
    );
  }
}
